import { useState } from "react";

import Navbar from "./components/Navbar";
import Sidebar from "./components/Sidebar";

import Dashboard from "./pages/Dashboard";
import Inspection from "./pages/Inspection";
import Inspections from "./pages/Inspections";
import Reports from "./pages/Reports";
import Analytics from "./pages/Analytics";
import Users from "./pages/Users";
import Settings from "./pages/Settings";
import Login from "./pages/Login";

import { useAuth } from "./context/AuthContext";

import "./App.css";

function App() {
  const { user, loading } = useAuth();

  const [page, setPage] = useState("dashboard");

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-slate-900">
            VisionInspect AI
          </h1>

          <p className="mt-2 text-sm text-slate-500">
            Loading...
          </p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Login />;
  }

  const handleNavigation = (newPage) => {
    setPage(newPage);
  };

  const renderPage = () => {
    switch (page) {
      case "dashboard":
        return <Dashboard user={user} />;

      case "inspection":
        return <Inspection user={user} />;

      case "inspections":
        return <Inspections user={user} />;

      case "reports":
        return <Reports user={user} />;

      case "analytics":
        return <Analytics user={user} />;

      case "users":
        return <Users user={user} />;

      case "settings":
        return <Settings user={user} />;

      default:
        return <Dashboard user={user} />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />

      <div className="flex min-h-screen pt-16">
        <Sidebar
          page={page}
          setPage={handleNavigation}
        />

        <main className="min-w-0 flex-1 overflow-x-hidden">
          <div className="w-full px-8 pt-0 pb-6">
            {renderPage()}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;