import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Link from "next/link";
import { getToken, getImageDetail, getImageFileUrl, runInspection } from "../../lib/api";

const SEVERITY_COLORS = {
  critical: "#ff5c5c",
  high: "#f5a623",
  medium: "#e8d44d",
  low: "#3dd68c",
};

function severityColor(level) {
  return SEVERITY_COLORS[(level || "").toLowerCase()] || "var(--text-muted)";
}

export default function InspectDetail() {
  const router = useRouter();
  const { id } = router.query;
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [inspecting, setInspecting] = useState(false);
  const [inspectError, setInspectError] = useState("");
  const [quality, setQuality] = useState(null);

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    if (!id) return;

    (async () => {
      setLoading(true);
      try {
        const detail = await getImageDetail(id);
        setData(detail);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [id, router]);

  const hasInspection = Boolean(data?.inspection);
  const result = data?.inspection?.result; // "normal" | "defective"
  const isFail = result === "defective";
  const defects = data?.defects || [];

  async function handleRunInspection() {
    setInspectError("");
    setInspecting(true);
    try {
      const response = await runInspection(id);
      setQuality(response.quality || null);
      const detail = await getImageDetail(id);
      setData(detail);
    } catch (err) {
      setInspectError(err.message);
    } finally {
      setInspecting(false);
    }
  }

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <Link href="/dashboard" style={styles.backLink}>
          ← Back to dashboard
        </Link>
        <div style={styles.eyebrow}>VISIONINSPECT AI · UNIT #{id}</div>
      </header>

      {loading && <div style={styles.centerMsg}>Loading inspection record…</div>}
      {error && <div style={styles.centerMsg}>Error: {error}</div>}

      {!loading && !error && data && (
        <main style={styles.main}>
          {/* IMAGE VIEWER */}
          <section style={styles.viewerCard}>
            <div style={styles.viewer}>
              <img
                src={getImageFileUrl(data.image_id)}
                alt={`Unit ${data.image_id}`}
                style={styles.image}
              />

              {/* targeting reticle corners */}
              <span style={{ ...styles.corner, ...styles.cornerTL }} />
              <span style={{ ...styles.corner, ...styles.cornerTR }} />
              <span style={{ ...styles.corner, ...styles.cornerBL }} />
              <span style={{ ...styles.corner, ...styles.cornerBR }} />

              {!hasInspection && (
                <>
                  <div style={styles.scanSweep} />
                  <div style={styles.scanBadge}>ANALYZING…</div>
                </>
              )}

              {hasInspection && (
                <div
                  style={{
                    ...styles.resultBadge,
                    borderColor: isFail ? "var(--danger)" : "var(--ok)",
                    color: isFail ? "var(--danger)" : "var(--ok)",
                    boxShadow: `0 0 20px ${isFail ? "rgba(255,92,92,0.3)" : "rgba(61,214,140,0.3)"}`,
                  }}
                >
                  {isFail ? "FAIL" : "PASS"}
                </div>
              )}
            </div>

            <div style={styles.viewerMeta}>
              <MetaItem label="Category" value={data.category || "—"} />
              <MetaItem label="Source" value={data.image_source} />
              <MetaItem label="Split" value={data.image_type} />
              <MetaItem
                label="Logged"
                value={new Date(data.created_at).toLocaleString()}
              />
            </div>
          </section>

          {/* RESULT PANEL */}
          <section style={styles.resultPanel}>
            {hasInspection ? (
              <>
                <div style={styles.gaugeRow}>
                  <SeverityGauge
                    score={Number(data.inspection.confidence_score) || 0}
                  />
                  <div>
                    <div style={styles.panelTitle}>Overall Result</div>
                    <div
                      style={{
                        ...styles.bigResult,
                        color: isFail ? "var(--danger)" : "var(--ok)",
                      }}
                    >
                      {isFail ? "DEFECTIVE" : "NORMAL"}
                    </div>
                    <div style={styles.confidenceText}>
                      Model confidence:{" "}
                      <span style={styles.mono}>
                        {data.inspection.confidence_score ?? "—"}%
                      </span>
                    </div>
                  </div>
                </div>

                <div style={styles.divider} />

                <div style={styles.panelTitle}>
                  Detected defects{" "}
                  <span style={styles.countBadge}>{defects.length}</span>
                </div>

                {defects.length === 0 ? (
                  <div style={styles.emptyLog}>No defects logged for this unit.</div>
                ) : (
                  <div style={styles.defectLog}>
                    {defects.map((d, i) => (
                      <div key={d.defect_id} style={styles.defectRow}>
                        <span style={styles.mono}>
                          {String(i + 1).padStart(2, "0")}
                        </span>
                        <span>{d.defect_type}</span>
                        <span
                          style={{
                            ...styles.severityPill,
                            color: severityColor(d.severity),
                            borderColor: severityColor(d.severity),
                          }}
                        >
                          {(d.severity || "unknown").toUpperCase()}
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {quality && (
                  <>
                    <div style={styles.divider} />
                    <div style={styles.panelTitle}>Image quality report</div>
                    <div style={styles.qualityRow}>
                      <QualityStat label="Sharpness" value={quality.sharpness} />
                      <QualityStat label="Brightness" value={quality.brightness} />
                      <span
                        style={{
                          ...styles.severityPill,
                          color: quality.is_blurry ? "var(--danger)" : "var(--ok)",
                          borderColor: quality.is_blurry ? "var(--danger)" : "var(--ok)",
                        }}
                      >
                        {quality.is_blurry ? "BLURRY" : "SHARP"}
                      </span>
                    </div>
                  </>
                )}
              </>
            ) : (
              <div style={styles.pendingState}>
                <div style={styles.pendingPulse} />
                <div style={styles.panelTitle}>Awaiting AI analysis</div>
                <p style={styles.pendingText}>
                  This unit has been logged but not yet run through the defect
                  detection model. Run the inspection to get a result.
                </p>
                {inspectError && <div style={styles.error}>{inspectError}</div>}
                <button
                  onClick={handleRunInspection}
                  disabled={inspecting}
                  style={styles.runButton}
                >
                  {inspecting ? "Analyzing…" : "Run inspection"}
                </button>
              </div>
            )}
          </section>
        </main>
      )}
    </div>
  );
}

function MetaItem({ label, value }) {
  return (
    <div style={styles.metaItem}>
      <div style={styles.metaLabel}>{label}</div>
      <div style={styles.metaValue}>{value}</div>
    </div>
  );
}

function QualityStat({ label, value }) {
  return (
    <div style={styles.qualityStat}>
      <span style={styles.qualityValue}>{value}</span>
      <span style={styles.qualityLabel}>{label}</span>
    </div>
  );
}

function SeverityGauge({ score }) {
  const clamped = Math.max(0, Math.min(100, score));
  const radius = 42;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (clamped / 100) * circumference;
  const color =
    clamped >= 80 ? "#ff5c5c" : clamped >= 60 ? "#f5a623" : clamped >= 40 ? "#e8d44d" : "#3dd68c";

  return (
    <svg width="104" height="104" viewBox="0 0 104 104">
      <circle
        cx="52"
        cy="52"
        r={radius}
        fill="none"
        stroke="var(--border)"
        strokeWidth="8"
      />
      <circle
        cx="52"
        cy="52"
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth="8"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        strokeLinecap="round"
        transform="rotate(-90 52 52)"
        style={{ transition: "stroke-dashoffset 0.6s ease" }}
      />
      <text
        x="52"
        y="48"
        textAnchor="middle"
        fill="var(--text)"
        fontSize="22"
        fontFamily="var(--font-mono)"
        fontWeight="600"
      >
        {clamped}
      </text>
      <text
        x="52"
        y="66"
        textAnchor="middle"
        fill="var(--text-muted)"
        fontSize="9"
        fontFamily="var(--font-mono)"
        letterSpacing="1"
      >
        CONF %
      </text>
    </svg>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    padding: "24px 32px 64px",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 28,
  },
  backLink: {
    color: "var(--text-muted)",
    textDecoration: "none",
    fontSize: 13,
  },
  eyebrow: {
    fontFamily: "var(--font-mono)",
    fontSize: 11,
    letterSpacing: "0.14em",
    color: "var(--accent)",
  },
  centerMsg: {
    textAlign: "center",
    color: "var(--text-muted)",
    padding: "80px 0",
  },
  main: {
    maxWidth: 1000,
    margin: "0 auto",
    display: "grid",
    gridTemplateColumns: "1.2fr 1fr",
    gap: 24,
  },
  viewerCard: {
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: 12,
    padding: 16,
  },
  viewer: {
    position: "relative",
    borderRadius: 8,
    overflow: "hidden",
    background: "#0b0d10",
    aspectRatio: "1 / 1",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  image: {
    width: "100%",
    height: "100%",
    objectFit: "contain",
  },
  corner: {
    position: "absolute",
    width: 22,
    height: 22,
    borderColor: "var(--accent)",
    opacity: 0.85,
  },
  cornerTL: { top: 10, left: 10, borderTop: "2px solid", borderLeft: "2px solid" },
  cornerTR: { top: 10, right: 10, borderTop: "2px solid", borderRight: "2px solid" },
  cornerBL: { bottom: 10, left: 10, borderBottom: "2px solid", borderLeft: "2px solid" },
  cornerBR: { bottom: 10, right: 10, borderBottom: "2px solid", borderRight: "2px solid" },
  scanSweep: {
    position: "absolute",
    left: 0,
    top: 0,
    width: "100%",
    height: "3px",
    background:
      "linear-gradient(90deg, transparent, var(--accent), transparent)",
    boxShadow: "0 0 16px var(--accent)",
    animation: "scanY 2.6s ease-in-out infinite",
  },
  scanBadge: {
    position: "absolute",
    bottom: 16,
    left: "50%",
    transform: "translateX(-50%)",
    fontFamily: "var(--font-mono)",
    fontSize: 11,
    letterSpacing: "0.12em",
    color: "var(--accent)",
    background: "rgba(0,0,0,0.5)",
    padding: "6px 12px",
    borderRadius: 6,
    border: "1px solid var(--accent-dim)",
  },
  resultBadge: {
    position: "absolute",
    top: 16,
    right: 16,
    fontFamily: "var(--font-mono)",
    fontWeight: 700,
    fontSize: 13,
    letterSpacing: "0.1em",
    padding: "6px 14px",
    borderRadius: 6,
    border: "1px solid",
    background: "rgba(0,0,0,0.5)",
  },
  viewerMeta: {
    display: "grid",
    gridTemplateColumns: "repeat(2, 1fr)",
    gap: 12,
    marginTop: 16,
  },
  metaItem: {
    background: "var(--surface-2)",
    border: "1px solid var(--border)",
    borderRadius: 8,
    padding: "10px 12px",
  },
  metaLabel: {
    fontSize: 10,
    color: "var(--text-muted)",
    textTransform: "uppercase",
    letterSpacing: "0.08em",
    marginBottom: 4,
  },
  metaValue: {
    fontSize: 13,
    fontFamily: "var(--font-mono)",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },
  resultPanel: {
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: 12,
    padding: 24,
  },
  gaugeRow: {
    display: "flex",
    alignItems: "center",
    gap: 20,
  },
  panelTitle: {
    fontFamily: "var(--font-display)",
    fontSize: 14,
    color: "var(--text-muted)",
    display: "flex",
    alignItems: "center",
    gap: 8,
    marginBottom: 6,
  },
  bigResult: {
    fontFamily: "var(--font-display)",
    fontSize: 28,
    fontWeight: 700,
    letterSpacing: "0.02em",
  },
  confidenceText: {
    fontSize: 13,
    color: "var(--text-muted)",
    marginTop: 4,
  },
  mono: {
    fontFamily: "var(--font-mono)",
    color: "var(--text)",
  },
  divider: {
    height: 1,
    background: "var(--border)",
    margin: "22px 0",
  },
  countBadge: {
    fontFamily: "var(--font-mono)",
    fontSize: 11,
    color: "var(--accent)",
    border: "1px solid var(--accent-dim)",
    borderRadius: 6,
    padding: "1px 8px",
  },
  emptyLog: {
    color: "var(--text-muted)",
    fontSize: 13,
    padding: "16px",
    textAlign: "center",
    border: "1px dashed var(--border)",
    borderRadius: 8,
  },
  defectLog: {
    display: "flex",
    flexDirection: "column",
    gap: 6,
  },
  defectRow: {
    display: "grid",
    gridTemplateColumns: "24px 1fr auto",
    alignItems: "center",
    gap: 10,
    background: "var(--surface-2)",
    borderRadius: 8,
    padding: "10px 12px",
    fontSize: 13,
  },
  severityPill: {
    fontFamily: "var(--font-mono)",
    fontSize: 10,
    letterSpacing: "0.06em",
    border: "1px solid",
    borderRadius: 20,
    padding: "3px 10px",
  },
  qualityRow: {
    display: "flex",
    alignItems: "center",
    gap: 20,
  },
  qualityStat: {
    display: "flex",
    flexDirection: "column",
    gap: 2,
  },
  qualityValue: {
    fontFamily: "var(--font-mono)",
    fontSize: 16,
    fontWeight: 600,
  },
  qualityLabel: {
    fontSize: 10,
    color: "var(--text-muted)",
    textTransform: "uppercase",
    letterSpacing: "0.06em",
  },
  pendingState: {
    textAlign: "center",
    padding: "24px 8px",
  },
  pendingPulse: {
    width: 14,
    height: 14,
    borderRadius: "50%",
    background: "var(--accent)",
    margin: "0 auto 20px",
    boxShadow: "0 0 0 0 rgba(245,166,35,0.6)",
    animation: "pulse 1.8s ease-out infinite",
  },
  pendingText: {
    color: "var(--text-muted)",
    fontSize: 13,
    lineHeight: 1.6,
    maxWidth: 320,
    margin: "8px auto 0",
  },
  runButton: {
    marginTop: 20,
    background: "var(--accent)",
    color: "#14161a",
    border: "none",
    borderRadius: 8,
    padding: "12px 24px",
    fontWeight: 600,
    fontSize: 14,
    cursor: "pointer",
  },
  error: {
    background: "rgba(255,92,92,0.1)",
    border: "1px solid var(--danger)",
    color: "var(--danger)",
    padding: "10px 12px",
    borderRadius: 8,
    fontSize: 13,
    marginTop: 16,
    textAlign: "left",
  },
};
