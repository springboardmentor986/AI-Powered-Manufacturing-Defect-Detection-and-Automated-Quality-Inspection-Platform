// import { useCallback, useEffect, useState } from "react";

// import {
//   BarChart,
//   Bar,
//   LineChart,
//   Line,
//   XAxis,
//   YAxis,
//   CartesianGrid,
//   Tooltip,
//   Legend,
//   ResponsiveContainer,
// } from "recharts";

// function Analytics({ user }) {
//   const API_URL = "http://127.0.0.1:8000";

//   const [analytics, setAnalytics] = useState(null);
//   const [days, setDays] = useState(30);
//   const [loading, setLoading] = useState(true);
//   const [error, setError] = useState("");

//   // =========================================================
//   // FETCH ANALYTICS DATA
//   // =========================================================

//   const fetchAnalytics = useCallback(async () => {
//     try {
//       const token = localStorage.getItem("access_token");

//       if (!token) {
//         setError("Your session has expired. Please login again.");
//         setLoading(false);
//         return;
//       }

//       const response = await fetch(
//         `${API_URL}/analytics/summary?days=${days}`,
//         {
//           method: "GET",
//           headers: {
//             Authorization: `Bearer ${token}`,
//             Accept: "application/json",
//           },
//         }
//       );

//       let data = null;

//       try {
//         data = await response.json();
//       } catch {
//         data = null;
//       }

//       // -------------------------------------------------------
//       // UNAUTHORIZED
//       // -------------------------------------------------------

//       if (response.status === 401) {
//         setError("Unauthorized. Please login again.");
//         setLoading(false);
//         return;
//       }

//       // -------------------------------------------------------
//       // OTHER API ERRORS
//       // -------------------------------------------------------

//       if (!response.ok) {
//         throw new Error(
//           data?.detail ||
//             `Failed to load analytics (${response.status})`
//         );
//       }

//       // -------------------------------------------------------
//       // SAVE DATA
//       // -------------------------------------------------------

//       setAnalytics(data);
//       setError("");
//     } catch (err) {
//       console.error("Analytics error:", err);

//       setError(
//         err.message || "Failed to load analytics data."
//       );
//     } finally {
//       setLoading(false);
//     }
//   }, [days]);

//   // =========================================================
//   // INITIAL LOAD + AUTOMATIC REFRESH
//   // =========================================================

//   useEffect(() => {
//     setLoading(true);

//     fetchAnalytics();

//     const interval = setInterval(() => {
//       fetchAnalytics();
//     }, 10000);

//     return () => clearInterval(interval);
//   }, [fetchAnalytics]);

//   // =========================================================
//   // SAFE DATA
//   // =========================================================

//   const totalInspections =
//     Number(analytics?.total_inspections ?? 0);

//   const qualityDecided =
//     Number(
//       analytics?.quality_decided_inspections ?? 0
//     );

//   const passed =
//     Number(analytics?.passed ?? 0);

//   const failed =
//     Number(analytics?.failed ?? 0);

//   const rework =
//     Number(analytics?.rework ?? 0);

//   const review =
//     Number(analytics?.review ?? 0);

//   const manualReview =
//     Number(analytics?.manual_review ?? 0);

//   const passRate =
//     Number(analytics?.pass_rate ?? 0);

//   const defectRate =
//     Number(analytics?.defect_rate ?? 0);

//   const dailyTrend =
//     analytics?.daily_trend ?? [];

//   const severityDistribution =
//     analytics?.severity_distribution ?? {
//       Critical: 0,
//       High: 0,
//       Medium: 0,
//       Low: 0,
//     };

//   const defectDistribution =
//     analytics?.defect_distribution ?? {};

//   // =========================================================
//   // CONFIDENCE DISTRIBUTION
//   // =========================================================

//   const confidenceDistribution =
//     analytics?.confidence_distribution ?? {
//       "<70%": 0,
//       "70-79%": 0,
//       "80-89%": 0,
//       "90-100%": 0,
//     };

//   // =========================================================
//   // FORMAT DEFECT NAME
//   // =========================================================

//   const formatDefectName = (value) => {
//     if (!value) {
//       return "-";
//     }

