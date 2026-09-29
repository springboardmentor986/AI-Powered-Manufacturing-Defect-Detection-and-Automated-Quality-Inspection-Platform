"use client";

import {
  ChangeEvent,
  FormEvent,
  useEffect,
  useState,
} from "react";

const API = "http://127.0.0.1:8000";

type Result = {
  category: string;
  original_filename: string;
  inspection_id: number;

  image_quality: {
    width: number;
    height: number;
    brightness: number;
    contrast: number;
    sharpness_score: number;
    sharpness: string;
  };

  defect_detection: {
    is_defective: boolean;
    prediction: string;
    anomaly_score: number;
    confidence: number;
  };

  defect_classification?: {
    defect_type: string;
    classification_confidence: number;
    classification_method: string;
  };

  severity_assessment?: {
    severity_score: number;
    severity_level: string;
  };

  quality_result: {
    defect_type: string;
    confidence_score: number;
    severity_score: number;
    severity_level: string;
    is_passed: boolean;
  };
};

type Summary = {
  total_inspections: number;
  passed_inspections: number;
  failed_inspections: number;
  pass_rate: number;
  defect_rate: number;
  average_confidence: number;
  average_defect_severity: number;
};

type Defect = {
  defect_type: string;
  count: number;
};

type Severity = {
  severity_level: string;
  count: number;
};

type Product = {
  product_name: string;
  product_code: string;
  total_inspections: number;
  failed_inspections: number;
  pass_rate: number;
};

type RecentInspection = {
  inspection_id: number;
  product_name: string;
  product_code: string;
  status: string;
  created_at: string | null;
  defect_type: string | null;
  confidence_score: number | null;
  severity_score: number | null;
  severity_level: string | null;
  is_passed: boolean | null;
};

type Trend = {
  date: string;
  inspections: number;
  defects: number;
};

