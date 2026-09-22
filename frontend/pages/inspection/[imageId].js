import { useRouter } from "next/router";
import Link from "next/link";

// TODO: replace with a real API call to GET /inspections/{id} once the
// defect-detection backend (Milestone 3) is built. For now this page
// renders with sample data so the UI/UX is ready ahead of the API.
const MOCK_RESULT = {
  image_path: "dataset_images/bottle/test/broken_large/000.png",
  category: "bottle",
  result: "FAIL",
  severity_score: 88,
  severity_level: "Critical",
  defects: [
    { id: 1, type: "Surface Crack", severity: "Critical", confidence: 92 },
    { id: 2, type: "Broken Edge", severity: "High", confidence: 81 },
  ],
  breakdown: {
    size: { score: 85, weight: 30 },
    location: { score: 90, weight: 25 },
    defect_type: { score: 95, weight: 25 },
    confidence: { score: 92, weight: 20 },
  },
};

const SEVERITY_COLOR = {
  Critical: "var(--danger)",
  High: "#ff9d4d",
  Medium: "var(--accent)",
  Low: "var(--ok)",
};

export default function InspectionResult() {
  const router = useRouter();
  const { imageId } = router.query;
  const data = MOCK_RESULT;

  const isFail = data.result === "FAIL";

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <div>
          <div style={styles.eyebrow}>VISIONINSPECT AI</div>
          <h1 style={styles.title}>Inspection Result {imageId ? `— #${imageId}` : ""}</h1>
        </div>
        <Link href="/dashboard" style={styles.backLink}>
          ← Back to dashboard
        </Link>
      </header>

      <main style={styles.main}>
        <section style={styles.imageCard}>
          <div style={styles.imagePlaceholder}>
            <span style={styles.mono}>{data.image_path}</span>
          </div>
          <div style={styles.categoryTag}>{data.category}</div>
        </section>

        <section style={styles.resultCard}>
          <div style={styles.resultHeader}>
            <span style={styles.cardLabel}>Overall Result</span>
            <span
              style={{
                ...styles.resultBadge,
                background: isFail ? "rgba(255,92,92,0.12)" : "rgba(61,214,140,0.12)",
                color: isFail ? "var(--danger)" : "var(--ok)",
                border: `1px solid ${isFail ? "var(--danger)" : "var(--ok)"}`,
              }}
            >
              {data.result}
            </span>
          </div>
          <div style={styles.severityRow}>
            <span style={styles.mono}>Severity Score</span>
            <span style={{ ...styles.mono, color: "var(--accent)", fontSize: 18 }}>
              {data.severity_score} / 100 — {data.severity_level}
            </span>
          </div>

          <h3 style={styles.subheading}>Detected Defects</h3>
          <div style={styles.defectTable}>
            <div style={styles.defectHeaderRow}>
              <span>#</span>
              <span>Type</span>
              <span>Severity</span>
              <span>Confidence</span>
            </div>
            {data.defects.map((d) => (
              <div key={d.id} style={styles.defectRow}>
                <span style={styles.mono}>{d.id}</span>
                <span>{d.type}</span>
                <span style={{ color: SEVERITY_COLOR[d.severity] || "var(--text)" }}>
                  {d.severity}
                </span>
                <span style={styles.mono}>{d.confidence}%</span>
              </div>
            ))}
          </div>

          <h3 style={styles.subheading}>Severity Score Breakdown</h3>
          <div style={styles.breakdown}>
            {Object.entries(data.breakdown).map(([key, val]) => (
              <div key={key} style={styles.breakdownRow}>
                <span style={styles.breakdownLabel}>
                  {key.replace("_", " ")} ({val.weight}%)
                </span>
                <div style={styles.barTrack}>
                  <div
                    style={{
                      ...styles.barFill,
                      width: `${val.score}%`,
                    }}
                  />
                </div>
                <span style={styles.mono}>{val.score}</span>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}

const styles = {
  page: { minHeight: "100vh", padding: "0 0 48px" },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
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
    fontSize: 22,
    margin: "4px 0 0",
  },
  backLink: {
    color: "var(--text-muted)",
    textDecoration: "none",
    fontSize: 13,
  },
  main: {
    maxWidth: 900,
    margin: "0 auto",
    padding: "32px",
    display: "grid",
    gridTemplateColumns: "1fr 1.3fr",
    gap: 24,
  },
  imageCard: {
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: 12,
    padding: "16px",
    height: "fit-content",
  },
  imagePlaceholder: {
    aspectRatio: "1 / 1",
    background: "var(--surface-2)",
    border: "1px dashed var(--border)",
    borderRadius: 8,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: 16,
    textAlign: "center",
  },
  categoryTag: {
    marginTop: 12,
    display: "inline-block",
    fontFamily: "var(--font-mono)",
    fontSize: 11,
    color: "var(--text-muted)",
    border: "1px solid var(--border)",
    borderRadius: 6,
    padding: "3px 8px",
    textTransform: "uppercase",
  },
  resultCard: {
    background: "var(--surface)",
    border: "1px solid var(--border)",
    borderRadius: 12,
    padding: "24px",
  },
  resultHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  cardLabel: {
    fontSize: 13,
    color: "var(--text-muted)",
  },
  resultBadge: {
    fontFamily: "var(--font-display)",
    fontWeight: 700,
    fontSize: 14,
    padding: "6px 16px",
    borderRadius: 8,
  },
  severityRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "baseline",
    paddingBottom: 20,
    borderBottom: "1px solid var(--border)",
    marginBottom: 20,
  },
  subheading: {
    fontFamily: "var(--font-display)",
    fontSize: 15,
    margin: "0 0 12px",
  },
  defectTable: {
    display: "flex",
    flexDirection: "column",
    gap: 2,
    marginBottom: 24,
  },
  defectHeaderRow: {
    display: "grid",
    gridTemplateColumns: "30px 1fr 90px 90px",
    fontSize: 11,
    color: "var(--text-muted)",
    textTransform: "uppercase",
    letterSpacing: "0.06em",
    padding: "6px 10px",
  },
  defectRow: {
    display: "grid",
    gridTemplateColumns: "30px 1fr 90px 90px",
    alignItems: "center",
    padding: "10px",
    background: "var(--surface-2)",
    borderRadius: 8,
    fontSize: 13,
  },
  breakdown: {
    display: "flex",
    flexDirection: "column",
    gap: 10,
  },
  breakdownRow: {
    display: "grid",
    gridTemplateColumns: "140px 1fr 32px",
    alignItems: "center",
    gap: 10,
    fontSize: 12,
  },
  breakdownLabel: {
    color: "var(--text-muted)",
    textTransform: "capitalize",
  },
  barTrack: {
    height: 8,
    background: "var(--surface-2)",
    borderRadius: 4,
    overflow: "hidden",
  },
  barFill: {
    height: "100%",
    background: "var(--accent)",
    borderRadius: 4,
  },
  mono: {
    fontFamily: "var(--font-mono)",
    fontSize: 12,
    color: "var(--text-muted)",
  },
};