//     return String(value)
//       .trim()
//       .replaceAll("_", " ")
//       .toLowerCase()
//       .replace(/\b\w/g, (char) => char.toUpperCase());
//   };

//   // =========================================================
//   // FORMAT DATE
//   // =========================================================

//   const formatDate = (dateString) => {
//     if (!dateString) {
//       return "";
//     }

//     const date = new Date(`${dateString}T00:00:00`);

//     return date.toLocaleDateString("en-IN", {
//       day: "2-digit",
//       month: "short",
//     });
//   };

//   // =========================================================
//   // QUALITY RESULT DATA
//   // =========================================================

//   const qualityResultData = [
//     {
//       name: "PASS",
//       value: passed,
//     },
//     {
//       name: "FAILED",
//       value: failed,
//     },
//     {
//       name: "REWORK",
//       value: rework,
//     },
//     {
//       name: "REVIEW",
//       value: review,
//     },
//   ];

//   // =========================================================
//   // SEVERITY DATA
//   // =========================================================

//   const severityData = [
//     {
//       name: "Critical",
//       value: Number(
//         severityDistribution.Critical ?? 0
//       ),
//     },
//     {
//       name: "High",
//       value: Number(
//         severityDistribution.High ?? 0
//       ),
//     },
//     {
//       name: "Medium",
//       value: Number(
//         severityDistribution.Medium ?? 0
//       ),
//     },
//     {
//       name: "Low",
//       value: Number(
//         severityDistribution.Low ?? 0
//       ),
//     },
//   ];

//   // =========================================================
//   // DEFECT DATA
//   // =========================================================

//   const defectData = Object.entries(
//     defectDistribution
//   )
//     .map(([name, value]) => ({
//       name: formatDefectName(name),
//       value: Number(value),
//     }))
//     .sort((a, b) => b.value - a.value);

//   // =========================================================
//   // CONFIDENCE DATA
//   // =========================================================

//   const confidenceData = [
//     {
//       name: "<70%",
//       value: Number(
//         confidenceDistribution["<70%"] ?? 0
//       ),
//     },
//     {
//       name: "70-79%",
//       value: Number(
//         confidenceDistribution["70-79%"] ?? 0
//       ),
//     },
//     {
//       name: "80-89%",
//       value: Number(
//         confidenceDistribution["80-89%"] ?? 0
//       ),
//     },
//     {
//       name: "90-100%",
//       value: Number(
//         confidenceDistribution["90-100%"] ?? 0
//       ),
//     },
//   ];

//   // =========================================================
//   // LOADING
//   // =========================================================

//   if (loading && !analytics) {
//     return (
//       <div className="w-full">

//         <div className="mb-6">
//           <h1 className="text-2xl font-bold text-slate-900">
//             Analytics
//           </h1>

//           <p className="mt-1 text-sm text-slate-500">
//             View manufacturing analytics and quality trends.
//           </p>
//         </div>

//         <div className="flex min-h-[400px] items-center justify-center rounded-xl border border-slate-200 bg-white shadow-sm">

//           <div className="text-center">

//             <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-blue-600"></div>

//             <p className="mt-4 text-sm text-slate-500">
//               Loading analytics...
//             </p>

//           </div>

//         </div>

//       </div>
//     );
//   }

//   // =========================================================
//   // MAIN ANALYTICS PAGE
//   // =========================================================

//   return (
//     <div className="w-full">

//       {/* =====================================================
//           HEADER
//          ===================================================== */}

//       <div className="mb-6 flex flex-col justify-between gap-4 md:flex-row md:items-center">

//         <div>

//           <h1 className="text-2xl font-bold text-slate-900">
//             Analytics
//           </h1>

//           <p className="mt-1 text-sm text-slate-500">
//             View manufacturing analytics and quality trends.
//           </p>

//         </div>

//         {/* PERIOD SELECTOR */}

//         <div className="flex items-center gap-3">

//           <span className="text-sm text-slate-500">
//             Period
//           </span>

//           <select
//             value={days}
//             onChange={(event) =>
//               setDays(Number(event.target.value))
//             }
//             className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
//           >
//             <option value={7}>
//               Last 7 days
//             </option>

//             <option value={30}>
//               Last 30 days
//             </option>

