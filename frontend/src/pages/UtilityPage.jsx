import { useLocation } from "react-router-dom";
import Sidebar from "../components/Sidebar";

function UtilityPage() {
  const location = useLocation();
  const isSettings = location.pathname === "/settings";
  return (
    <div className="dashboard-layout">
      <Sidebar />
      <main className="dashboard-main">
        <header className="dashboard-header">
          <div>
            <div className="dashboard-breadcrumb">Workspace / {isSettings ? "Settings" : "Reports"}</div>
            <h1>{isSettings ? "Settings" : "Reports"}</h1>
            <p>{isSettings ? "Manage your inspection workspace preferences." : "Review and export inspection reports."}</p>
          </div>
        </header>
        <section className="camera-card">
          <h2>{isSettings ? "Workspace settings" : "Inspection reports"}</h2>
          <p>{isSettings ? "Settings are ready for configuration." : "Reports are available from your inspection history and analytics."}</p>
        </section>
      </main>
    </div>
  );
}

export default UtilityPage;
