import { useAuth } from "../context/AuthContext";

function Sidebar({ page, setPage }) {
  const { user } = useAuth();

  const isQualityEngineer =
    user?.role === "quality_engineer";

  const isSupervisor =
    user?.role === "factory_supervisor";

  const getButtonClass = (pageName) =>
    `w-full rounded-lg px-4 py-3 text-left text-sm font-medium transition ${
      page === pageName
        ? "bg-blue-600 text-white"
        : "text-slate-300 hover:bg-slate-800 hover:text-white"
    }`;

  return (
    <aside
      className="
        w-[240px]
        min-w-[240px]
        max-w-[240px]
        shrink-0
        bg-slate-900
        text-white
      "
    >
      <div className="sticky top-0 flex h-screen flex-col">

        {/* Header */}
        <div className="border-b border-slate-800 px-5 py-5">
          <h2 className="text-lg font-bold">
            VisionInspect AI
          </h2>

          <p className="mt-1 text-xs text-slate-400">
            Quality Inspection System
          </p>
        </div>

        {/* User */}
        <div className="border-b border-slate-800 px-5 py-4">
          <p className="text-xs text-slate-400">
            Logged in as
          </p>

          <p className="mt-1 text-sm font-semibold text-white">
            {user?.name}
          </p>

          <p className="mt-1 text-xs text-blue-400">
            {isQualityEngineer
              ? "Quality Engineer"
              : isSupervisor
                ? "Factory Supervisor"
                : user?.role}
          </p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 px-3 py-4">

          {/* Dashboard */}
          <button
            type="button"
            onClick={() => setPage("dashboard")}
            className={getButtonClass("dashboard")}
          >
            Dashboard
          </button>

          {/* New Inspection */}
          {isQualityEngineer && (
            <button
              type="button"
              onClick={() => setPage("inspection")}
              className={getButtonClass("inspection")}
            >
              New Inspection
            </button>
          )}

          {/* Inspections */}
          {(isQualityEngineer || isSupervisor) && (
            <button
              type="button"
              onClick={() => setPage("inspections")}
              className={getButtonClass("inspections")}
            >
              Inspections
            </button>
          )}

          {/* Supervisor Pages */}
          {isSupervisor && (
            <>
              <button
                type="button"
                onClick={() => setPage("reports")}
                className={getButtonClass("reports")}
              >
                Reports
              </button>

              <button
                type="button"
                onClick={() => setPage("analytics")}
                className={getButtonClass("analytics")}
              >
                Analytics
              </button>

              <button
                type="button"
                onClick={() => setPage("users")}
                className={getButtonClass("users")}
              >
                Users
              </button>
            </>
          )}

          {/* Settings */}
          <button
            type="button"
            onClick={() => setPage("settings")}
            className={getButtonClass("settings")}
          >
            Settings
          </button>

        </nav>
      </div>
    </aside>
  );
}

export default Sidebar;