//             <option value={90}>
//               Last 90 days
//             </option>
//           </select>

//         </div>

//       </div>

//       {/* =====================================================
//           ERROR
//          ===================================================== */}

//       {error && (
//         <div className="mb-6 rounded-xl border border-red-200 bg-red-50 px-5 py-4">

//           <p className="text-sm font-medium text-red-700">
//             {error}
//           </p>

//         </div>
//       )}

//       {/* =====================================================
//           LIVE STATUS
//          ===================================================== */}

//       <div className="mb-6 flex items-center justify-between">

//         <div className="flex items-center gap-2 text-xs text-slate-500">

//           <span className="h-2 w-2 rounded-full bg-green-500"></span>

//           Live analytics data

//         </div>

//         <p className="text-xs text-slate-400">
//           Automatically refreshes every 10 seconds
//         </p>

//       </div>

//       {/* =====================================================
//           KPI CARDS
//          ===================================================== */}

//       <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-4">

//         {/* TOTAL */}

//         <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

//           <p className="text-sm font-medium text-slate-500">
//             Total Inspections
//           </p>

//           <p className="mt-2 text-3xl font-bold text-slate-900">
//             {totalInspections}
//           </p>

//           <p className="mt-2 text-xs text-slate-400">
//             Last {days} days
//           </p>

//         </div>

//         {/* PASS RATE */}

//         <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

//           <p className="text-sm font-medium text-slate-500">
//             Pass Rate
//           </p>

//           <p className="mt-2 text-3xl font-bold text-green-600">
//             {passRate.toFixed(1)}%
//           </p>

//           <p className="mt-2 text-xs text-slate-400">
//             {passed} passed
//           </p>

//         </div>

//         {/* DEFECT RATE */}

//         <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

//           <p className="text-sm font-medium text-slate-500">
//             Defect Rate
//           </p>

//           <p className="mt-2 text-3xl font-bold text-red-600">
//             {defectRate.toFixed(1)}%
//           </p>

//           <p className="mt-2 text-xs text-slate-400">
//             {failed + rework + review} quality issues
//           </p>

//         </div>

//         {/* MANUAL REVIEW */}

//         <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

//           <p className="text-sm font-medium text-slate-500">
//             Manual Review
//           </p>

//           <p className="mt-2 text-3xl font-bold text-purple-600">
//             {manualReview}
//           </p>

//           <p className="mt-2 text-xs text-slate-400">
//             Require human verification
//           </p>

//         </div>

//       </div>

//       {/* =====================================================
//           INSPECTION TREND
//          ===================================================== */}

//       <div className="mt-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">

//         <div className="mb-5">

//           <h2 className="text-lg font-semibold text-slate-900">
//             Inspection Trend
//           </h2>

//           <p className="mt-1 text-sm text-slate-500">
//             Daily inspection volume and quality results.
//           </p>

//         </div>

//         {dailyTrend.length === 0 ? (

//           <div className="flex h-[350px] items-center justify-center">

//             <p className="text-sm text-slate-500">
//               No inspection trend data available.
//             </p>

//           </div>

//         ) : (

//           <div className="h-[350px] w-full">

//             <ResponsiveContainer
//               width="100%"
//               height="100%"
//             >

//               <LineChart
//                 data={dailyTrend.map((item) => ({
//                   ...item,
//                   displayDate: formatDate(item.date),
//                 }))}
//                 margin={{
//                   top: 10,
//                   right: 20,
//                   left: 0,
//                   bottom: 5,
//                 }}
//               >

//                 <CartesianGrid
//                   strokeDasharray="3 3"
//                   vertical={false}
//                 />

//                 <XAxis
//                   dataKey="displayDate"
//                   tick={{ fontSize: 12 }}
//                 />

//                 <YAxis
//                   allowDecimals={false}
//                   tick={{ fontSize: 12 }}
//                 />

//                 <Tooltip />

//                 <Legend />

//                 <Line
//                   type="monotone"
//                   dataKey="inspections"
//                   name="Inspections"
//                   stroke="#2563eb"
//                   strokeWidth={3}
//                   dot={{ r: 4 }}
//                   activeDot={{ r: 6 }}
//                 />

