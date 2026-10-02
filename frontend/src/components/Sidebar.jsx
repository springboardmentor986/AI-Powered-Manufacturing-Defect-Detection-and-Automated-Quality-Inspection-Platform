import { useLocation, useNavigate } from "react-router-dom";

const NAV_ITEMS = [
  ["⌂", "Dashboard", "/dashboard"],
  ["▣", "New Inspection", "/inspection", "quality_engineer"],
  ["◉", "Camera & Batch", "/camera-batch", "quality_engineer"],
  ["☷", "Inspection History", "/history"],
  ["⌁", "Analytics", "/analytics"],
  ["▤", "Reports", "/reports"],
  ["⚙", "Settings", "/settings"],
];

function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();

  const role = localStorage.getItem("role");

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("role");
    navigate("/login", { replace: true });
  };

  const visibleItems = NAV_ITEMS.filter(
    ([, , , requiredRole]) =>
      !requiredRole || requiredRole === role
  );

  return (
    <aside className="dashboard-sidebar">

      <div className="sidebar-brand">
        <div className="sidebar-logo">V</div>

        <div>
          <div className="sidebar-brand-name">
            Vision<span>Inspect AI</span>
          </div>

          <div className="sidebar-brand-subtitle">
            QUALITY INTELLIGENCE
          </div>
        </div>
      </div>

      <nav
        className="sidebar-navigation"
        aria-label="Primary navigation"
      >
        <div className="sidebar-section-title">
          WORKSPACE
        </div>

        {visibleItems.map(([icon, label, path]) => (
          <button
            className={`sidebar-nav ${
              location.pathname === path ? "active" : ""
            }`}
            key={path}
            onClick={() => navigate(path)}
            type="button"
          >
            <span className="nav-icon">{icon}</span>
            {label}
          </button>
        ))}
      </nav>

      <div className="dashboard-sidebar-spacer" />

      <button
        className="sidebar-logout"
        onClick={logout}
        type="button"
      >
        <span>⇥</span>
        Logout
      </button>

    </aside>
  );
}

export default Sidebar;