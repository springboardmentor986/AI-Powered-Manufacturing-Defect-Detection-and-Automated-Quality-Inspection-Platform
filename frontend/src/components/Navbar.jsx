import { Link, useNavigate, useLocation } from "react-router-dom";
import { getStoredUser, logout } from "../services/api";

function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const user = getStoredUser();

  const isSupervisor = user?.role_id === 2;
  const dashboardPath = isSupervisor ? "/supervisor/dashboard" : "/dashboard";

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header className="navbar">
      <div className="navbar-inner">
        <Link to={dashboardPath} className="navbar-brand-link">
          <div className="navbar-brand-logo">VI</div>
          <span className="navbar-brand-title">VisionInspect AI</span>
        </Link>

        <nav className="navbar-links">
          {!isSupervisor && (
            <>
              <Link
                to="/dashboard"
                className={`nav-link ${location.pathname === "/dashboard" ? "active" : ""}`}
              >
                Dashboard
              </Link>
              <Link
                to="/upload"
                className={`nav-link ${location.pathname === "/upload" ? "active" : ""}`}
              >
                Upload Image
              </Link>
            </>
          )}

          {isSupervisor && (
            <>
              <Link
                to="/supervisor/dashboard"
                className={`nav-link ${location.pathname === "/supervisor/dashboard" ? "active" : ""}`}
              >
                Supervisor Dashboard
              </Link>
            </>
          )}
        </nav>

        {/* User Profile & Logout */}
        <div className="navbar-user-section">
          {user && (
            <div className="user-profile-meta">
              <span className="user-profile-name">{user.name || user.email}</span>
              <span className="badge badge-role">
                {user.role || (isSupervisor ? "Factory Supervisor" : "Quality Engineer")}
              </span>
            </div>
          )}

          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={handleLogout}
            title="Sign out of console"
          >
            Sign Out
          </button>
        </div>
      </div>
    </header>
  );
}

export default Navbar;
