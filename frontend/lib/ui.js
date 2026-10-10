export const ui = {
  shell: { display: "flex", minHeight: "100vh" },
  page: { flex: 1, minWidth: 0, padding: "32px 40px 60px" },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-end",
    gap: 16,
    flexWrap: "wrap",
    marginBottom: 24,
  },
  eyebrow: {
    fontFamily: "monospace",
    fontSize: 12,
    letterSpacing: 2,
    color: "#f5a623",
    marginBottom: 8,
  },
  title: { fontSize: 30, fontWeight: 700, margin: 0, color: "#ffffff" },
  subtitle: { color: "#8a94a1", fontSize: 14, marginTop: 6 },
  panel: {
    background: "#161c24",
    border: "1px solid #232b36",
    borderRadius: 14,
    padding: 20,
    marginBottom: 20,
  },
  panelHead: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 12,
    flexWrap: "wrap",
    marginBottom: 14,
  },
  panelTitle: {
    fontSize: 13,
    letterSpacing: 1,
    textTransform: "uppercase",
    color: "#8a94a1",
    margin: 0,
  },
  row: { display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" },
  select: {
    background: "#0e1319",
    color: "#e6eaf0",
    border: "1px solid #2a3340",
    borderRadius: 8,
    padding: "9px 12px",
    fontSize: 14,
  },
  button: {
    background: "#f5a623",
    color: "#111111",
    border: "none",
    borderRadius: 8,
    padding: "10px 16px",
    fontSize: 14,
    fontWeight: 700,
    cursor: "pointer",
  },
  buttonGhost: {
    background: "transparent",
    color: "#e6eaf0",
    border: "1px solid #2a3340",
    borderRadius: 8,
    padding: "9px 14px",
    fontSize: 14,
    cursor: "pointer",
  },
  tableWrap: { overflowX: "auto" },
  table: { width: "100%", borderCollapse: "collapse", fontSize: 14, color: "#e6eaf0" },
  th: {
    textAlign: "left",
    padding: "10px 12px",
    color: "#8a94a1",
    fontWeight: 500,
    fontSize: 12,
    letterSpacing: 1,
    textTransform: "uppercase",
    borderBottom: "1px solid #232b36",
    whiteSpace: "nowrap",
  },
  td: { padding: "11px 12px", borderBottom: "1px solid #1c232d" },
  msg: { color: "#8a94a1", padding: "40px 0", textAlign: "center" },
  statGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))",
    gap: 14,
    marginBottom: 20,
  },
  stat: {
    background: "#161c24",
    border: "1px solid #232b36",
    borderRadius: 14,
    padding: "16px 18px",
  },
  statValue: { fontSize: 26, fontWeight: 700, color: "#ffffff", wordBreak: "break-word" },
  statLabel: { fontSize: 13, color: "#8a94a1", marginTop: 4 },
  pager: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 12,
    marginTop: 14,
    color: "#8a94a1",
    fontSize: 13,
  },
  infoRow: {
    display: "flex",
    justifyContent: "space-between",
    gap: 16,
    padding: "12px 0",
    borderBottom: "1px solid #1c232d",
    color: "#e6eaf0",
    fontSize: 15,
  },
  infoLabel: { color: "#8a94a1" },
};

export function badge(color) {
  return {
    display: "inline-block",
    padding: "3px 10px",
    borderRadius: 999,
    border: "1px solid " + color,
    color: color,
    fontSize: 12,
    fontWeight: 600,
    letterSpacing: 0.5,
  };
}

function escapeCell(v) {
  if (v === null || v === undefined) return "";
  const s = String(v);
  return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
}

export function downloadCsv(filename, headers, rows) {
  const lines = [headers.map(escapeCell).join(",")];
  rows.forEach((r) => lines.push(r.map(escapeCell).join(",")));
  const blob = new Blob(["\uFEFF" + lines.join("\r\n")], {
    type: "text/csv;charset=utf-8;",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}