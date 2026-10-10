import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Sidebar from "../components/Sidebar";
import { getToken, getAnalyticsSummary } from "../lib/api";
import { ui, badge, downloadCsv } from "../lib/ui";

const SEVERITY_COLORS = {
  critical: "#ff5c5c",
  high: "#f5a623",
  medium: "#e8d44d",
  low: "#3dd68c",
  unknown: "#8a94a1",
};

export default function Reports() {
  const router = useRouter();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    (async () => {
      try {
        setData(await getAnalyticsSummary());
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [router]);

  const today = new Date().toISOString().slice(0, 10);
  const cats = data ? data.category_breakdown : [];
  const types = data ? data.defect_type_breakdown : [];
  const sev = data ? data.severity_breakdown : [];
  const typeTotal = types.reduce((sum, t) => sum + t.count, 0);
  const share = (c) => (typeTotal ? Math.round((c / typeTotal) * 1000) / 10 : 0);

  const exportCategories = () =>
    downloadCsv(
      "category_report_" + today + ".csv",
      ["category", "total", "pass", "fail", "fail_rate_percent"],
      cats.map((c) => [c.category, c.total, c.pass, c.fail, c.fail_rate])
    );

  const exportTypes = () =>
    downloadCsv(
      "defect_type_report_" + today + ".csv",
      ["defect_type", "count", "share_percent"],
      types.map((t) => [t.type, t.count, share(t.count)])
    );

  const exportSeverity = () =>
    downloadCsv(
      "severity_report_" + today + ".csv",
      ["severity", "count"],
      sev.map((s) => [s.severity, s.count])
    );

  return (
    <div style={ui.shell}>
      <Sidebar />
      <div style={ui.page}>
        <header style={ui.header}>
          <div>
            <div style={ui.eyebrow}>VISIONINSPECT AI - REPORTS</div>
            <h1 style={ui.title}>Quality Reports</h1>
            <div style={ui.subtitle}>
              Summaries of all completed inspections. Download any table as CSV.
            </div>
          </div>
        </header>

        {loading && <div style={ui.msg}>Loading reports...</div>}
        {error && <div style={ui.msg}>Error: {error}</div>}

        {!loading && !error && data && (
          <>
            <section style={ui.statGrid}>
              <div style={ui.stat}>
                <div style={ui.statValue}>{data.total_inspections}</div>
                <div style={ui.statLabel}>Total inspections</div>
              </div>
              <div style={ui.stat}>
                <div style={{ ...ui.statValue, color: "#3dd68c" }}>{data.pass_rate}%</div>
                <div style={ui.statLabel}>Pass rate</div>
              </div>
              <div style={ui.stat}>
                <div style={{ ...ui.statValue, color: "#ff5c5c" }}>{data.fail_rate}%</div>
                <div style={ui.statLabel}>Fail rate</div>
              </div>
              <div style={ui.stat}>
                <div style={{ ...ui.statValue, fontSize: 20 }}>
                  {data.most_common_defect || "-"}
                </div>
                <div style={ui.statLabel}>Most common defect</div>
              </div>
            </section>

            <section style={ui.panel}>
              <div style={ui.panelHead}>
                <h3 style={ui.panelTitle}>Category quality report</h3>
                <button style={ui.buttonGhost} onClick={exportCategories} disabled={!cats.length}>
                  Download CSV
                </button>
              </div>
              <div style={ui.tableWrap}>
                <table style={ui.table}>
                  <thead>
                    <tr>
                      <th style={ui.th}>Category</th>
                      <th style={ui.th}>Total</th>
                      <th style={ui.th}>Pass</th>
                      <th style={ui.th}>Fail</th>
                      <th style={ui.th}>Fail rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cats.map((c) => (
                      <tr key={c.category}>
                        <td style={ui.td}>{c.category}</td>
                        <td style={ui.td}>{c.total}</td>
                        <td style={ui.td}>{c.pass}</td>
                        <td style={ui.td}>{c.fail}</td>
                        <td style={ui.td}>
                          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                            <div
                              style={{
                                width: 110,
                                height: 6,
                                background: "#232b36",
                                borderRadius: 4,
                              }}
                            >
                              <div
                                style={{
                                  width: Math.min(100, c.fail_rate) + "%",
                                  height: 6,
                                  background: "#ff5c5c",
                                  borderRadius: 4,
                                }}
                              />
                            </div>
                            <span>{c.fail_rate}%</span>
                          </div>
                        </td>
                      </tr>
                    ))}
                    {!cats.length && (
                      <tr>
                        <td style={ui.td} colSpan={5}>
                          No inspections yet. Run an inspection from the dashboard first.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>

            <section style={ui.panel}>
              <div style={ui.panelHead}>
                <h3 style={ui.panelTitle}>Top defect types</h3>
                <button style={ui.buttonGhost} onClick={exportTypes} disabled={!types.length}>
                  Download CSV
                </button>
              </div>
              <div style={ui.tableWrap}>
                <table style={ui.table}>
                  <thead>
                    <tr>
                      <th style={ui.th}>Defect type</th>
                      <th style={ui.th}>Count</th>
                      <th style={ui.th}>Share</th>
                    </tr>
                  </thead>
                  <tbody>
                    {types.map((t) => (
                      <tr key={t.type}>
                        <td style={ui.td}>{t.type}</td>
                        <td style={ui.td}>{t.count}</td>
                        <td style={ui.td}>{share(t.count)}%</td>
                      </tr>
                    ))}
                    {!types.length && (
                      <tr>
                        <td style={ui.td} colSpan={3}>
                          No defects logged yet.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>

            <section style={ui.panel}>
              <div style={ui.panelHead}>
                <h3 style={ui.panelTitle}>Severity breakdown</h3>
                <button style={ui.buttonGhost} onClick={exportSeverity} disabled={!sev.length}>
                  Download CSV
                </button>
              </div>
              <div style={ui.row}>
                {sev.map((s) => (
                  <span key={s.severity} style={badge(SEVERITY_COLORS[s.severity] || "#8a94a1")}>
                    {s.severity.toUpperCase()}: {s.count}
                  </span>
                ))}
                {!sev.length && <span style={{ color: "#8a94a1" }}>No defects logged yet.</span>}
              </div>
            </section>
          </>
        )}
      </div>
    </div>
  );
}