export default function Home() {
  const [category, setCategory] = useState("bottle");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState("");
  const [result, setResult] = useState<Result | null>(null);

  const [summary, setSummary] = useState<Summary | null>(null);
  const [defects, setDefects] = useState<Defect[]>([]);
  const [severity, setSeverity] = useState<Severity[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [recent, setRecent] = useState<RecentInspection[]>([]);
  const [trends, setTrends] = useState<Trend[]>([]);

  const [loading, setLoading] = useState(false);
  const [analyticsLoading, setAnalyticsLoading] = useState(true);
  const [active, setActive] = useState("Dashboard");
  const [error, setError] = useState("");

  const loadAnalytics = async () => {
    setAnalyticsLoading(true);

    try {
      const [
        summaryRes,
        defectsRes,
        severityRes,
        productsRes,
        recentRes,
        trendsRes,
      ] = await Promise.all([
        fetch(`${API}/analytics/summary`),
        fetch(`${API}/analytics/defects`),
        fetch(`${API}/analytics/severity`),
        fetch(`${API}/analytics/products`),
        fetch(`${API}/analytics/recent?limit=10`),
        fetch(`${API}/analytics/trends?days=7`),
      ]);

      if (
        !summaryRes.ok ||
        !defectsRes.ok ||
        !severityRes.ok ||
        !productsRes.ok ||
        !recentRes.ok ||
        !trendsRes.ok
      ) {
        throw new Error("Unable to load analytics data.");
      }

      const [
        summaryData,
        defectsData,
        severityData,
        productsData,
        recentData,
        trendsData,
      ] = await Promise.all([
        summaryRes.json(),
        defectsRes.json(),
        severityRes.json(),
        productsRes.json(),
        recentRes.json(),
        trendsRes.json(),
      ]);

      setSummary(summaryData);
      setDefects(defectsData.defects || []);
      setSeverity(severityData.severity || []);
      setProducts(productsData.products || []);
      setRecent(recentData.inspections || []);
      setTrends(trendsData.trends || []);
    } catch (err) {
      console.error(err);
      setError("Analytics service unavailable.");
    } finally {
      setAnalyticsLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
  }, []);

  const chooseFile = (e: ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];

    if (!selected) return;

    setFile(selected);
    setPreview(URL.createObjectURL(selected));
    setResult(null);
    setError("");
  };

  const analyze = async (e: FormEvent) => {
    e.preventDefault();

    if (!file) {
      setError("Select a product image before starting inspection.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const form = new FormData();

      form.append("category", category);
      form.append("file", file);

      const response = await fetch(`${API}/inspection/analyze`, {
        method: "POST",
        body: form,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Inspection failed.");
      }

      setResult(data);

      // Refresh live analytics after a new inspection
      await loadAnalytics();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to connect to VisionInspect AI."
      );
    } finally {
      setLoading(false);
    }
  };

  const maxTrend = Math.max(
    ...trends.map((item) =>
      Math.max(item.inspections, item.defects)
    ),
    1
  );

  const maxDefect = Math.max(
    ...defects.map((item) => item.count),
    1
  );

  const maxSeverity = Math.max(
    ...severity.map((item) => item.count),
    1
  );

  return (
    <main className="vision-app">

      {/* SIDEBAR */}

      <aside className="sidebar">

        <div className="logo-area">
          <div className="logo-mark">
            <span>VI</span>
          </div>

          <div>
            <h2>VisionInspect</h2>
            <p>AI QUALITY CONTROL</p>
          </div>
        </div>

        <div className="plant-status">
          <span className="pulse"></span>

          <div>
            <strong>Production System</strong>
            <small>Operational</small>
          </div>
        </div>

        <div className="menu-title">
          CONTROL CENTER
        </div>

        <nav>
          {[
            ["Dashboard", "⌂"],
            ["Inspection", "◎"],
            ["Inspection History", "▤"],
            ["Analytics", "◒"],
            ["Quality Control", "✓"],
            ["Production Reports", "▥"],
          ].map(([name, icon]) => (
            <button
              key={name}
              className={`menu-item ${
                active === name ? "selected" : ""
              }`}
              onClick={() => setActive(name)}
            >
              <span>{icon}</span>
              {name}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">

          <div className="ai-status">
            <div className="ai-orb">AI</div>

            <div>
              <strong>AI Engine</strong>
              <small>Isolation Forest</small>
            </div>

            <span className="online-dot"></span>
          </div>

          <div className="profile">
            <div className="profile-avatar">
              A
            </div>

            <div>
              <strong>Administrator</strong>
              <small>Quality Manager</small>
            </div>

            <span>•••</span>
          </div>

        </div>
      </aside>

      {/* MAIN */}

      <section className="main">

        {/* HEADER */}

        <header className="header">

          <div>
            <div className="breadcrumb">
              CONTROL CENTER / {active.toUpperCase()}
            </div>

            <h1>
              {active === "Dashboard"
                ? "Manufacturing Intelligence"
                : active}
            </h1>

            <p>
              AI-powered visual inspection and production
              quality monitoring
            </p>
          </div>

          <div className="header-actions">

            <div className="system-time">
              <span className="live"></span>
              LIVE SYSTEM
            </div>

            <button
              className="notification"
              onClick={loadAnalytics}
              title="Refresh analytics"
            >
              ↻
            </button>

            <div className="date-box">
              <small>PLANT STATUS</small>
              <strong>Operational</strong>
            </div>

          </div>

        </header>

        {/* KPI */}

        <section className="kpis">

          <KPI
            label="TOTAL INSPECTIONS"
            value={
              analyticsLoading
                ? "..."
                : String(summary?.total_inspections ?? 0)
            }
            detail="All recorded inspections"
            icon="◎"
          />

          <KPI
            label="QUALITY PASS RATE"
            value={
              analyticsLoading
                ? "..."
                : `${summary?.pass_rate ?? 0}%`
            }
            detail="Production quality"
            icon="✓"
          />

          <KPI
            label="DEFECT RATE"
            value={
              analyticsLoading
                ? "..."
                : `${summary?.defect_rate ?? 0}%`
            }
            detail="Detected production defects"
            icon="!"
            danger={
              (summary?.defect_rate ?? 0) > 50
            }
          />

          <KPI
            label="MODEL CONFIDENCE"
            value={
              analyticsLoading
                ? "..."
                : `${summary?.average_confidence ?? 0}%`
            }
            detail="Average AI confidence"
            icon="AI"
          />

        </section>

        {/* WORKSPACE */}

        <section className="dashboard-grid">

          {/* INSPECTION */}

          <div className="panel inspection-panel">

            <div className="panel-header">

              <div>
                <span className="panel-kicker">
                  COMPUTER VISION
                </span>

                <h2>AI Inspection Station</h2>
              </div>

              <span className="station-badge">
                ● STATION 01
              </span>

            </div>

            <form onSubmit={analyze}>

              <div className="inspection-controls">

                <div>
                  <label>PRODUCT CATEGORY</label>

                  <select
                    value={category}
                    onChange={(e) =>
                      setCategory(e.target.value)
                    }
                  >
                    <option value="bottle">Bottle</option>
                    <option value="cable">Cable</option>
                    <option value="screw">Screw</option>
                    <option value="tile">Tile</option>
                    <option value="toothbrush">
                      Toothbrush
                    </option>
                    <option value="wood">Wood</option>
                  </select>
                </div>

                <div className="model-chip">
                  <span>MODEL</span>
                  <strong>
                    {category}_anomaly_model
                  </strong>
                </div>

              </div>

              <label className="drop-zone">

                {preview ? (

                  <div className="preview-wrap">

                    <img
                      src={preview}
                      alt="Inspection"
                    />

                    <div className="scan-line"></div>

                    <div className="preview-overlay">
                      <span>VISION FEED</span>
                      <strong>
                        READY FOR ANALYSIS
                      </strong>
                    </div>

                  </div>

                ) : (

                  <div className="drop-content">

                    <div className="camera-icon">
                      ◉
                    </div>

                    <h3>
                      Drop inspection image
                    </h3>

                    <p>
                      Upload a product image for
                      automated computer vision
                      inspection
                    </p>

                    <span className="formats">
                      JPG • JPEG • PNG
                    </span>

                  </div>

                )}

                <input
                  type="file"
                  accept=".jpg,.jpeg,.png"
                  onChange={chooseFile}
                  hidden
                />

              </label>

              {file && (
                <div className="selected-file">
                  <span>IMAGE SELECTED</span>
                  <strong>{file.name}</strong>
                </div>
              )}

              {error && (
                <div className="error-message">
                  ⚠ {error}
                </div>
              )}

              <button
                className="inspect-button"
                disabled={loading}
              >
                <span>
                  {loading
                    ? "AI ENGINE ANALYZING..."
                    : "START AI INSPECTION"}
                </span>

                <b>→</b>
              </button>

            </form>
          </div>

          {/* RESULT */}

          <div className="panel result-panel">

            <div className="panel-header">

              <div>
                <span className="panel-kicker">
                  QUALITY ASSESSMENT
                </span>

                <h2>Inspection Intelligence</h2>
              </div>

              {result && (
                <span className="inspection-id">
                  #{result.inspection_id}
                </span>
              )}

            </div>

            {!result && (

              <div className="waiting">

                <div className="radar">
                  <div></div>
                  <div></div>
                  <div></div>
                  <span>AI</span>
                </div>

                <h3>Awaiting Inspection</h3>

                <p>
                  Upload a manufacturing image to
                  activate the AI quality assessment
                  engine.
                </p>

              </div>

            )}

            {result && (

              <div className="result-content">

                <div
                  className={`decision ${
                    result.defect_detection
                      .is_defective
                      ? "bad"
                      : "good"
                  }`}
                >

                  <div className="decision-icon">
                    {result.defect_detection
                      .is_defective
                      ? "!"
                      : "✓"}
                  </div>

                  <div>
                    <span>
                      FINAL QUALITY DECISION
                    </span>

                    <h3>
                      {result.quality_result
                        .is_passed
                        ? "QUALITY PASSED"
                        : "DEFECT DETECTED"}
                    </h3>
                  </div>

                </div>

                <div className="analysis-grid">

                  <Metric
                    label="DEFECT TYPE"
                    value={
                      result.quality_result
                        .defect_type
                    }
                  />

                  <Metric
                    label="CONFIDENCE"
                    value={`${result.defect_detection.confidence}%`}
                  />

                  <Metric
                    label="SEVERITY SCORE"
                    value={`${result.quality_result.severity_score}/100`}
                  />

                  <Metric
                    label="SEVERITY LEVEL"
                    value={
                      result.quality_result
                        .severity_level
                    }
                  />

                </div>

                <div className="quality-analysis">

                  <div className="quality-title">
                    IMAGE QUALITY ANALYSIS
                  </div>

                  <QualityBar
                    label="Brightness"
                    value={
                      result.image_quality
                        .brightness
                    }
                  />

                  <QualityBar
                    label="Contrast"
                    value={
                      result.image_quality.contrast
                    }
                  />

                  <QualityBar
                    label="Sharpness"
                    value={Math.min(
                      100,
                      result.image_quality
                        .sharpness_score / 20
                    )}
                  />

                </div>

                <div className="recommendation">

                  <span>
                    QUALITY CONTROL ACTION
                  </span>

                  <strong>
                    {result.quality_result
                      .is_passed
                      ? "Product approved for production"
                      : "Product requires quality review"}
                  </strong>

                </div>

              </div>
            )}

          </div>

        </section>

        {/* ANALYTICS */}

        <section className="lower-grid">

          {/* TREND */}

          <div className="panel chart-panel">

            <div className="panel-header">

              <div>
                <span className="panel-kicker">
                  MANUFACTURING ANALYTICS
                </span>

                <h2>
                  Inspection & Defect Trends
                </h2>
              </div>

              <button
                className="refresh-button"
                onClick={loadAnalytics}
              >
                ↻ Refresh
              </button>

            </div>

            <div className="chart">

              {trends.map((item) => {

                const inspectionHeight =
                  (item.inspections / maxTrend) *
                  100;

                const defectHeight =
                  (item.defects / maxTrend) *
                  100;

                return (
                  <div
                    className="bar-group"
                    key={item.date}
                  >

                    <div className="trend-bars">

                      <div
                        className="bar"
                        style={{
                          height: `${Math.max(
                            inspectionHeight,
                            3
                          )}%`,
                        }}
                        title={`Inspections: ${item.inspections}`}
                      ></div>

                      <div
                        className="bar defect-bar"
                        style={{
                          height: `${Math.max(
                            defectHeight,
                            item.defects > 0
                              ? 3
                              : 0
                          )}%`,
                        }}
                        title={`Defects: ${item.defects}`}
                      ></div>

                    </div>

                    <span>
                      {item.date.slice(5)}
                    </span>

                  </div>
                );
              })}

            </div>

            <div className="chart-footer">

              <div>
                <span className="legend-dot blue"></span>
                Inspections
              </div>

              <div>
                <span className="legend-dot red"></span>
                Defects
              </div>

              <strong>
                7-day monitoring
              </strong>

            </div>

          </div>

          {/* DEFECT DISTRIBUTION */}

          <div className="panel system-panel">

            <div className="panel-header">

              <div>
                <span className="panel-kicker">
                  DEFECT INTELLIGENCE
                </span>

                <h2>
                  Defect Distribution
                </h2>
              </div>

            </div>

            {defects.length === 0 ? (

              <div className="no-data">
                No defects recorded.
              </div>

            ) : (

              <div className="analytics-list">

                {defects.map((item) => (

                  <div
                    className="analytics-item"
                    key={item.defect_type}
                  >

                    <div className="analytics-label">
                      <span>
                        {item.defect_type}
                      </span>

                      <strong>
                        {item.count}
                      </strong>
                    </div>

                    <div className="bar-track">
                      <div
                        className="bar-fill"
                        style={{
                          width: `${
                            (item.count /
                              maxDefect) *
                            100
                          }%`,
                        }}
                      ></div>
                    </div>

                  </div>

                ))}

              </div>
            )}

          </div>

          {/* SEVERITY */}

          <div className="panel system-panel">

            <div className="panel-header">

              <div>
                <span className="panel-kicker">
                  RISK MANAGEMENT
                </span>

                <h2>
                  Severity Distribution
                </h2>
              </div>

            </div>

            {severity.length === 0 ? (

              <div className="no-data">
                No severity records.
              </div>

            ) : (

              <div className="analytics-list">

                {severity.map((item) => (

                  <div
                    className="analytics-item"
                    key={item.severity_level}
                  >

                    <div className="analytics-label">
                      <span>
                        {item.severity_level}
                      </span>

                      <strong>
                        {item.count}
                      </strong>
                    </div>

                    <div className="bar-track">
                      <div
                        className="bar-fill"
                        style={{
                          width: `${
                            (item.count /
                              maxSeverity) *
                            100
                          }%`,
                        }}
                      ></div>
                    </div>

                  </div>

                ))}

              </div>
            )}

          </div>

        </section>

        {/* PRODUCT ANALYTICS */}

        <section className="panel recent-panel">

          <div className="panel-header">

            <div>
              <span className="panel-kicker">
                PRODUCTION QUALITY
              </span>

              <h2>
                Product Performance
              </h2>
            </div>

          </div>

          {products.length === 0 ? (

            <div className="no-data">
              No product analytics available.
            </div>

          ) : (

            <div className="table-wrapper">

              <table className="analytics-table">

                <thead>
                  <tr>
                    <th>PRODUCT</th>
                    <th>CODE</th>
                    <th>INSPECTIONS</th>
                    <th>FAILED</th>
                    <th>PASS RATE</th>
                  </tr>
                </thead>

                <tbody>

                  {products.map((product) => (

                    <tr
                      key={product.product_code}
                    >

                      <td>
                        <strong>
                          {product.product_name}
                        </strong>
                      </td>

                      <td>
                        {product.product_code}
                      </td>

                      <td>
                        {product.total_inspections}
                      </td>

                      <td>
                        {product.failed_inspections}
                      </td>

                      <td>
                        <span
                          className={
                            product.pass_rate >= 80
                              ? "status-pass"
                              : "status-defect"
                          }
                        >
                          {product.pass_rate}%
                        </span>
                      </td>

                    </tr>

                  ))}

                </tbody>

              </table>

            </div>
          )}

        </section>

        {/* RECENT INSPECTIONS */}

        <section className="panel recent-panel">

          <div className="panel-header">

            <div>
              <span className="panel-kicker">
                INSPECTION MANAGEMENT
              </span>

              <h2>
                Recent Inspections
              </h2>
            </div>

            <span className="station-badge">
              LIVE DATABASE
            </span>

          </div>

          {recent.length === 0 ? (

            <div className="no-data">
              No inspection records available.
            </div>

          ) : (

            <div className="recent-table">

              {recent.map((inspection) => (

                <div
                  className="recent-row"
                  key={inspection.inspection_id}
                >

                  <div className="recent-image">
                    <span>VI</span>
                  </div>

                  <div className="recent-info">

                    <strong>
                      Inspection #
                      {inspection.inspection_id}
                    </strong>

                    <span>
                      {inspection.product_name}
                    </span>

                    <small>
                      {inspection.defect_type ||
                        "No Defect"}
                    </small>

                  </div>

                  <div className="recent-metric">

                    <span>CONFIDENCE</span>

                    <strong>
                      {inspection.confidence_score !==
                      null
                        ? `${inspection.confidence_score}%`
                        : "—"}
                    </strong>

                  </div>

                  <div className="recent-metric">

                    <span>SEVERITY</span>

                    <strong>
                      {inspection.severity_level ||
                        "None"}
                    </strong>

                  </div>

                  <div
                    className={
                      inspection.is_passed
                        ? "status-pass"
                        : "status-defect"
                    }
                  >
                    {inspection.is_passed
                      ? "PASSED"
                      : "DEFECT"}
                  </div>

                </div>

              ))}

            </div>
          )}

        </section>

        {/* SYSTEM */}

        <section className="panel system-panel">

          <div className="panel-header">

            <div>
              <span className="panel-kicker">
                AI INFRASTRUCTURE
              </span>

              <h2>
                System Intelligence
              </h2>
            </div>

          </div>

          <SystemRow
            label="FastAPI Backend"
            value="ONLINE"
          />

          <SystemRow
            label="PostgreSQL Database"
            value="CONNECTED"
          />

          <SystemRow
            label="OpenCV Pipeline"
            value="READY"
          />

          <SystemRow
            label="Anomaly Detection"
            value="ACTIVE"
          />

          <SystemRow
            label="Manufacturing Analytics"
            value="ACTIVE"
          />

        </section>

        <footer>

          <span>
            VISIONINSPECT AI
          </span>

          <span>
            Manufacturing Defect Detection &
            Quality Inspection System
          </span>

          <span>
            AI ENGINE v1.0
          </span>

        </footer>

      </section>
    </main>
  );
}


/* KPI */

function KPI({
  label,
  value,
  detail,
  icon,
  danger,
}: {
  label: string;
  value: string;
  detail: string;
  icon: string;
  danger?: boolean;
}) {
  return (
    <div className="kpi">

      <div className="kpi-top">

        <span>{label}</span>

        <div
          className={`kpi-icon ${
            danger ? "danger" : ""
          }`}
        >
          {icon}
        </div>

      </div>

      <strong
        className={
          danger ? "danger-text" : ""
        }
      >
        {value}
      </strong>

      <small>{detail}</small>

    </div>
  );
}


/* METRIC */

function Metric({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="metric">

      <span>{label}</span>

      <strong>{value}</strong>

    </div>
  );
}


/* QUALITY BAR */

function QualityBar({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  const percentage = Math.min(
    100,
    Math.max(0, value)
  );

  return (
    <div className="quality-bar">

      <div>
        <span>{label}</span>

        <strong>
          {value.toFixed(1)}
        </strong>
      </div>

      <div className="bar-track">

        <div
          className="bar-fill"
          style={{
            width: `${percentage}%`,
          }}
        ></div>

      </div>

    </div>
  );
}


/* SYSTEM ROW */

function SystemRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="system-row">

      <div>
        <span className="system-dot"></span>
        {label}
      </div>

      <strong>{value}</strong>

    </div>
  );
}