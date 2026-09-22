import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Sidebar from "../components/Sidebar";
import { getToken, clearToken, getAnalyticsSummary } from "../lib/api";

const SEVERITY_COLORS = {
  critical: "#ff5c5c",
  high: "#f5a623",
  medium: "#e8d44d",
  low: "#3dd68c",
  unknown: "#8a94a1",
};

export default function Analytics() {
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
        const summary = await getAnalyticsSummary();
        setData(summary);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [router]);

  return (
    <div style={styles.shell}>
      <Sidebar />
      <div style={styles.page}>
        <header style={styles.header}>
          <div>
            <div style={styles.eyebrow}>VISIONINSPECT AI · ANALYTICS</div>
            <h1 style={styles.title}>Manufacturing Analytics</h1>
          </div>
        </header>

        {loading && <div style={styles.centerMsg}>Loading analytics…</div>}
        {error && <div style={styles.centerMsg}>Error: {error}</div>}

        {!loading && !error && data && (
          <main style={styles.main}>
            <section style={styles.statRow}>
              <StatCard
                label="Total Inspections"
                value={data.total_inspections}
                accent="var(--accent)"
              />
              <StatCard
                label="Pass Rate"
                value={`${data.pass_rate}%`}
                accent="#3dd68c"
              />
              <StatCard
                label="Fail Rate"
                value={`${data.fail_rate}%`}
                accent="#ff5c5c"
              />
              <StatCard
                label="Most Common Defect"
                value={data.most_common_defect || "—"}
                accent="#c084fc"
                small
              />
            </section>

            <section style={styles.panel}>
              <h2 style={styles.panelTitle}>Inspections over time</h2>
              {data.trend.length === 0 ? (
                <EmptyState text="Run some inspections to see trends here." />
              ) : (
                <TrendChart trend={data.trend} />
              )}
            </section>

            <div style={styles.twoCol}>
              <section style={styles.panel}>
                <h2 style={styles.panelTitle}>Severity breakdown</h2>
                {data.severity_breakdown.length === 0 ? (
                  <EmptyState text="No defects logged yet." />
                ) : (
                  <BarList
                    items={data.severity_breakdown.map((s) => ({
                      label: s.severity,
                      value: s.count,
                      color: SEVERITY_COLORS[s.severity] || "var(--text-muted)",
                    }))}
                  />
                )}
              </section>

              <section style={styles.panel}>
                <h2 style={styles.panelTitle}>Top defect types</h2>
                {data.defect_type_breakdown.length === 0 ? (
                  <EmptyState text="No defects logged yet." />
                ) : (
                  <BarList
                    items={data.defect_type_breakdown.map((d) => ({
                      label: d.type,
                      value: d.count,
                      color: "var(--accent)",
                    }))}
                  />
                )}
              </section>
            </div>

            <section style={styles.panel}>
              <h2 style={styles.panelTitle}>Production quality by category</h2>
              {data.category_breakdown.length === 0 ? (
                <EmptyState text="No inspections logged yet." />
              ) : (
                <div style={styles.table}>
                  <div style={styles.tableHeader}>
                    <span>Category</span>
                    <span>Total</span>
                    <span>Pass</span>
                    <span>Fail</span>
                    <span>Fail rate</span>
                  </div>
                  {data.category_breakdown.map((c) => (
                    <div key={c.category} style={styles.tableRow}>
                      <span>{c.category}</span>
                      <span style={styles.mono}>{c.total}</span>
                      <span style={{ ...styles.mono, color: "var(--ok)" }}>
                        {c.pass}
                      </span>
                      <span style={{ ...styles.mono, color: "var(--danger)" }}>
                        {c.fail}
                      </span>
                      <span style={styles.mono}>{c.fail_rate}%</span>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </main>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value, accent, small }) {
  return (
    <div style={styles.statCard}>
      <div style={{ ...styles.statAccent, background: accent }} />
      <div style={small ? styles.statValueSmall : styles.statValue}>{value}</div>
      <div style={styles.statLabel}>{label}</div>
    </div>
  );
}

function EmptyState({ text }) {
  return <div style={styles.emptyState}>{text}</div>;
}

function BarList({ items }) {
  const max = Math.max(...items.map((i) => i.value), 1);
  return (
    <div style={styles.barList}>
      {items.map((item) => (
        <div key={item.label} style={styles.barRow}>
          <div style={styles.barLabelRow}>
            <span style={styles.barLabel}>{item.label}</span>
            <span style={styles.mono}>{item.value}</span>
          </div>
          <div style={styles.barTrack}>
            <div
              style={{
                ...styles.barFill,
                width: `${(item.value / max) * 100}%`,
                background: item.color,
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function TrendChart({ trend }) {
  const width = 640;
  const height = 180;
  const padding = 24;
  const maxTotal = Math.max(...trend.map((t) => t.total), 1);

  const points = (key) =>
    trend
      .map((t, i) => {
        const x =
          trend.length === 1
            ? width / 2
            : padding + (i / (trend.length - 1)) * (width - padding * 2);
        const y =
          height - padding - (t[key] / maxTotal) * (height - padding * 2);
        return `${x},${y}`;
      })
      .join(" ");

  return (
    <div style={{ overflowX: "auto" }}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        style={{ width: "100%", maxWidth: width, height }}
      >
        <line
          x1={padding}
          y1={height - padding}
          x2={width - padding}
          y2={height - padding}
          stroke="var(--border)"
          strokeWidth="1"
        />
        <polyline
          points={points("total")}
          fill="none"
          stroke="var(--accent)"
          strokeWidth="2"
        />
        <polyline
          points={points("defective")}
          fill="none"
          stroke="var(--danger)"
          strokeWidth="2"
        />
        {trend.map((t, i) => {
          const x =
            trend.length === 1
              ? width / 2
              : padding + (i / (trend.length - 1)) * (width - padding * 2);
          const yTotal =
            height - padding - (t.total / maxTotal) * (height - padding * 2);
          const yDef =
            height - padding - (t.defective / maxTotal) * (height - padding * 2);
          return (
            <g key={t.date}>
              <circle cx={x} cy={yTotal} r="3" fill="var(--accent)" />
              <circle cx={x} cy={yDef} r="3" fill="var(--danger)" />
            </g>
          );
        })}
      </svg>
      <div style={styles.legendRow}>
        <span style={styles.legendItem}>
          <span style={{ ...styles.legendDot, background: "var(--accent)" }} />
          Total inspections
        </span>
        <span style={styles.legendItem}>
          <span style={{ ...styles.legendDot, background: "var(--danger)" }} />
          Defective
        </span>
      </div>
    </div>
  );
}

const styles = {
  shell: {
    display: "flex",
    minHeight: "100vh",
  },
  page: {
    flex: 1,
    minHeight: "100vh",
    padding: "0 0 48px",
  },
  header: {
    padding: "24px 32px",
    borderBottom: "1px solid var(--border)",
  },
  eyebrow: {
    fontFamily: "var(--font-mono)",
    fontSize: 11,
    letterSpacing: "0.14em",
    color: "var(--accent)",
  },
  title: {
    fontFamily: "var(--font-display)",
    fontSize: 24,
    margin: "4px 0 0",
  },
  centerMsg: {
    textAlign: "center",
    color: "var(--text-muted)",
    padding: "80px 0",
  },
  main: {
    maxWidth: 1000,
    margin: "0 auto",
    padding: "32px",
    display: "flex",
    flexDirection: "column",
    gap: 20,
  },
  statRow: {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gap: 16,
  },
  statCard: {
    position: "relative",
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: 12,
    padding: "18px 20px",
    overflow: "hidden",
  },
  statAccent: {
    position: "absolute",
    top: 0,
    left: 0,
    width: "100%",
    height: 3,
  },
  statValue: {
    fontFamily: "var(--font-display)",
    fontSize: 28,
    fontWeight: 700,
  },
  statValueSmall: {
    fontFamily: "var(--font-display)",
    fontSize: 18,
    fontWeight: 700,
    textTransform: "capitalize",
  },
  statLabel: {
    fontSize: 12,
    color: "var(--text-muted)",
    marginTop: 4,
  },
  panel: {
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: 12,
    padding: "20px 24px",
  },
  panelTitle: {
    fontFamily: "var(--font-display)",
    fontSize: 16,
    margin: "0 0 16px",
  },
  twoCol: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 20,
  },
  emptyState: {
    color: "var(--text-muted)",
    fontSize: 13,
    padding: "20px",
    textAlign: "center",
    border: "1px dashed var(--border)",
    borderRadius: 8,
  },
  barList: {
    display: "flex",
    flexDirection: "column",
    gap: 12,
  },
  barRow: {
    display: "flex",
    flexDirection: "column",
    gap: 5,
  },
  barLabelRow: {
    display: "flex",
    justifyContent: "space-between",
    fontSize: 12,
    textTransform: "capitalize",
  },
  barLabel: {
    color: "var(--text-muted)",
  },
  barTrack: {
    height: 8,
    borderRadius: 4,
    background: "var(--surface-2)",
    overflow: "hidden",
  },
  barFill: {
    height: "100%",
    borderRadius: 4,
    transition: "width 0.4s ease",
  },
  table: {
    display: "flex",
    flexDirection: "column",
    gap: 2,
  },
  tableHeader: {
    display: "grid",
    gridTemplateColumns: "1.5fr 0.8fr 0.8fr 0.8fr 0.8fr",
    fontSize: 11,
    color: "var(--text-muted)",
    textTransform: "uppercase",
    letterSpacing: "0.06em",
    padding: "8px 10px",
  },
  tableRow: {
    display: "grid",
    gridTemplateColumns: "1.5fr 0.8fr 0.8fr 0.8fr 0.8fr",
    alignItems: "center",
    padding: "10px",
    background: "var(--surface-2)",
    borderRadius: 8,
    fontSize: 13,
    textTransform: "capitalize",
  },
  mono: {
    fontFamily: "var(--font-mono)",
    color: "var(--text)",
  },
  legendRow: {
    display: "flex",
    gap: 20,
    marginTop: 8,
    justifyContent: "center",
  },
  legendItem: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    fontSize: 12,
    color: "var(--text-muted)",
  },
  legendDot: {
    width: 8,
    height: 8,
    borderRadius: "50%",
  },
};
