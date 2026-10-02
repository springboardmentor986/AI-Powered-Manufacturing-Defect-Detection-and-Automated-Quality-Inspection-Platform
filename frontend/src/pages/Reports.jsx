import { useEffect, useMemo, useState } from "react";
import api from "../services/api";
import Sidebar from "../components/Sidebar";

const REPORT_TYPES = [
  "Production Quality Report",
  "Defect Report",
  "Quality Risk Report",
  "Inspection Summary Report",
];
const CATEGORIES = ["all", "bottle", "cable", "capsule", "carpet", "grid", "hazelnut", "leather", "metal_nut", "pill", "screw", "tile", "toothbrush", "transistor", "wood", "zipper"];
const SEVERITIES = ["all", "Critical", "High", "Medium", "Low"];

const parseResult = (item) => {
  if (item?.result && typeof item.result === "object") return item.result;
  try { return item?.result ? JSON.parse(item.result) : null; } catch { return null; }
};
const statusOf = (item) => String(parseResult(item)?.status || "").toUpperCase();
const display = (value = "Unknown") => String(value).replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
const severityOf = (item) => parseResult(item)?.quality_assessment?.severity?.level || "";

function Reports() {
  const [inspections, setInspections] = useState([]);
  const [filters, setFilters] = useState({ type: REPORT_TYPES[0], from: "", to: "", category: "all", result: "all", severity: "all" });
  const [generated, setGenerated] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/inspections/")
      .then((response) => setInspections(Array.isArray(response.data) ? response.data : []))
      .catch((requestError) => setError(requestError.response?.data?.detail || "Unable to load inspection data."));
  }, []);

  const filteredRows = useMemo(() => inspections.filter((item) => {
    const result = parseResult(item);
    const date = item.created_at ? new Date(item.created_at).toISOString().slice(0, 10) : "";
    const category = item.category || result?.category || "";
    const status = statusOf(item);
    return (!filters.from || date >= filters.from)
      && (!filters.to || date <= filters.to)
      && (filters.category === "all" || category === filters.category)
      && (filters.result === "all" || status === filters.result)
      && (filters.severity === "all" || severityOf(item) === filters.severity);
  }), [inspections, filters]);

  const buildReport = (rows) => {
    const completed = rows.filter((item) => ["GOOD", "DEFECT"].includes(statusOf(item)));
    const passed = completed.filter((item) => statusOf(item) === "GOOD").length;
    const defectInspections = completed.filter((item) => statusOf(item) === "DEFECT").length;
    const defectTypes = {};
    const categories = {};
    const findings = [];
    const recommendations = [];
    const qualityScores = [];
    const qualityStatuses = {};
    completed.forEach((item) => {
      const result = parseResult(item);
      const category = item.category || result?.category || "unknown";
      const severity = result?.quality_assessment?.severity;
      const qualityScore = Number(result?.image_quality?.quality_score);
      if (Number.isFinite(qualityScore)) qualityScores.push(qualityScore);
      if (result?.image_quality?.quality_status) {
        const qualityStatus = result.image_quality.quality_status;
        qualityStatuses[qualityStatus] = (qualityStatuses[qualityStatus] || 0) + 1;
      }
      categories[category] = (categories[category] || 0) + 1;
      if (severity?.level && severity.level !== "Low") findings.push({ category, level: severity.level, score: severity.score });
      if (result?.quality_assessment?.recommendation) recommendations.push(result.quality_assessment.recommendation);
      const detections = Array.isArray(result?.defects) ? result.defects : [];
      detections.forEach((defect) => {
        const type = defect.defect_type || result?.classification?.defect_type || "Detected Defect";
        defectTypes[type] = (defectTypes[type] || 0) + 1;
      });
      if (!detections.length && statusOf(item) === "DEFECT") {
        const type = result?.classification?.defect_type || "Detected Defect";
        defectTypes[type] = (defectTypes[type] || 0) + 1;
      }
    });
    const highestFinding = findings.sort((a, b) => Number(b.score || 0) - Number(a.score || 0))[0];
    const frequentTypes = Object.entries(defectTypes).sort((a, b) => b[1] - a[1]).slice(0, 5);
    const uniqueRecommendations = [...new Set(recommendations)];
    const riskLevel = highestFinding?.level || (defectInspections ? "Review" : "Low");
    return {
      total: rows.length, completed: completed.length, passed, defectInspections,
      passRate: completed.length ? (passed / completed.length) * 100 : 0,
      defectRate: completed.length ? (defectInspections / completed.length) * 100 : 0,
      totalDefects: Object.values(defectTypes).reduce((sum, count) => sum + count, 0),
      categories, frequentTypes, findings: findings.slice(0, 8), highestFinding,
      riskLevel, qualityStatus: rows.length ? (defectInspections ? "REVIEW REQUIRED" : "GOOD") : "NO DATA",
      recommendations: uniqueRecommendations.slice(0, 5),
      qualityConcerns: findings.length ? findings.map((item) => `${display(item.category)}: ${item.level} severity`).slice(0, 5) : [],
      averageQuality: qualityScores.length ? qualityScores.reduce((sum, score) => sum + score, 0) / qualityScores.length : null,
      qualityStatuses,
    };
  };

  const generateReport = () => {
    setGenerated({ id: `RPT-${Date.now()}`, generatedAt: new Date(), filters: { ...filters }, rows: filteredRows, summary: buildReport(filteredRows) });
  };

  const updateFilter = (name, value) => setFilters((current) => ({ ...current, [name]: value }));

  const exportCsv = () => {
    if (!generated) return;
    const header = ["Date", "Filename", "Category", "Result", "Defect Type", "Severity", "Severity Score", "Quality Score", "Recommendation"];
    const lines = generated.rows.map((item) => {
      const result = parseResult(item);
      const values = [item.created_at || "", item.filename || "", item.category || result?.category || "", statusOf(item), result?.classification?.defect_type || "", severityOf(item), result?.quality_assessment?.severity?.score ?? "", result?.image_quality?.quality_score ?? "", result?.quality_assessment?.recommendation || ""];
      return values.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(",");
    });
    const url = URL.createObjectURL(new Blob([[header.join(","), ...lines].join("\n")], { type: "text/csv;charset=utf-8" }));
    const link = document.createElement("a"); link.href = url; link.download = `${generated.id}.csv`; link.click(); URL.revokeObjectURL(url);
  };

  const exportPdf = async () => {
    if (!generated) return;
    const { jsPDF } = await import("jspdf");
    const pdf = new jsPDF();
    const { summary } = generated;
    let y = 18;
    const write = (text, size = 10, gap = 7) => { pdf.setFontSize(size); const lines = pdf.splitTextToSize(String(text), 180); pdf.text(lines, 14, y); y += lines.length * 5 + gap; if (y > 280) { pdf.addPage(); y = 18; } };
    write("VisionInspect AI", 20, 4); write(generated.filters.type, 14, 3);
    write(`Report ID: ${generated.id}`, 10, 2); write(`Generated: ${generated.generatedAt.toLocaleString()}`, 10, 2);
    write(`Period: ${generated.filters.from || "All dates"} to ${generated.filters.to || "All dates"}`, 10, 10);
    if (generated.filters.type === "Production Quality Report") {
      write("PRODUCTION QUALITY SUMMARY", 13, 4);
      write(`Total inspections: ${summary.total} | Pass rate: ${summary.passRate.toFixed(1)}% | Defect rate: ${summary.defectRate.toFixed(1)}% | Total defects: ${summary.totalDefects}`);
      write(`Average image quality: ${summary.averageQuality === null ? "Not recorded" : `${summary.averageQuality.toFixed(1)} / 100`} | Quality status: ${summary.qualityStatus}`, 10, 10);
      write("PRODUCTION ACTIONS", 13, 4); write(summary.recommendations.join("; ") || "No recommendation was recorded.");
    } else if (generated.filters.type === "Defect Report") {
      write("DEFECT FINDINGS", 13, 4);
      write(`Defect inspections: ${summary.defectInspections} | Localized defects: ${summary.totalDefects}`);
      write(`Frequent defect types: ${summary.frequentTypes.map(([name, count]) => `${display(name)} (${count})`).join(", ") || "None"}`);
      write(`Critical/High findings: ${summary.findings.filter((item) => ["Critical", "High"].includes(item.level)).map((item) => `${display(item.category)} - ${item.level}`).join(", ") || "None"}`, 10, 10);
      write("DEFECT FOLLOW-UP", 13, 4); write(summary.recommendations[0] || "No recommendation was recorded.");
    } else if (generated.filters.type === "Quality Risk Report") {
      write("RISK ASSESSMENT", 13, 4);
      write(`Overall risk level: ${summary.riskLevel}`);
      write(`Highest-risk category: ${summary.highestFinding ? display(summary.highestFinding.category) : "None"}`);
      write(`Important severity findings: ${summary.findings.map((item) => `${display(item.category)} - ${item.level}`).join(", ") || "None recorded"}`);
      write(`Quality concerns: ${summary.qualityConcerns.join("; ") || "None recorded."}`, 10, 10);
      write("RISK RECOMMENDATION", 13, 4); write(summary.recommendations.join("; ") || "No recommendation was recorded.");
    } else {
      write("INSPECTION SUMMARY", 13, 4);
      write(`Inspections: ${summary.total} | Completed: ${summary.completed} | Passed: ${summary.passed} | Defective: ${summary.defectInspections}`);
      write(`Pass rate: ${summary.passRate.toFixed(1)}% | Defect rate: ${summary.defectRate.toFixed(1)}%`, 10, 10);
      write("SUMMARY NOTES", 13, 4); write(summary.frequentTypes.map(([name, count]) => `${display(name)} (${count})`).join(", ") || "No findings recorded.");
    }
    pdf.save(`${generated.id}.pdf`);
  };

  return (
    <div className="dashboard-layout">
      <Sidebar />
      <main className="dashboard-main reports-page">
        <header className="dashboard-header"><div><div className="dashboard-breadcrumb">Workspace / Reports</div><h1>Production Quality Reports</h1></div></header>
        {error && <div className="camera-error">{error}</div>}
        <section className="report-generator">
          <div className="report-section-heading"><span className="report-eyebrow">REPORT GENERATOR</span><h2>Configure report</h2></div>
          <div className="report-form-grid">
            <label>Report Type<select value={filters.type} onChange={(event) => updateFilter("type", event.target.value)}>{REPORT_TYPES.map((type) => <option key={type}>{type}</option>)}</select></label>
            <label>From Date<input type="date" value={filters.from} onChange={(event) => updateFilter("from", event.target.value)} /></label>
            <label>To Date<input type="date" value={filters.to} onChange={(event) => updateFilter("to", event.target.value)} /></label>
            <label>Category<select value={filters.category} onChange={(event) => updateFilter("category", event.target.value)}>{CATEGORIES.map((category) => <option key={category} value={category}>{category === "all" ? "All categories" : display(category)}</option>)}</select></label>
            <label>Result<select value={filters.result} onChange={(event) => updateFilter("result", event.target.value)}><option value="all">All results</option><option value="GOOD">Good</option><option value="DEFECT">Defect</option></select></label>
            <label>Severity<select value={filters.severity} onChange={(event) => updateFilter("severity", event.target.value)}>{SEVERITIES.map((severity) => <option key={severity} value={severity}>{severity === "all" ? "All severities" : severity}</option>)}</select></label>
          </div>
          <button className="report-generate-button" type="button" onClick={generateReport}>Generate Report</button>
        </section>

        {generated && <section className="report-preview">
          <div className="report-preview-header"><div><span className="report-eyebrow">GENERATED REPORT PREVIEW</span><h2>{generated.filters.type}</h2></div><div className="report-export-actions"><button type="button" onClick={exportPdf}>Download PDF</button><button type="button" onClick={exportCsv}>Download CSV</button></div></div>
          <div className="report-information"><h3>REPORT INFORMATION</h3><div><span>Report ID<strong>{generated.id}</strong></span><span>Generated date<strong>{generated.generatedAt.toLocaleString("en-IN")}</strong></span><span>Reporting period<strong>{generated.filters.from || "All dates"} — {generated.filters.to || "All dates"}</strong></span><span>Selected filters<strong>{display(generated.filters.category)} · {generated.filters.result === "all" ? "All results" : generated.filters.result} · {generated.filters.severity === "all" ? "All severities" : generated.filters.severity}</strong></span></div></div>
          {generated.filters.type === "Production Quality Report" && <div className="report-summary-grid"><article><h3>PRODUCTION QUALITY SUMMARY</h3><div className="report-metric-grid"><span>Total inspections<strong>{generated.summary.total}</strong></span><span>Pass rate<strong>{generated.summary.passRate.toFixed(1)}%</strong></span><span>Defect rate<strong>{generated.summary.defectRate.toFixed(1)}%</strong></span><span>Total defects<strong>{generated.summary.totalDefects}</strong></span><span>Average image quality<strong>{generated.summary.averageQuality === null ? "Not recorded" : `${generated.summary.averageQuality.toFixed(1)} / 100`}</strong></span><span>Quality status<strong>{generated.summary.qualityStatus}</strong></span></div></article><article><h3>PRODUCTION ACTIONS</h3><p><b>Quality-control recommendations</b><strong>{generated.summary.recommendations.join(" ") || "No recommendation was recorded."}</strong></p><p><b>Areas requiring attention</b><strong>{generated.summary.qualityConcerns.join(", ") || "None recorded"}</strong></p><p><b>Risk status</b><strong>{generated.summary.riskLevel}</strong></p></article></div>}
          {generated.filters.type === "Defect Report" && <div className="report-summary-grid"><article><h3>DEFECT FINDINGS</h3><p><b>Total defect inspections</b><strong>{generated.summary.defectInspections}</strong></p><p><b>Total localized defects</b><strong>{generated.summary.totalDefects}</strong></p><p><b>Most frequent defect types</b><strong>{generated.summary.frequentTypes.map(([name, count]) => `${display(name)} (${count})`).join(", ") || "None recorded"}</strong></p></article><article><h3>DEFECT FOLLOW-UP</h3><p><b>Major defect categories</b><strong>{Object.keys(generated.summary.categories).filter((category) => generated.summary.categories[category] > 0).map(display).join(", ") || "None recorded"}</strong></p><p><b>Critical and High findings</b><strong>{generated.summary.findings.filter((item) => ["Critical", "High"].includes(item.level)).map((item) => `${display(item.category)} (${item.level})`).join(", ") || "None recorded"}</strong></p><p><b>Recommended action</b><strong>{generated.summary.recommendations[0] || "No recommendation was recorded."}</strong></p></article></div>}
          {generated.filters.type === "Quality Risk Report" && <div className="report-summary-grid"><article><h3>RISK ASSESSMENT</h3><p><b>Overall risk level</b><strong>{generated.summary.riskLevel}</strong></p><p><b>Highest-risk category</b><strong>{generated.summary.highestFinding ? display(generated.summary.highestFinding.category) : "None recorded"}</strong></p><p><b>Important severity findings</b><strong>{generated.summary.findings.map((item) => `${display(item.category)} — ${item.level} (${Number(item.score || 0).toFixed(1)})`).join(", ") || "None recorded"}</strong></p></article><article><h3>QUALITY CONCERNS</h3><p><b>Recorded concerns</b><strong>{generated.summary.qualityConcerns.join(", ") || "None recorded"}</strong></p><p><b>Risk recommendation</b><strong>{generated.summary.recommendations.join(" ") || "No recommendation was recorded."}</strong></p></article></div>}
          {generated.filters.type === "Inspection Summary Report" && <div className="report-summary-grid"><article><h3>INSPECTION SUMMARY</h3><div className="report-metric-grid"><span>Inspections<strong>{generated.summary.total}</strong></span><span>Completed<strong>{generated.summary.completed}</strong></span><span>Passed<strong>{generated.summary.passed}</strong></span><span>Defective<strong>{generated.summary.defectInspections}</strong></span><span>Pass rate<strong>{generated.summary.passRate.toFixed(1)}%</strong></span><span>Defect rate<strong>{generated.summary.defectRate.toFixed(1)}%</strong></span></div></article><article><h3>SUMMARY NOTES</h3><p><b>Quality status</b><strong>{generated.summary.qualityStatus}</strong></p><p><b>Recorded recommendations</b><strong>{generated.summary.recommendations.join(" ") || "None recorded"}</strong></p><p><b>Most frequent findings</b><strong>{generated.summary.frequentTypes.map(([name, count]) => `${display(name)} (${count})`).join(", ") || "None recorded"}</strong></p></article></div>}
        </section>}
      </main>
    </div>
  );
}

export default Reports;
