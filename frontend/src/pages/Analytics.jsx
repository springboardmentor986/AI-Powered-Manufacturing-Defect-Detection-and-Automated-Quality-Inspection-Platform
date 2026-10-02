import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import Sidebar from "../components/Sidebar";

const CATEGORIES = [
  "bottle", "cable", "capsule", "carpet", "grid", "hazelnut",
  "leather", "metal_nut", "pill", "screw", "tile", "toothbrush",
  "transistor", "wood", "zipper",
];

function parseResult(item) {
  if (!item) return null;
  if (typeof item.result === "object" && item.result !== null) return item.result;
  if (typeof item.result === "string") {
    try { return JSON.parse(item.result); } catch { return null; }
  }
  return null;
}

const titleCase = (value = "") =>
  String(value).replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

function Analytics() {
  const navigate = useNavigate();
  const [inspections, setInspections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");

  const loadAnalytics = useCallback(async (silent = false) => {
    try {
      silent ? setRefreshing(true) : setLoading(true);
      setError("");
      const response = await api.get("/inspections/");
      const data = Array.isArray(response.data)
        ? response.data
        : response.data?.items ?? [];
      setInspections(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to load inspection analytics.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadAnalytics();
  }, [loadAnalytics]);

  const analytics = useMemo(() => {
    const filteredInspections = inspections.filter((item) => {
      const date = item.created_at ? new Date(item.created_at).toISOString().slice(0, 10) : "";
      return (!fromDate || date >= fromDate) && (!toDate || date <= toDate);
    });
    const completed = filteredInspections.filter(
      (x) => String(x.status || "").toLowerCase() === "completed"
    );
    const results = completed.map((item) => ({ item, result: parseResult(item) }));
    const defective = results.filter(
      ({ result }) => String(result?.status || "").toUpperCase() === "DEFECT"
    );
    const good = results.filter(
      ({ result }) => String(result?.status || "").toUpperCase() === "GOOD"
    );
    const pending = filteredInspections.filter((x) =>
      ["processing", "pending"].includes(String(x.status || "").toLowerCase())
    );
    const failed = filteredInspections.filter(
      (x) => String(x.status || "").toLowerCase() === "failed"
    );

    const scores = completed
      .map((x) => Number(parseResult(x)?.image_quality?.quality_score))
      .filter(Number.isFinite);
    const averageQuality = scores.length
      ? scores.reduce((a, b) => a + b, 0) / scores.length
      : 0;
    const defectRate = completed.length ? (defective.length / completed.length) * 100 : 0;
    const passRate = completed.length ? (good.length / completed.length) * 100 : 0;

    const categoryMap = {};
    CATEGORIES.forEach((c) => {
      categoryMap[c] = { total: 0, good: 0, defect: 0 };
    });
    filteredInspections.forEach((item) => {
      const category = item.category || parseResult(item)?.category || "unknown";
      if (!categoryMap[category]) categoryMap[category] = { total: 0, good: 0, defect: 0 };
      categoryMap[category].total += 1;
      const status = String(parseResult(item)?.status || "").toUpperCase();
      if (status === "GOOD") categoryMap[category].good += 1;
      if (status === "DEFECT") categoryMap[category].defect += 1;
    });
    const categories = Object.entries(categoryMap)
      .filter(([, v]) => v.total > 0)
      .sort((a, b) => b[1].total - a[1].total);

    const defectTypes = {};
    defective.forEach(({ result }) => {
      const detections = Array.isArray(result?.defects) ? result.defects : [];
      if (detections.length) {
        detections.forEach((d) => {
          const type = d.defect_type || d.class_name || d.type || "Detected Defect";
          defectTypes[type] = (defectTypes[type] || 0) + 1;
        });
      } else {
        const type = result?.classification?.defect_type || "Detected Defect";
        defectTypes[type] = (defectTypes[type] || 0) + 1;
      }
    });
    const sortedDefectTypes = Object.entries(defectTypes)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6);

    const trendMap = {};
    completed.forEach((item) => {
      if (!item.created_at) return;
      const d = new Date(item.created_at);
      if (Number.isNaN(d.getTime())) return;
      const key = d.toISOString().slice(0, 10);
      if (!trendMap[key]) trendMap[key] = { date: key, inspections: 0, defects: 0, good: 0 };
      trendMap[key].inspections += 1;
      const status = String(parseResult(item)?.status || "").toUpperCase();
      if (status === "DEFECT") trendMap[key].defects += 1;
      if (status === "GOOD") trendMap[key].good += 1;
    });
    const trend = Object.values(trendMap).sort((a, b) => a.date.localeCompare(b.date)).slice(-7);

    const totalDefectDetections = defective.reduce((sum, { result }) =>
      sum + (Array.isArray(result?.defects) ? result.defects.length : 1), 0);

    return {
      total: filteredInspections.length, completed: completed.length, good: good.length,
      defective: defective.length, pending: pending.length, failed: failed.length,
      averageQuality, defectRate, passRate, categories, sortedDefectTypes, trend,
      totalDefectDetections,
    };
  }, [inspections, fromDate, toDate]);

  const maxCategory = Math.max(...analytics.categories.map(([, v]) => v.total), 1);
  const maxDefect = Math.max(...analytics.sortedDefectTypes.map(([, v]) => v), 1);
  const maxTrend = Math.max(...analytics.trend.map((v) => v.inspections), 1);

  const qualityLabel =
    analytics.averageQuality >= 80 ? "Excellent" :
    analytics.averageQuality >= 60 ? "Good" :
    analytics.averageQuality >= 40 ? "Fair" : "Poor";

  return (
    <div className="analytics-v3">
      <style>{`
        .analytics-v3{min-height:100vh;display:flex;background:#f4f7fb;color:#0f172a;font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
        .analytics-v3 *{box-sizing:border-box}
        .analytics-v3 .side{width:248px;background:linear-gradient(180deg,#0b1730 0%,#101f3e 100%);color:#fff;padding:24px 14px;display:flex;flex-direction:column;position:fixed;inset:0 auto 0 0;z-index:5}
        .analytics-v3 .brand{display:flex;align-items:center;gap:11px;padding:4px 10px 28px}
        .analytics-v3 .logo{width:42px;height:42px;border-radius:12px;background:linear-gradient(135deg,#2563eb,#38bdf8);display:grid;place-items:center;font-weight:900;font-size:20px;box-shadow:0 8px 22px #2563eb40}
        .analytics-v3 .brand b{display:block;font-size:16px;letter-spacing:-.3px}.analytics-v3 .brand b span{color:#60a5fa}.analytics-v3 .brand small{font-size:8px;letter-spacing:1.4px;color:#91a4c5}
        .analytics-v3 .section{font-size:10px;font-weight:800;letter-spacing:1.2px;color:#7184a7;padding:0 12px 10px}
        .analytics-v3 .nav{display:flex;flex-direction:column;gap:6px}
        .analytics-v3 .nav button,.analytics-v3 .logout{border:0;background:transparent;color:#aebbd0;text-align:left;width:100%;padding:12px 13px;border-radius:11px;display:flex;align-items:center;gap:12px;font-size:13px;font-weight:650;cursor:pointer;transition:.2s}
        .analytics-v3 .nav button:hover,.analytics-v3 .logout:hover{background:#ffffff0d;color:#fff;transform:translateX(2px)}
        .analytics-v3 .nav button.active{background:linear-gradient(90deg,#2563eb,#1d4ed8);color:#fff;box-shadow:0 8px 20px #2563eb35}
        .analytics-v3 .nav-icon{width:20px;text-align:center;font-size:17px}.analytics-v3 .bottom{margin-top:auto}.analytics-v3 .logout{color:#9eacc3}
        .analytics-v3 .main{margin-left:0;width:auto;flex:1;min-width:0;padding:28px 34px 42px}
        .analytics-v3 .top{display:flex;align-items:center;justify-content:space-between;gap:18px;margin-bottom:26px}
        .analytics-v3 .crumb{font-size:11px;color:#7890b2;font-weight:650;margin-bottom:7px}.analytics-v3 h1{font-size:29px;line-height:1.1;margin:0;letter-spacing:-.8px}.analytics-v3 .sub{margin:8px 0 0;color:#718096;font-size:13px}
        .analytics-v3 .actions{display:flex;gap:10px}.analytics-v3 .btn{border:1px solid #d9e2ee;background:#fff;color:#334155;border-radius:10px;padding:10px 14px;font-weight:750;cursor:pointer}.analytics-v3 .btn.primary{background:#2563eb;border-color:#2563eb;color:#fff;box-shadow:0 7px 18px #2563eb2e}.analytics-v3 .btn:disabled{opacity:.6;cursor:not-allowed}
        .analytics-v3 .grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:18px}
        .analytics-v3 .card{background:#fff;border:1px solid #e4eaf2;border-radius:16px;box-shadow:0 8px 28px #0f172a0a}
        .analytics-v3 .kpi{padding:18px 19px;position:relative;overflow:hidden}.analytics-v3 .kpi:after{content:"";position:absolute;width:80px;height:80px;border-radius:50%;background:#2563eb08;right:-25px;top:-25px}
        .analytics-v3 .kpi-top{display:flex;justify-content:space-between;align-items:center}.analytics-v3 .kicon{width:38px;height:38px;border-radius:11px;background:#eff6ff;color:#2563eb;display:grid;place-items:center;font-weight:900}.analytics-v3 .klabel{font-size:12px;color:#718096;font-weight:700}.analytics-v3 .kvalue{font-size:27px;font-weight:850;margin-top:10px;letter-spacing:-.5px}.analytics-v3 .knote{font-size:11px;color:#94a3b8;margin-top:4px}
        .analytics-v3 .twocol{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:18px}.analytics-v3 .panel{padding:21px}.analytics-v3 .panel-head{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin-bottom:19px}.analytics-v3 .panel h2{font-size:16px;margin:0;letter-spacing:-.2px}.analytics-v3 .panel p{font-size:11px;color:#8a98aa;margin:5px 0 0}
        .analytics-v3 .outcome{display:grid;grid-template-columns:135px 1fr;gap:22px;align-items:center}.analytics-v3 .donut{width:128px;height:128px;border-radius:50%;display:grid;place-items:center}.analytics-v3 .donut-inner{width:91px;height:91px;border-radius:50%;background:#fff;display:grid;place-items:center;text-align:center}.analytics-v3 .donut-inner b{font-size:22px}.analytics-v3 .donut-inner span{font-size:9px;color:#94a3b8;display:block}
        .analytics-v3 .legend{display:flex;flex-direction:column;gap:12px}.analytics-v3 .legend-row{display:grid;grid-template-columns:9px 1fr auto;align-items:center;gap:8px;font-size:12px}.analytics-v3 .dot{width:8px;height:8px;border-radius:50%}.analytics-v3 .legend-row span{color:#64748b}.analytics-v3 .legend-row b{font-size:12px}
        .analytics-v3 .quality-wrap{display:flex;align-items:center;gap:24px}.analytics-v3 .quality-ring{width:122px;height:122px;border-radius:50%;display:grid;place-items:center;flex:0 0 auto}.analytics-v3 .quality-ring-in{width:88px;height:88px;border-radius:50%;background:#fff;display:grid;place-items:center;text-align:center}.analytics-v3 .quality-ring-in b{font-size:23px}.analytics-v3 .quality-ring-in span{font-size:9px;color:#94a3b8}.analytics-v3 .quality-copy b{font-size:15px}.analytics-v3 .quality-copy p{line-height:1.6;font-size:12px;color:#64748b;margin-top:7px}
        .analytics-v3 .bar-row{margin:14px 0}.analytics-v3 .bar-label{display:flex;justify-content:space-between;font-size:11px;font-weight:700;margin-bottom:6px}.analytics-v3 .bar-label span{color:#475569}.analytics-v3 .bar-bg{height:9px;background:#edf2f7;border-radius:20px;overflow:hidden}.analytics-v3 .bar{height:100%;border-radius:20px;background:linear-gradient(90deg,#2563eb,#60a5fa)}
        .analytics-v3 .threecol{display:grid;grid-template-columns:1.15fr .85fr;gap:18px;margin-bottom:18px}.analytics-v3 .trend{height:190px;display:flex;align-items:flex-end;gap:14px;padding:8px 4px 0;overflow-x:auto}.analytics-v3 .trend-item{min-width:48px;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;gap:6px}.analytics-v3 .trend-value{font-size:10px;font-weight:800}.analytics-v3 .trend-bar{width:31px;border-radius:8px 8px 3px 3px;background:linear-gradient(180deg,#60a5fa,#2563eb);min-height:4px}.analytics-v3 .trend-date{font-size:9px;color:#8492a6;white-space:nowrap}.analytics-v3 .trend-def{font-size:9px;color:#dc2626;font-weight:750}
        .analytics-v3 .insight-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.analytics-v3 .insight{padding:14px;border-radius:12px;background:#f8fafc;border:1px solid #edf1f6}.analytics-v3 .insight label{display:block;font-size:10px;color:#8492a6;font-weight:700}.analytics-v3 .insight b{display:block;margin-top:5px;font-size:14px}.analytics-v3 .footer-note{margin-top:18px;color:#94a3b8;font-size:10px}
        .analytics-v3 .loading,.analytics-v3 .error{padding:35px;text-align:center}.analytics-v3 .error{color:#b42318;background:#fff1f2;border:1px solid #fecdd3;border-radius:12px}
        @media(max-width:1050px){.analytics-v3 .grid4{grid-template-columns:repeat(2,1fr)}.analytics-v3 .twocol,.analytics-v3 .threecol{grid-template-columns:1fr}}
        @media(max-width:760px){.analytics-v3 .side{position:relative;width:100%;height:auto;inset:auto}.analytics-v3{display:block}.analytics-v3 .main{margin-left:0;width:100%;padding:20px}.analytics-v3 .grid4{grid-template-columns:1fr 1fr}.analytics-v3 .top{align-items:flex-start}.analytics-v3 .actions{flex-wrap:wrap}.analytics-v3 .outcome{grid-template-columns:1fr}.analytics-v3 .insight-grid{grid-template-columns:1fr}}
        @media(max-width:480px){.analytics-v3 .grid4{grid-template-columns:1fr}.analytics-v3 h1{font-size:24px}}
      `}</style>

      <Sidebar />

      <main className="main">
        <header className="top">
          <div>
            <div className="crumb">Dashboard / Analytics</div>
            <h1>Image Analytics</h1>
            <p className="sub">Monitor inspection performance, quality levels and defect patterns.</p>
          </div>
          <div className="actions">
            <label className="analytics-date-filter">From <input type="date" value={fromDate} onChange={(event) => setFromDate(event.target.value)} /></label>
            <label className="analytics-date-filter">To <input type="date" value={toDate} onChange={(event) => setToDate(event.target.value)} /></label>
            <button className="btn" onClick={() => navigate("/history")}>View History</button>
            <button className="btn primary" onClick={() => navigate("/inspection")}>+ New Inspection</button>
            <button className="btn" disabled={refreshing} onClick={() => loadAnalytics(true)}>
              {refreshing ? "Refreshing..." : "↻ Refresh"}
            </button>
          </div>
        </header>

        {loading ? (
          <div className="card loading">Loading inspection analytics...</div>
        ) : error ? (
          <div className="error">{error}</div>
        ) : (
          <>
            <section className="grid4">
              {[
                ["▣", "Total Inspections", analytics.total, "All recorded inspections"],
                ["✓", "Good Parts", analytics.good, `${analytics.passRate.toFixed(1)}% pass rate`],
                ["⚠", "Defects Detected", analytics.defective, `${analytics.defectRate.toFixed(1)}% defect rate`],
                ["◎", "Avg Image Quality", analytics.averageQuality.toFixed(1), `${qualityLabel} · score / 100`],
              ].map(([icon, label, value, note]) => (
                <div className="card kpi" key={label}>
                  <div className="kpi-top"><div className="klabel">{label}</div><div className="kicon">{icon}</div></div>
                  <div className="kvalue">{value}</div><div className="knote">{note}</div>
                </div>
              ))}
            </section>

            <section className="twocol">
              <div className="card panel">
                <div className="panel-head"><div><h2>Inspection Outcome</h2><p>Distribution of completed inspections</p></div></div>
                <div className="outcome">
                  <div className="donut" style={{background:`conic-gradient(#16a34a 0 ${analytics.total ? analytics.good/analytics.total*360 : 0}deg,#ef4444 0 ${analytics.total ? (analytics.good+analytics.defective)/analytics.total*360 : 0}deg,#f59e0b 0 ${analytics.total ? (analytics.good+analytics.defective+analytics.pending)/analytics.total*360 : 0}deg,#8b5cf6 0 360deg)`}}>
                    <div className="donut-inner"><div><b>{analytics.completed}</b><span>completed</span></div></div>
                  </div>
                  <div className="legend">
                    {[
                      ["#16a34a","Good",analytics.good],
                      ["#ef4444","Defect",analytics.defective],
                      ["#f59e0b","Pending",analytics.pending],
                      ["#8b5cf6","Failed",analytics.failed],
                    ].map(([color,label,value]) => (
                      <div className="legend-row" key={label}><i className="dot" style={{background:color}}/><span>{label}</span><b>{value}</b></div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="card panel">
                <div className="panel-head"><div><h2>Image Quality</h2><p>Average quality score from inspected images</p></div></div>
                <div className="quality-wrap">
                  <div className="quality-ring" style={{background:`conic-gradient(#2563eb ${Math.min(Math.max(analytics.averageQuality,0),100)*3.6}deg,#e8eef8 0deg)`}}>
                    <div className="quality-ring-in"><div><b>{analytics.averageQuality.toFixed(1)}</b><span>/ 100</span></div></div>
                  </div>
                  <div className="quality-copy"><b>{qualityLabel} image quality</b><p>Based on brightness, contrast, sharpness and noise analysis produced during image inspection.</p></div>
                </div>
              </div>
            </section>

            <section className="card panel" style={{marginBottom:18}}>
              <div className="panel-head"><div><h2>Category-wise Inspection Statistics</h2><p>Real inspection records grouped by MVTec product category</p></div></div>
              {analytics.categories.length === 0 ? <p>No inspection records available yet.</p> : analytics.categories.map(([category, value]) => (
                <div className="bar-row" key={category}>
                  <div className="bar-label"><span>{titleCase(category)}</span><b>{value.total} inspections · {value.defect} defects</b></div>
                  <div className="bar-bg"><div className="bar" style={{width:`${value.total/maxCategory*100}%`}}/></div>
                </div>
              ))}
            </section>

            <section className="threecol">
              <div className="card panel">
                <div className="panel-head"><div><h2>Inspection Trend</h2><p>Last 7 dates with completed inspections</p></div></div>
                {analytics.trend.length === 0 ? <p>No completed trend data yet.</p> : (
                  <div className="trend">
                    {analytics.trend.map((item) => (
                      <div className="trend-item" key={item.date}>
                        <span className="trend-value">{item.inspections}</span>
                        <div className="trend-bar" title={`${item.inspections} inspections, ${item.defects} defects`} style={{height:`${Math.max(item.inspections/maxTrend*140, item.inspections ? 8 : 3)}px`}}/>
                        <span className="trend-date">{new Date(`${item.date}T00:00:00`).toLocaleDateString("en-IN",{day:"2-digit",month:"short"})}</span>
                        {item.defects > 0 && <span className="trend-def">{item.defects} defect{item.defects !== 1 ? "s" : ""}</span>}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="card panel">
                <div className="panel-head"><div><h2>Detected Defect Types</h2><p>Most frequently reported defects</p></div></div>
                {analytics.sortedDefectTypes.length === 0 ? <p>No defects detected yet.</p> : analytics.sortedDefectTypes.map(([type,count]) => (
                  <div className="bar-row" key={type}>
                    <div className="bar-label"><span>{titleCase(type)}</span><b>{count}</b></div>
                    <div className="bar-bg"><div className="bar" style={{width:`${count/maxDefect*100}%`,background:"linear-gradient(90deg,#ef4444,#fb7185)"}}/></div>
                  </div>
                ))}
              </div>
            </section>

            <section className="card panel">
              <div className="panel-head"><div><h2>Operational Insights</h2><p>Quick summary derived from current inspection records</p></div></div>
              <div className="insight-grid">
                <div className="insight"><label>Most Inspected Category</label><b>{analytics.categories[0] ? titleCase(analytics.categories[0][0]) : "—"}</b></div>
                <div className="insight"><label>Highest Defect Category</label><b>{analytics.categories.length ? titleCase([...analytics.categories].sort((a,b)=>b[1].defect-a[1].defect)[0][0]) : "—"}</b></div>
                <div className="insight"><label>Total Defect Detections</label><b>{analytics.totalDefectDetections}</b></div>
              </div>
              <div className="footer-note">Analytics are calculated from inspection records returned by the existing inspection API.</div>
            </section>
          </>
        )}
      </main>
    </div>
  );
}

export default Analytics;
