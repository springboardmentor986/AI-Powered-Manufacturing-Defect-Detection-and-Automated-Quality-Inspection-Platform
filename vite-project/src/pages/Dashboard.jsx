import { useCallback, useEffect, useState } from "react";

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

function Dashboard({ user }) {
  const API_URL = "http://127.0.0.1:8000";

  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // =========================================================
  // FETCH REAL DASHBOARD DATA
  // =========================================================

  const fetchDashboardData = useCallback(async () => {
    try {
      const token = localStorage.getItem("access_token");

      if (!token) {
        setError("Your session has expired. Please login again.");
        setLoading(false);
        return;
      }

      const response = await fetch(
        `${API_URL}/reports/quality-summary?days=30`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
            Accept: "application/json",
          },
        }
      );

      let data = null;

      try {
        data = await response.json();
      } catch {
        data = null;
      }

      // -------------------------------------------------------
      // UNAUTHORIZED
      // -------------------------------------------------------

      if (response.status === 401) {
        setError("Unauthorized. Please login again.");
        setLoading(false);
        return;
      }

      // -------------------------------------------------------
      // OTHER API ERRORS
      // -------------------------------------------------------

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            `Failed to load dashboard (${response.status})`
        );
      }

      // -------------------------------------------------------
      // SAVE REPORT
      // -------------------------------------------------------

      setReport(data);
      setError("");
    } catch (err) {
      console.error("Dashboard error:", err);

      setError(
        err.message || "Failed to load dashboard data."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  // =========================================================
  // INITIAL LOAD + AUTOMATIC REFRESH
  // =========================================================

  useEffect(() => {
    fetchDashboardData();

    const interval = setInterval(() => {
      fetchDashboardData();
    }, 10000);

    return () => clearInterval(interval);
  }, [fetchDashboardData]);

  // =========================================================
  // FORMAT DEFECT NAME
  // =========================================================

  const formatDefectName = (value) => {
    if (!value) {
      return "-";
    }

    return String(value)
      .trim()
      .replaceAll("_", " ")
      .toLowerCase()
      .replace(/\b\w/g, (char) => char.toUpperCase());
  };

  // =========================================================
  // LOADING
  // =========================================================

  if (loading) {
    return (
      <div className="w-full">

        <div className="mb-6">
          <h1 className="text-2xl font-bold text-slate-900">
            Quality Dashboard
          </h1>

          <p className="mt-1 text-sm text-slate-500">
            Real-time quality inspection overview.
          </p>
        </div>

        <div className="flex min-h-[350px] items-center justify-center rounded-xl border border-slate-200 bg-white shadow-sm">

          <div className="text-center">

            <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-blue-600"></div>

            <p className="mt-4 text-sm text-slate-500">
              Loading dashboard data...
            </p>

          </div>

        </div>

      </div>
    );
  }

  // =========================================================
  // SAFE DATA
  // =========================================================

  const totalInspections =
    Number(report?.total_inspections ?? 0);

  const qualityDecided =
    Number(report?.quality_decided_inspections ?? 0);

  const severityDistribution =
    report?.severity_distribution ?? {
      Critical: 0,
      High: 0,
      Medium: 0,
      Low: 0,
    };

  const defectDistribution =
    report?.defect_distribution ?? {};

  // =========================================================
  // QUALITY RESULTS
  //
  // IMPORTANT:
  // Backend returns these values directly at the top level.
  // =========================================================

  const passed =
    Number(report?.passed ?? 0);

  const failed =
    Number(report?.failed ?? 0);

  const rework =
    Number(report?.rework ?? 0);

  const review =
    Number(report?.review ?? 0);

  const manualReview =
    Number(report?.manual_review ?? 0);

  const passRate =
    Number(report?.pass_rate ?? 0);

  const defectRate =
    Number(report?.defect_rate ?? 0);

  // ---------------------------------------------------------
  // TOTAL QUALITY ISSUES
  // ---------------------------------------------------------

  const defectiveItems =
    failed + rework + review;

  // =========================================================
  // PIE CHART DATA
  // =========================================================

  const qualityChartData = [
    {
      name: "PASS",
      value: passed,
    },
    {
      name: "FAILED",
      value: failed,
    },
    {
      name: "REWORK",
      value: rework,
    },
    {
      name: "REVIEW",
      value: review,
    },
  ].filter((item) => item.value > 0);

  // =========================================================
  // PIE CHART COLORS
  // =========================================================

  const PIE_COLORS = [
    "#22c55e",
    "#ef4444",
    "#f97316",
    "#6366f1",
  ];

  // =========================================================
  // DEFECT BAR DATA
  // =========================================================

  const defectValues =
    Object.values(defectDistribution);

  const maxDefectCount =
    defectValues.length > 0
      ? Math.max(...defectValues)
      : 1;

  // =========================================================
  // SEVERITY DATA
  // =========================================================

  const severityValues = [
    Number(severityDistribution.Critical ?? 0),
    Number(severityDistribution.High ?? 0),
    Number(severityDistribution.Medium ?? 0),
    Number(severityDistribution.Low ?? 0),
  ];

  const maxSeverityCount =
    Math.max(...severityValues, 1);

  // =========================================================
  // DASHBOARD
  // =========================================================

  return (
    <div className="w-full">

      {/* =====================================================
          HEADER
         ===================================================== */}

      <div className="mb-6 flex flex-col justify-between gap-4 md:flex-row md:items-center">

        <div>

          <h1 className="text-2xl font-bold text-slate-900">
            Quality Dashboard
          </h1>

          <p className="mt-1 text-sm text-slate-500">
            Real-time quality inspection overview.
          </p>

        </div>

        <div className="flex items-center gap-2 text-xs text-slate-500">

          <span className="h-2 w-2 rounded-full bg-green-500"></span>

          Live data

        </div>

      </div>


      {/* =====================================================
          ERROR
         ===================================================== */}

      {error && (
        <div className="mb-6 rounded-xl border border-red-200 bg-red-50 px-5 py-4">

          <p className="text-sm font-medium text-red-700">
            {error}
          </p>

        </div>
      )}


      {/* =====================================================
          STAT CARDS
         ===================================================== */}

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-4">

        {/* TOTAL */}

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

          <p className="text-sm font-medium text-slate-500">
            Total Inspections
          </p>

          <p className="mt-2 text-3xl font-bold text-slate-900">
            {totalInspections}
          </p>

          <p className="mt-2 text-xs text-slate-400">
            Last 30 days
          </p>

        </div>


        {/* PASS RATE */}

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

          <p className="text-sm font-medium text-slate-500">
            Pass Rate
          </p>

          <p className="mt-2 text-3xl font-bold text-green-600">
            {passRate.toFixed(1)}%
          </p>

          <p className="mt-2 text-xs text-slate-400">
            {passed} passed inspections
          </p>

        </div>


        {/* DEFECT RATE */}

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

          <p className="text-sm font-medium text-slate-500">
            Defect Rate
          </p>

          <p className="mt-2 text-3xl font-bold text-red-600">
            {defectRate.toFixed(1)}%
          </p>

          <p className="mt-2 text-xs text-slate-400">
            {defectiveItems} quality issues
          </p>

        </div>


        {/* MANUAL REVIEW */}

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

          <p className="text-sm font-medium text-slate-500">
            Manual Review
          </p>

          <p className="mt-2 text-3xl font-bold text-purple-600">
            {manualReview}
          </p>

          <p className="mt-2 text-xs text-slate-400">
            Require human verification
          </p>

        </div>

      </div>


      {/* =====================================================
          PIE CHART + SEVERITY
         ===================================================== */}

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">

        {/* ===================================================
            QUALITY RESULT PIE CHART
           =================================================== */}

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">

          <div className="mb-4">

            <h2 className="text-lg font-semibold text-slate-900">
              Quality Result Distribution
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Distribution of inspection quality decisions.
            </p>

          </div>


          {qualityChartData.length === 0 ? (

            <div className="flex h-[300px] items-center justify-center">

              <p className="text-sm text-slate-500">
                No quality result data available.
              </p>

            </div>

          ) : (

            <div className="h-[320px] w-full">

              <ResponsiveContainer
                width="100%"
                height="100%"
              >

                <PieChart>

                  <Pie
                    data={qualityChartData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="45%"
                    outerRadius={100}
                    innerRadius={55}
                    paddingAngle={3}
                    label={({ name, percent }) =>
                      `${name} ${(percent * 100).toFixed(0)}%`
                    }
                  >

                    {qualityChartData.map(
                      (entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={
                            PIE_COLORS[
                              index %
                                PIE_COLORS.length
                            ]
                          }
                        />
                      )
                    )}

                  </Pie>

                  <Tooltip
                    formatter={(value) => [
                      value,
                      "Inspections",
                    ]}
                  />

                  <Legend />

                </PieChart>

              </ResponsiveContainer>

            </div>

          )}

        </div>


        {/* ===================================================
            SEVERITY DISTRIBUTION
           =================================================== */}

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">

          <div className="mb-5">

            <h2 className="text-lg font-semibold text-slate-900">
              Severity Distribution
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Distribution of detected defect severity.
            </p>

          </div>


          <div className="space-y-5">

            {[
              {
                name: "Critical",
                value:
                  severityDistribution.Critical ?? 0,
                className: "bg-red-600",
                textClass: "text-red-600",
              },
              {
                name: "High",
                value:
                  severityDistribution.High ?? 0,
                className: "bg-orange-500",
                textClass: "text-orange-600",
              },
              {
                name: "Medium",
                value:
                  severityDistribution.Medium ?? 0,
                className: "bg-amber-500",
                textClass: "text-amber-600",
              },
              {
                name: "Low",
                value:
                  severityDistribution.Low ?? 0,
                className: "bg-green-500",
                textClass: "text-green-600",
              },
            ].map((item) => (

              <div key={item.name}>

                <div className="mb-2 flex items-center justify-between">

                  <span className="text-sm font-medium text-slate-600">
                    {item.name}
                  </span>

                  <span
                    className={`text-sm font-bold ${item.textClass}`}
                  >
                    {item.value}
                  </span>

                </div>

                <div className="h-3 overflow-hidden rounded-full bg-slate-100">

                  <div
                    className={`h-full rounded-full ${item.className}`}
                    style={{
                      width: `${
                        (Number(item.value) /
                          maxSeverityCount) *
                        100
                      }%`,
                    }}
                  />

                </div>

              </div>

            ))}

          </div>

        </div>

      </div>


      {/* =====================================================
          DEFECT DISTRIBUTION
         ===================================================== */}

      <div className="mt-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">

        <div className="mb-5">

          <h2 className="text-lg font-semibold text-slate-900">
            Defect Type Distribution
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Defects detected by the classification model.
          </p>

        </div>


        {Object.keys(defectDistribution).length === 0 ? (

          <div className="rounded-lg bg-slate-50 px-5 py-10 text-center">

            <p className="text-sm text-slate-500">
              No defect data available.
            </p>

          </div>

        ) : (

          <div className="space-y-4">

            {Object.entries(defectDistribution)
              .sort((a, b) => Number(b[1]) - Number(a[1]))
              .map(([defect, count]) => (

                <div key={defect}>

                  <div className="mb-2 flex items-center justify-between">

                    <span className="text-sm font-medium text-slate-700">
                      {formatDefectName(defect)}
                    </span>

                    <span className="text-sm font-semibold text-slate-900">
                      {count}
                    </span>

                  </div>

                  <div className="h-2 overflow-hidden rounded-full bg-slate-100">

                    <div
                      className="h-full rounded-full bg-blue-500"
                      style={{
                        width: `${
                          (Number(count) /
                            maxDefectCount) *
                          100
                        }%`,
                      }}
                    />

                  </div>

                </div>

              ))}

          </div>

        )}

      </div>


      {/* =====================================================
          SUMMARY
         ===================================================== */}

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">

        {/* QUALITY DECIDED */}

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

          <p className="text-sm text-slate-500">
            Quality Decided
          </p>

          <p className="mt-2 text-2xl font-bold text-slate-900">
            {qualityDecided}
          </p>

          <p className="mt-1 text-xs text-slate-400">
            Inspections with quality results
          </p>

        </div>


        {/* REWORK */}

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

          <p className="text-sm text-slate-500">
            Rework Required
          </p>

          <p className="mt-2 text-2xl font-bold text-orange-600">
            {rework}
          </p>

          <p className="mt-1 text-xs text-slate-400">
            High severity quality issues
          </p>

        </div>


        {/* REVIEW */}

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

          <p className="text-sm text-slate-500">
            Review Required
          </p>

          <p className="mt-2 text-2xl font-bold text-indigo-600">
            {review}
          </p>

          <p className="mt-1 text-xs text-slate-400">
            Medium severity issues
          </p>

        </div>

      </div>


      {/* =====================================================
          FOOTER
         ===================================================== */}

      <div className="mt-6 flex flex-col justify-between gap-2 text-xs text-slate-400 sm:flex-row">

        <span>
          Data source: VisionInspect AI inspection database
        </span>

        <span>
          Dashboard refreshes automatically every 10 seconds
        </span>

      </div>

    </div>
  );
}

export default Dashboard;