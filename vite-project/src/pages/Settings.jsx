import { useState } from "react";
import { useAuth } from "../context/AuthContext";

function Settings() {
  const { user } = useAuth();

  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState("10");

  const roleName =
    user?.role === "quality_engineer"
      ? "Quality Engineer"
      : user?.role === "factory_supervisor"
        ? "Factory Supervisor"
        : "User";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">
          Settings
        </h1>

        <p className="mt-1 text-sm text-slate-500">
          Manage your profile, inspection preferences, and system information.
        </p>
      </div>

      {/* Profile Settings */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">
          Profile Settings
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          Your current account information.
        </p>

        <div className="mt-5 grid gap-5 md:grid-cols-2">
          <div>
            <label className="text-sm font-medium text-slate-700">
              Name
            </label>

            <input
              type="text"
              value={user?.name || ""}
              readOnly
              className="mt-2 w-full rounded-lg border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm text-slate-700 outline-none"
            />
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700">
              Email
            </label>

            <input
              type="email"
              value={user?.email || ""}
              readOnly
              className="mt-2 w-full rounded-lg border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm text-slate-700 outline-none"
            />
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700">
              Role
            </label>

            <input
              type="text"
              value={roleName}
              readOnly
              className="mt-2 w-full rounded-lg border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm text-slate-700 outline-none"
            />
          </div>
        </div>
      </div>

      {/* Inspection Settings */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">
          Inspection Settings
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          Current ML inspection thresholds.
        </p>

        <div className="mt-5 grid gap-5 md:grid-cols-3">
          {/* YOLO Threshold */}
          <div className="rounded-lg bg-slate-50 p-4">
            <p className="text-sm font-medium text-slate-600">
              YOLO Detection Threshold
            </p>

            <p className="mt-2 text-2xl font-bold text-slate-900">
              25%
            </p>

            <p className="mt-1 text-xs text-slate-500">
              Minimum confidence required to keep a YOLO detection
            </p>
          </div>

          {/* Classification Confidence */}
          <div className="rounded-lg bg-slate-50 p-4">
            <p className="text-sm font-medium text-slate-600">
              Classification Confidence
            </p>

            <p className="mt-2 text-2xl font-bold text-slate-900">
              70%
            </p>

            <p className="mt-1 text-xs text-slate-500">
              Minimum confidence used for classification review
            </p>
          </div>

          {/* Manual Review */}
          <div className="rounded-lg bg-slate-50 p-4">
            <p className="text-sm font-medium text-slate-600">
              Manual Review Threshold
            </p>

            <p className="mt-2 text-2xl font-bold text-slate-900">
              70%
            </p>

            <p className="mt-1 text-xs text-slate-500">
              Results below this level require manual review
            </p>
          </div>
        </div>

        {/* Explanation */}
        <div className="mt-5 rounded-lg border border-blue-100 bg-blue-50 p-4">
          <p className="text-sm font-medium text-blue-900">
            Confidence vs Threshold
          </p>

          <p className="mt-1 text-sm text-blue-700">
            The 25% YOLO value is a detection threshold, not the actual
            prediction confidence. For example, a YOLO detection may have
            75.95% confidence and still pass the 25% threshold.
          </p>
        </div>
      </div>

      {/* Severity Configuration */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">
          Severity Configuration
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          Current severity scoring configuration.
        </p>

        {/* Weights */}
        <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-lg border border-slate-200 p-4">
            <p className="text-sm text-slate-500">Size</p>
            <p className="mt-1 text-xl font-bold text-slate-900">
              30%
            </p>
          </div>

          <div className="rounded-lg border border-slate-200 p-4">
            <p className="text-sm text-slate-500">Location</p>
            <p className="mt-1 text-xl font-bold text-slate-900">
              25%
            </p>
          </div>

          <div className="rounded-lg border border-slate-200 p-4">
            <p className="text-sm text-slate-500">Defect Type</p>
            <p className="mt-1 text-xl font-bold text-slate-900">
              25%
            </p>
          </div>

          <div className="rounded-lg border border-slate-200 p-4">
            <p className="text-sm text-slate-500">Confidence</p>
            <p className="mt-1 text-xl font-bold text-slate-900">
              20%
            </p>
          </div>
        </div>

        {/* Severity Table */}
        <div className="mt-5 overflow-hidden rounded-lg border border-slate-200">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left font-semibold text-slate-700">
                  Severity
                </th>

                <th className="px-4 py-3 text-left font-semibold text-slate-700">
                  Score
                </th>

                <th className="px-4 py-3 text-left font-semibold text-slate-700">
                  Action
                </th>
              </tr>
            </thead>

            <tbody>
              <tr className="border-t border-slate-200">
                <td className="px-4 py-3 font-medium text-slate-900">
                  Critical
                </td>
                <td className="px-4 py-3 text-slate-600">
                  80–100
                </td>
                <td className="px-4 py-3 text-slate-600">
                  Reject
                </td>
              </tr>

              <tr className="border-t border-slate-200">
                <td className="px-4 py-3 font-medium text-slate-900">
                  High
                </td>
                <td className="px-4 py-3 text-slate-600">
                  60–79
                </td>
                <td className="px-4 py-3 text-slate-600">
                  Rework
                </td>
              </tr>

              <tr className="border-t border-slate-200">
                <td className="px-4 py-3 font-medium text-slate-900">
                  Medium
                </td>
                <td className="px-4 py-3 text-slate-600">
                  40–59
                </td>
                <td className="px-4 py-3 text-slate-600">
                  Review
                </td>
              </tr>

              <tr className="border-t border-slate-200">
                <td className="px-4 py-3 font-medium text-slate-900">
                  Low
                </td>
                <td className="px-4 py-3 text-slate-600">
                  0–39
                </td>
                <td className="px-4 py-3 text-slate-600">
                  Accept
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Dashboard Preferences */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">
          Dashboard Preferences
        </h2>

        <div className="mt-5 flex items-center justify-between rounded-lg bg-slate-50 p-4">
          <div>
            <p className="font-medium text-slate-800">
              Auto Refresh Dashboard
            </p>

            <p className="mt-1 text-xs text-slate-500">
              Automatically refresh dashboard statistics.
            </p>
          </div>

          <button
            type="button"
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`relative h-6 w-11 rounded-full transition ${
              autoRefresh ? "bg-blue-600" : "bg-slate-300"
            }`}
          >
            <span
              className={`absolute top-1 h-4 w-4 rounded-full bg-white transition ${
                autoRefresh ? "left-6" : "left-1"
              }`}
            />
          </button>
        </div>

        {autoRefresh && (
          <div className="mt-4 max-w-xs">
            <label className="text-sm font-medium text-slate-700">
              Refresh Interval
            </label>

            <select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(e.target.value)}
              className="mt-2 w-full rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm outline-none focus:border-blue-500"
            >
              <option value="5">5 seconds</option>
              <option value="10">10 seconds</option>
              <option value="30">30 seconds</option>
              <option value="60">60 seconds</option>
            </select>
          </div>
        )}
      </div>

      {/* System Information */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">
          System Information
        </h2>

        <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <p className="text-xs text-slate-500">
              Application
            </p>

            <p className="mt-1 font-medium text-slate-900">
              VisionInspect AI
            </p>
          </div>

          <div>
            <p className="text-xs text-slate-500">
              Version
            </p>

            <p className="mt-1 font-medium text-slate-900">
              1.0.0
            </p>
          </div>

          <div>
            <p className="text-xs text-slate-500">
              Object Detection
            </p>

            <p className="mt-1 font-medium text-slate-900">
              YOLO26n
            </p>
          </div>

          <div>
            <p className="text-xs text-slate-500">
              Classification
            </p>

            <p className="mt-1 font-medium text-slate-900">
              ResNet18
            </p>
          </div>

          <div>
            <p className="text-xs text-slate-500">
              Dataset
            </p>

            <p className="mt-1 font-medium text-slate-900">
              MVTec AD
            </p>
          </div>

          <div>
            <p className="text-xs text-slate-500">
              Backend
            </p>

            <p className="mt-1 font-medium text-slate-900">
              FastAPI + PostgreSQL
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Settings;