//                 <Line
//                   type="monotone"
//                   dataKey="passed"
//                   name="Passed"
//                   stroke="#22c55e"
//                   strokeWidth={2}
//                   dot={{ r: 3 }}
//                 />

//                 <Line
//                   type="monotone"
//                   dataKey="review"
//                   name="Review"
//                   stroke="#6366f1"
//                   strokeWidth={2}
//                   dot={{ r: 3 }}
//                 />

//               </LineChart>

//             </ResponsiveContainer>

//           </div>

//         )}

//       </div>

//       {/* =====================================================
//           QUALITY RESULT + SEVERITY
//          ===================================================== */}

//       <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">

//         {/* ===================================================
//             QUALITY RESULT
//            =================================================== */}

//         <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">

//           <div className="mb-5">

//             <h2 className="text-lg font-semibold text-slate-900">
//               Quality Results
//             </h2>

//             <p className="mt-1 text-sm text-slate-500">
//               Distribution of inspection quality decisions.
//             </p>

//           </div>

//           <div className="h-[320px] w-full">

//             <ResponsiveContainer
//               width="100%"
//               height="100%"
//             >

//               <BarChart
//                 data={qualityResultData}
//                 margin={{
//                   top: 10,
//                   right: 20,
//                   left: 0,
//                   bottom: 5,
//                 }}
//               >

//                 <CartesianGrid
//                   strokeDasharray="3 3"
//                   vertical={false}
//                 />

//                 <XAxis
//                   dataKey="name"
//                   tick={{ fontSize: 12 }}
//                 />

//                 <YAxis
//                   allowDecimals={false}
//                   tick={{ fontSize: 12 }}
//                 />

//                 <Tooltip />

//                 <Bar
//                   dataKey="value"
//                   name="Inspections"
//                   fill="#2563eb"
//                   radius={[6, 6, 0, 0]}
//                 />

//               </BarChart>

//             </ResponsiveContainer>

//           </div>

//         </div>

//         {/* ===================================================
//             SEVERITY
//            =================================================== */}

//         <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">

//           <div className="mb-5">

//             <h2 className="text-lg font-semibold text-slate-900">
//               Severity Analysis
//             </h2>

//             <p className="mt-1 text-sm text-slate-500">
//               Distribution of detected defect severity.
//             </p>

//           </div>

//           <div className="h-[320px] w-full">

//             <ResponsiveContainer
//               width="100%"
//               height="100%"
//             >

//               <BarChart
//                 data={severityData}
//                 margin={{
//                   top: 10,
//                   right: 20,
//                   left: 0,
//                   bottom: 5,
//                 }}
//               >

//                 <CartesianGrid
//                   strokeDasharray="3 3"
//                   vertical={false}
//                 />

//                 <XAxis
//                   dataKey="name"
//                   tick={{ fontSize: 12 }}
//                 />

//                 <YAxis
//                   allowDecimals={false}
//                   tick={{ fontSize: 12 }}
//                 />

//                 <Tooltip />

//                 <Bar
//                   dataKey="value"
//                   name="Defects"
//                   fill="#f97316"
//                   radius={[6, 6, 0, 0]}
//                 />

//               </BarChart>

//             </ResponsiveContainer>

//           </div>

//         </div>

//       </div>

//       {/* =====================================================
//           CONFIDENCE DISTRIBUTION
//          ===================================================== */}

//       <div className="mt-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">

//         <div className="mb-5">

//           <h2 className="text-lg font-semibold text-slate-900">
//             Confidence Distribution
//           </h2>

//           <p className="mt-1 text-sm text-slate-500">
//             Distribution of defect classification confidence levels.
//           </p>

//         </div>

//         <div className="h-[320px] w-full">

//           <ResponsiveContainer
//             width="100%"
//             height="100%"
//           >

//             <BarChart
//               data={confidenceData}
//               margin={{
//                 top: 10,
//                 right: 20,
//                 left: 0,
//                 bottom: 5,
//               }}
//             >

//               <CartesianGrid
//                 strokeDasharray="3 3"
//                 vertical={false}
//               />

//               <XAxis
//                 dataKey="name"
//                 tick={{ fontSize: 12 }}
//               />

