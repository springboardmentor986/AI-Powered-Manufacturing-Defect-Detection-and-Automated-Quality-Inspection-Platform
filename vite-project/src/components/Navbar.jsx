import { useAuth } from "../context/AuthContext";

function Navbar() {
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 h-16 bg-white border-b border-slate-200 shadow-sm">
      <div className="h-full px-6 flex items-center justify-between">

        {/* LEFT */}
        <div>
          <h2 className="text-lg font-bold text-slate-900">
            VisionInspect AI
          </h2>

          <p className="text-xs text-slate-500">
            Quality Inspection System
          </p>
        </div>

        {/* RIGHT */}
        {user && (
          <div className="flex items-center gap-5">

            <div className="text-right">
              <p className="text-sm font-semibold text-slate-800">
                {user.name}
              </p>

              <p className="text-xs text-blue-600">
                {user.role === "quality_engineer"
                  ? "Quality Engineer"
                  : "Factory Supervisor"}
              </p>
            </div>

            <button
              type="button"
              onClick={handleLogout}
              className="px-4 py-2 text-sm font-medium text-slate-600 rounded-lg hover:bg-red-50 hover:text-red-600 transition"
            >
              Logout
            </button>

          </div>
        )}

      </div>
    </nav>
  );
}

export default Navbar;