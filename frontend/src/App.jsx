import { useEffect } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate
} from "react-router-dom";

import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Inspection from "./pages/Inspection";
import Analytics from "./pages/Analytics";
import InspectionHistory from "./pages/InspectionHistory";
import CameraBatch from "./pages/CameraBatch";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";

import ProtectedRoute from "./components/ProtectedRoute";

function App() {
   useEffect(() => {
    const savedTheme = localStorage.getItem("theme") || "light";
    document.documentElement.setAttribute("data-theme", savedTheme);
  }, []);
  return (
    <BrowserRouter>

      <Routes>

        <Route
          path="/"
          element={<Navigate to="/login" replace />}
        />

        <Route
          path="/login"
          element={<Login />}
        />

        <Route
          path="/register"
          element={<Register />}
        />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/analytics"
          element={
            <ProtectedRoute>
              <Analytics />
            </ProtectedRoute>
          }
        />
        <Route
  path="/history"
  element={
    <ProtectedRoute>
      <InspectionHistory />
    </ProtectedRoute>
  }
/>
        <Route
          path="/inspection"
          element={
            <ProtectedRoute
              allowedRoles={["quality_engineer"]}
            >
              <Inspection />
            </ProtectedRoute>
          }
        />
        <Route
          path="/camera-batch"
          element={
            <ProtectedRoute allowedRoles={["quality_engineer"]}>
              <CameraBatch />
            </ProtectedRoute>
          }
        />
        <Route path="/reports" element={<ProtectedRoute><Reports /></ProtectedRoute>} />
        <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />

      </Routes>

    </BrowserRouter>
  );
}

export default App;