//               <YAxis
//                 allowDecimals={false}
//                 tick={{ fontSize: 12 }}
//               />

//               <Tooltip />

//               <Bar
//                 dataKey="value"
//                 name="Inspections"
//                 fill="#8b5cf6"
//                 radius={[6, 6, 0, 0]}
//               />

//             </BarChart>

//           </ResponsiveContainer>

//         </div>

//       </div>

//       {/* =====================================================
//           DEFECT TYPE ANALYSIS
//          ===================================================== */}

//       <div className="mt-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">

//         <div className="mb-5">

//           <h2 className="text-lg font-semibold text-slate-900">
//             Defect Type Analysis
//           </h2>

//           <p className="mt-1 text-sm text-slate-500">
//             Frequency of defects identified by the classification model.
//           </p>

//         </div>

//         {defectData.length === 0 ? (

//           <div className="flex h-[300px] items-center justify-center">

//             <p className="text-sm text-slate-500">
//               No defect data available.
//             </p>

//           </div>

//         ) : (

//           <div className="h-[350px] w-full">

//             <ResponsiveContainer
//               width="100%"
//               height="100%"
//             >

//               <BarChart
//                 data={defectData}
//                 layout="vertical"
//                 margin={{
//                   top: 10,
//                   right: 30,
//                   left: 30,
//                   bottom: 10,
//                 }}
//               >

//                 <CartesianGrid
//                   strokeDasharray="3 3"
//                   horizontal={false}
//                 />

//                 <XAxis
//                   type="number"
//                   allowDecimals={false}
//                   tick={{ fontSize: 12 }}
//                 />

//                 <YAxis
//                   type="category"
//                   dataKey="name"
//                   width={150}
//                   tick={{ fontSize: 12 }}
//                 />

//                 <Tooltip />

//                 <Bar
//                   dataKey="value"
//                   name="Defects"
//                   fill="#2563eb"
//                   radius={[0, 6, 6, 0]}
//                 />

//               </BarChart>

//             </ResponsiveContainer>

//           </div>

//         )}

//       </div>

//       {/* =====================================================
//           ANALYTICS SUMMARY
//          ===================================================== */}

//       <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">

//         {/* QUALITY DECIDED */}

//         <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

//           <p className="text-sm text-slate-500">
//             Quality Decided
//           </p>

//           <p className="mt-2 text-2xl font-bold text-slate-900">
//             {qualityDecided}
//           </p>

//           <p className="mt-1 text-xs text-slate-400">
//             Inspections with quality results
//           </p>

//         </div>

//         {/* REWORK */}

//         <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

//           <p className="text-sm text-slate-500">
//             Rework Required
//           </p>

//           <p className="mt-2 text-2xl font-bold text-orange-600">
//             {rework}
//           </p>

//           <p className="mt-1 text-xs text-slate-400">
//             Inspections requiring rework
//           </p>

//         </div>

//         {/* REVIEW */}

//         <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

//           <p className="text-sm text-slate-500">
//             Review Required
//           </p>

//           <p className="mt-2 text-2xl font-bold text-indigo-600">
//             {review}
//           </p>

//           <p className="mt-1 text-xs text-slate-400">
//             Inspections requiring review
//           </p>

//         </div>

//       </div>

//       {/* =====================================================
//           FOOTER
//          ===================================================== */}

//       <div className="mt-6 flex flex-col justify-between gap-2 text-xs text-slate-400 sm:flex-row">

//         <span>
//           Data source: VisionInspect AI inspection database
//         </span>

//         <span>
//           Analytics refreshes automatically every 10 seconds
//         </span>

//       </div>

//     </div>
//   );
// }

// export default Analytics;
import { useCallback, useEffect, useState } from "react";

import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

