import Link from "next/link";
import { useRouter } from "next/router";

const NAV_ITEMS = [
  { key: "dashboard", label: "Dashboard", href: "/dashboard", icon: "▣", enabled: true },
  { key: "inspections", label: "Inspections", href: "#", icon: "◎", enabled: false },
  { key: "analytics", label: "Analytics", href: "/analytics", icon: "▤", enabled: true },
  { key: "reports", label: "Reports", href: "#", icon: "▧", enabled: false },
  { key: "settings", label: "Settings", href: "#", icon: "⚙", enabled: false },
];

export default function Sidebar() {
  const router = useRouter();

  return (
    <aside style={styles.sidebar}>
      <div>
        <div style={styles.brand}>
          <span style={styles.brandDot} />
          <div>
            <div style={styles.brandName}>VisionInspect</div>
            <div style={styles.brandSub}>AI</div>
          </div>
        </div>

        <nav style={styles.nav}>
          {NAV_ITEMS.map((item) => {
            const active = router.pathname === item.href;
            const content = (
              <>
                <span style={styles.navIcon}>{item.icon}</span>
                <span>{item.label}</span>
                {!item.enabled && <span style={styles.soonTag}>SOON</span>}
              </>
            );
            return item.enabled ? (
              <Link
                key={item.key}
                href={item.href}
                style={{
                  ...styles.navItem,
                  ...(active ? styles.navItemActive : {}),
                }}
              >
                {content}
              </Link>
            ) : (
              <div key={item.key} style={{ ...styles.navItem, ...styles.navItemDisabled }}>
                {content}
              </div>
            );
          })}
        </nav>
      </div>

      <div style={styles.moduleList}>
        <div style={styles.moduleHeading}>Pipeline modules</div>
        {[
          "User Management",
          "Image Acquisition",
          "Image Processing",
          "Defect Detection",
          "Defect Classification",
          "Quality Control",
          "Analytics Dashboard",
        ].map((m, i) => (
          <div key={m} style={styles.moduleItem}>
            <span
              style={{
                ...styles.moduleDot,
                background: i < 7 ? "var(--ok)" : "var(--border)",
              }}
            />
            {m}
          </div>
        ))}
      </div>
    </aside>
  );
}

const styles = {
  sidebar: {
    width: 216,
    flexShrink: 0,
    minHeight: "100vh",
    borderRight: "1px solid var(--border)",
    background: "var(--surface)",
    padding: "20px 14px",
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
    position: "sticky",
    top: 0,
  },
  brand: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    padding: "0 8px",
    marginBottom: 28,
  },
  brandDot: {
    width: 10,
    height: 10,
    borderRadius: 3,
    background: "var(--accent)",
    boxShadow: "0 0 10px var(--accent)",
  },
  brandName: {
    fontFamily: "var(--font-display)",
    fontSize: 14,
    fontWeight: 700,
    lineHeight: 1.1,
  },
  brandSub: {
    fontFamily: "var(--font-mono)",
    fontSize: 9,
    color: "var(--accent)",
    letterSpacing: "0.14em",
  },
  nav: {
    display: "flex",
    flexDirection: "column",
    gap: 2,
  },
  navItem: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    padding: "9px 10px",
    borderRadius: 8,
    fontSize: 13,
    color: "var(--text-muted)",
    textDecoration: "none",
    border: "1px solid transparent",
  },
  navItemActive: {
    background: "var(--surface-2)",
    borderColor: "var(--border)",
    color: "var(--text)",
  },
  navItemDisabled: {
    opacity: 0.45,
    cursor: "default",
  },
  navIcon: {
    fontSize: 13,
    width: 16,
    textAlign: "center",
  },
  soonTag: {
    marginLeft: "auto",
    fontFamily: "var(--font-mono)",
    fontSize: 8,
    letterSpacing: "0.06em",
    color: "var(--text-muted)",
    border: "1px solid var(--border)",
    borderRadius: 4,
    padding: "1px 4px",
  },
  moduleList: {
    borderTop: "1px solid var(--border)",
    paddingTop: 16,
  },
  moduleHeading: {
    fontFamily: "var(--font-mono)",
    fontSize: 9,
    letterSpacing: "0.1em",
    color: "var(--text-muted)",
    textTransform: "uppercase",
    padding: "0 10px 10px",
  },
  moduleItem: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: "6px 10px",
    fontSize: 11,
    color: "var(--text-muted)",
  },
  moduleDot: {
    width: 6,
    height: 6,
    borderRadius: "50%",
    flexShrink: 0,
  },
};