function Analytics({ user }) {
  const API_URL = "http://127.0.0.1:8000";

  const [analytics, setAnalytics] = useState(null);
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // =========================================================
  // FETCH ANALYTICS DATA
  // =========================================================

  const fetchAnalytics = useCallback(async () => {
    try {
      const token = localStorage.getItem("access_token");

      if (!token) {
        setError("Your session has expired. Please login again.");
        setLoading(false);
        return;
      }

      const response = await fetch(
        `${API_URL}/analytics/summary?days=${days}`,
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

      if (response.status === 401) {
        setError("Unauthorized. Please login again.");
        setLoading(false);
        return;
      }

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            `Failed to load analytics (${response.status})`
        );
      }

      setAnalytics(data);
      setError("");
    } catch (err) {
      console.error("Analytics error:", err);

      setError(
        err.message || "Failed to load analytics data."
      );
    } finally {
      setLoading(false);
    }
  }, [days]);

  // =========================================================
  // INITIAL LOAD + AUTO REFRESH
  // =========================================================

  useEffect(() => {
    setLoading(true);

    fetchAnalytics();

    const interval = setInterval(() => {
      fetchAnalytics();
    }, 10000);

    return () => clearInterval(interval);
  }, [fetchAnalytics]);

  // =========================================================
  // SAFE DATA
  // =========================================================

  const totalInspections =
    Number(analytics?.total_inspections ?? 0);

  const qualityDecided =
    Number(
      analytics?.quality_decided_inspections ?? 0
    );

  const passed =
    Number(analytics?.passed ?? 0);

  const failed =
    Number(analytics?.failed ?? 0);

  const rework =
    Number(analytics?.rework ?? 0);

  const review =
    Number(analytics?.review ?? 0);

  const manualReview =
    Number(analytics?.manual_review ?? 0);

  const passRate =
    Number(analytics?.pass_rate ?? 0);

  const defectRate =
    Number(analytics?.defect_rate ?? 0);

  const dailyTrend =
    analytics?.daily_trend ?? [];

  const severityDistribution =
    analytics?.severity_distribution ?? {
      Critical: 0,
      High: 0,
      Medium: 0,
      Low: 0,
    };

  const defectDistribution =
    analytics?.defect_distribution ?? {};

  const confidenceDistribution =
    analytics?.confidence_distribution ?? {
      "<70%": 0,
      "70-79%": 0,
      "80-89%": 0,
      "90-100%": 0,
    };

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
  // FORMAT DATE
  // =========================================================

  const formatDate = (dateString) => {
    if (!dateString) {
      return "";
    }

    const date = new Date(`${dateString}T00:00:00`);

    return date.toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
    });
  };

  // =========================================================
  // QUALITY RESULT DATA
  // =========================================================

  const qualityResultData = [
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
  ];

  // =========================================================
  // SEVERITY DATA
  // =========================================================

  const severityData = [
    {
      name: "Critical",
      value: Number(
        severityDistribution.Critical ?? 0
      ),
    },
    {
      name: "High",
      value: Number(
        severityDistribution.High ?? 0
      ),
    },
    {
      name: "Medium",
      value: Number(
        severityDistribution.Medium ?? 0
      ),
    },
    {
      name: "Low",
      value: Number(
        severityDistribution.Low ?? 0
      ),
    },
  ];

  // =========================================================
  // DEFECT DATA
  // =========================================================

  const defectData = Object.entries(
    defectDistribution
  )
    .map(([name, value]) => ({
      name: formatDefectName(name),
      value: Number(value),
    }))
    .sort((a, b) => b.value - a.value);

  // =========================================================
  // CONFIDENCE DATA
  // =========================================================

  const confidenceData = [
    {
      name: "<70%",
      value: Number(
        confidenceDistribution["<70%"] ?? 0
      ),
    },
    {
      name: "70-79%",
      value: Number(
        confidenceDistribution["70-79%"] ?? 0
      ),
    },
    {
      name: "80-89%",
      value: Number(
        confidenceDistribution["80-89%"] ?? 0
      ),
    },
    {
      name: "90-100%",
      value: Number(
        confidenceDistribution["90-100%"] ?? 0
      ),
    },
  ];

  // =========================================================
  // LOADING SCREEN
  // =========================================================

  if (loading && !analytics) {
    return (
      <div className="w-full">

        <div className="mb-6">
          <h1 className="text-2xl font-bold text-slate-900">
            Analytics
          </h1>

          <p className="mt-1 text-sm text-slate-500">
            View manufacturing analytics and quality trends.
          </p>
        </div>

        <div className="flex min-h-[400px] items-center justify-center rounded-xl border border-slate-200 bg-white shadow-sm">

          <div className="text-center">

            <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-blue-600"></div>

            <p className="mt-4 text-sm text-slate-500">
              Loading analytics...
            </p>

          </div>

        </div>

      </div>
    );
  }

  // =========================================================
  // MAIN PAGE
  // =========================================================

  return (
    <div className="w-full">

      {/* =====================================================
          HEADER
         ===================================================== */}

      <div className="mb-6 flex flex-col justify-between gap-4 md:flex-row md:items-center">

        <div>

          <h1 className="text-2xl font-bold text-slate-900">
            Analytics
          </h1>

          <p className="mt-1 text-sm text-slate-500">
            View manufacturing analytics and quality trends.
          </p>

        </div>

        {/* PERIOD FILTER */}

        <div className="flex items-center gap-3">

          <span className="text-sm text-slate-500">
            Period
          </span>

          <select
            value={days}
            onChange={(event) =>
              setDays(Number(event.target.value))
            }
            className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          >
            <option value={7}>
              Last 7 days
            </option>

            <option value={30}>
              Last 30 days
            </option>

            <option value={90}>
              Last 90 days
            </option>
          </select>

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
          LIVE STATUS
         ===================================================== */}

      <div className="mb-6 flex items-center justify-between">

        <div className="flex items-center gap-2 text-xs text-slate-500">

          <span className="h-2 w-2 rounded-full bg-green-500"></span>

          Live analytics data

        </div>

        <p className="text-xs text-slate-400">
          Automatically refreshes every 10 seconds
        </p>

      </div>

      {/* =====================================================
          KPI CARDS
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
            Last {days} days
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
            {passed} passed
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
            {failed + rework + review} quality issues
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
          INSPECTION TREND
         ===================================================== */}

      <div className="mt-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">

        <div className="mb-5">

          <h2 className="text-lg font-semibold text-slate-900">
            Inspection Trend
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Daily inspection volume and quality results.
          </p>

        </div>

        {dailyTrend.length === 0 ? (

          <div className="flex h-[350px] items-center justify-center">

            <p className="text-sm text-slate-500">
              No inspection trend data available.
            </p>

          </div>

        ) : (

          <div className="h-[350px] w-full">

            <ResponsiveContainer
              width="100%"
              height="100%"
            >

              <LineChart
                data={dailyTrend.map((item) => ({
                  ...item,
                  displayDate: formatDate(item.date),
                }))}
                margin={{
                  top: 10,
                  right: 20,
                  left: 0,
                  bottom: 5,
                }}
              >

                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                />

                <XAxis
                  dataKey="displayDate"
                  tick={{ fontSize: 12 }}
                />

                <YAxis
                  allowDecimals={false}
                  tick={{ fontSize: 12 }}
                />

                <Tooltip />

                <Legend />

                {/* TOTAL INSPECTIONS */}

                <Line
                  type="monotone"
                  dataKey="inspections"
                  name="Inspections"
                  stroke="#2563eb"
                  strokeWidth={3}
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />

                {/* PASSED */}

                <Line
                  type="monotone"
                  dataKey="passed"
                  name="Passed"
                  stroke="#22c55e"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />

                {/* FAILED */}

                <Line
                  type="monotone"
                  dataKey="failed"
                  name="Failed"
                  stroke="#ef4444"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />

                {/* REWORK */}

                <Line
                  type="monotone"
                  dataKey="rework"
                  name="Rework"
                  stroke="#f97316"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />

                {/* REVIEW */}

                <Line
                  type="monotone"
                  dataKey="review"
                  name="Review"
                  stroke="#6366f1"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />

              </LineChart>

            </ResponsiveContainer>

          </div>

        )}

      </div>

      {/* =====================================================
          QUALITY RESULTS + SEVERITY
         ===================================================== */}

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">

        {/* ===================================================
            QUALITY RESULTS
           =================================================== */}

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">

          <div className="mb-5">

            <h2 className="text-lg font-semibold text-slate-900">
              Quality Results
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Distribution of inspection quality decisions.
            </p>

          </div>

          <div className="h-[320px] w-full">

            <ResponsiveContainer
              width="100%"
              height="100%"
            >

              <BarChart
                data={qualityResultData}
                margin={{
                  top: 10,
                  right: 20,
                  left: 0,
                  bottom: 5,
                }}
              >

                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                />

                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 12 }}
                />

                <YAxis
                  allowDecimals={false}
                  tick={{ fontSize: 12 }}
                />

                <Tooltip />

                <Bar
                  dataKey="value"
                  name="Inspections"
                  fill="#2563eb"
                  radius={[6, 6, 0, 0]}
                />

              </BarChart>

            </ResponsiveContainer>

          </div>

        </div>

        {/* ===================================================
            SEVERITY ANALYSIS
           =================================================== */}

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">

          <div className="mb-5">

            <h2 className="text-lg font-semibold text-slate-900">
              Severity Analysis
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Distribution of detected defect severity.
            </p>

          </div>

          <div className="h-[320px] w-full">

            <ResponsiveContainer
              width="100%"
              height="100%"
            >

              <BarChart
                data={severityData}
                margin={{
                  top: 10,
                  right: 20,
                  left: 0,
                  bottom: 5,
                }}
              >

                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                />

                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 12 }}
                />

                <YAxis
                  allowDecimals={false}
                  tick={{ fontSize: 12 }}
                />

                <Tooltip />

                <Bar
                  dataKey="value"
                  name="Defects"
                  fill="#f97316"
                  radius={[6, 6, 0, 0]}
                />

              </BarChart>

            </ResponsiveContainer>

          </div>

        </div>

      </div>

      {/* =====================================================
          CONFIDENCE DISTRIBUTION
         ===================================================== */}

      <div className="mt-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">

        <div className="mb-5">

          <h2 className="text-lg font-semibold text-slate-900">
            Confidence Distribution
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Distribution of defect classification confidence levels.
          </p>

        </div>

        <div className="h-[320px] w-full">

          <ResponsiveContainer
            width="100%"
            height="100%"
          >

            <BarChart
              data={confidenceData}
              margin={{
                top: 10,
                right: 20,
                left: 0,
                bottom: 5,
              }}
            >

              <CartesianGrid
                strokeDasharray="3 3"
                vertical={false}
              />

              <XAxis
                dataKey="name"
                tick={{ fontSize: 12 }}
              />

              <YAxis
                allowDecimals={false}
                tick={{ fontSize: 12 }}
              />

              <Tooltip />

              <Bar
                dataKey="value"
                name="Inspections"
                fill="#8b5cf6"
                radius={[6, 6, 0, 0]}
              />

            </BarChart>

          </ResponsiveContainer>

        </div>

      </div>

      {/* =====================================================
          DEFECT TYPE ANALYSIS
         ===================================================== */}

      <div className="mt-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">

        <div className="mb-5">

          <h2 className="text-lg font-semibold text-slate-900">
            Defect Type Analysis
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Frequency of defects identified by the classification model.
          </p>

        </div>

        {defectData.length === 0 ? (

          <div className="flex h-[300px] items-center justify-center">

            <p className="text-sm text-slate-500">
              No defect data available.
            </p>

          </div>

        ) : (

          <div className="h-[350px] w-full">

            <ResponsiveContainer
              width="100%"
              height="100%"
            >

              <BarChart
                data={defectData}
                layout="vertical"
                margin={{
                  top: 10,
                  right: 30,
                  left: 30,
                  bottom: 10,
                }}
              >

                <CartesianGrid
                  strokeDasharray="3 3"
                  horizontal={false}
                />

                <XAxis
                  type="number"
                  allowDecimals={false}
                  tick={{ fontSize: 12 }}
                />

                <YAxis
                  type="category"
                  dataKey="name"
                  width={150}
                  tick={{ fontSize: 12 }}
                />

                <Tooltip />

                <Bar
                  dataKey="value"
                  name="Defects"
                  fill="#2563eb"
                  radius={[0, 6, 6, 0]}
                />

              </BarChart>

            </ResponsiveContainer>

          </div>

        )}

      </div>

      {/* =====================================================
          ANALYTICS SUMMARY
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
            Inspections requiring rework
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
            Inspections requiring review
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
          Analytics refreshes automatically every 10 seconds
        </span>

      </div>

    </div>
  );
}

export default Analytics;