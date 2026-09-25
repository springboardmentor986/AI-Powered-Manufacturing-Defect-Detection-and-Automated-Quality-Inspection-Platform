import { useEffect, useState } from "react";

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

function Reports() {
  const [days, setDays] = useState("30");
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [exportingCSV, setExportingCSV] = useState(false);
  const [exportingPDF, setExportingPDF] = useState(false);

  const API_URL = "http://127.0.0.1:8000";



  const fetchReport = async () => {
    try {
      setLoading(true);
      setError("");

      const token = localStorage.getItem("access_token");

      const response = await fetch(
        `${API_URL}/reports/quality-summary?days=${days}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error("Failed to load quality report");
      }

      const data = await response.json();

      setReport(data);
    } catch (err) {
      console.error(err);
      setError("Unable to load quality report.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, [days]);



  const exportCSV = async () => {
    try {
      setExportingCSV(true);

      const token = localStorage.getItem("access_token");

      const response = await fetch(
        `${API_URL}/reports/quality-summary/csv?days=${days}`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error("Failed to export CSV");
      }

      const blob = await response.blob();

      const url = window.URL.createObjectURL(blob);

      const link = document.createElement("a");

      link.href = url;
      link.download = `quality_report_${days}_days.csv`;

      document.body.appendChild(link);

      link.click();

      link.remove();

      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
      alert("Unable to export CSV report.");
    } finally {
      setExportingCSV(false);
    }
  };



  const exportPDF = async () => {
    try {
      setExportingPDF(true);

      const token = localStorage.getItem("access_token");

      const response = await fetch(
        `${API_URL}/reports/quality-summary/pdf?days=${days}`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error("Failed to export PDF");
      }

      const blob = await response.blob();

      const url = window.URL.createObjectURL(blob);

      const link = document.createElement("a");

      link.href = url;
      link.download = `quality_report_${days}_days.pdf`;

      document.body.appendChild(link);

      link.click();

      link.remove();

      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
      alert("Unable to export PDF report.");
    } finally {
      setExportingPDF(false);
    }
  };



  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <p className="text-sm text-slate-500">
          Loading quality report...
        </p>
      </div>
    );
  }



  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-6">
        <h2 className="font-semibold text-red-800">
          Report Error
        </h2>

        <p className="mt-1 text-sm text-red-600">
          {error}
        </p>

        <button
          onClick={fetchReport}
          className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }



  const total = report?.total_inspections ?? 0;

  const passed = report?.passed ?? 0;

  const failed = report?.failed ?? 0;

  const rework = report?.rework ?? 0;

  const review = report?.review ?? 0;

  const manualReview = report?.manual_review ?? 0;

  const passRate = report?.pass_rate ?? 0;

  const defectRate = report?.defect_rate ?? 0;

  const severityDistribution =
    report?.severity_distribution || {};

  const defectDistribution =
    report?.defect_distribution || {};


  const severityChartData = [
    {
      severity: "Critical",
      count: severityDistribution.Critical || 0,
    },
    {
      severity: "High",
      count: severityDistribution.High || 0,
    },
    {
      severity: "Medium",
      count: severityDistribution.Medium || 0,
    },
    {
      severity: "Low",
      count: severityDistribution.Low || 0,
    },
  ];



  const defectChartData = Object.entries(defectDistribution)
    .sort(([, a], [, b]) => b - a)
    .map(([defect, count]) => ({
      defect: formatDefectName(defect),
      count,
    }));



  return (
    <div className="space-y-6">

      {/* =====================================================
          HEADER
      ====================================================== */}

      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">

        <div>

          <h1 className="text-2xl font-bold text-slate-900">
            Quality Reports
          </h1>

          <p className="mt-1 text-sm text-slate-500">
            Analyze inspection quality results and defect information.
          </p>

        </div>

        {/* =================================================
            REPORT CONTROLS
        ================================================== */}

        <div className="flex flex-wrap items-center gap-3">

          {/* DATE RANGE */}

          <select
            value={days}
            onChange={(e) => setDays(e.target.value)}
            className="rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-700 outline-none focus:border-blue-500"
          >

            <option value="7">
              Last 7 days
            </option>

            <option value="30">
              Last 30 days
            </option>

            <option value="90">
              Last 90 days
            </option>

          </select>

          {/* EXPORT CSV */}

          <button
            onClick={exportCSV}
            disabled={exportingCSV}
            className="rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          >

            {exportingCSV
              ? "Exporting..."
              : "Export CSV"}

          </button>

          {/* EXPORT PDF */}

          <button
            onClick={exportPDF}
            disabled={exportingPDF}
            className="rounded-lg bg-slate-700 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
          >

            {exportingPDF
              ? "Exporting..."
              : "Export PDF"}

          </button>

        </div>

      </div>


      {/* =====================================================
          SUMMARY CARDS
      ====================================================== */}

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">

        {/* TOTAL */}

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

          <p className="text-sm text-slate-500">
            Total Inspections
          </p>

          <p className="mt-2 text-3xl font-bold text-slate-900">
            {total}
          </p>

        </div>


        {/* PASSED */}

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

          <p className="text-sm text-slate-500">
            Passed
          </p>

          <p className="mt-2 text-3xl font-bold text-green-600">
            {passed}
          </p>

          <p className="mt-1 text-xs text-slate-500">
            Pass rate:{" "}
            {Number(passRate).toFixed(1)}%
          </p>

        </div>


        {/* QUALITY ISSUES */}

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

          <p className="text-sm text-slate-500">
            Quality Issues
          </p>

          <p className="mt-2 text-3xl font-bold text-red-600">
            {failed + rework + review}
          </p>

          <p className="mt-1 text-xs text-slate-500">
            Defect rate:{" "}
            {Number(defectRate).toFixed(1)}%
          </p>

        </div>


        {/* MANUAL REVIEW */}

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

          <p className="text-sm text-slate-500">
            Manual Review
          </p>

          <p className="mt-2 text-3xl font-bold text-orange-600">
            {manualReview}
          </p>

        </div>

      </div>


      {/* =====================================================
          QUALITY RESULT DISTRIBUTION
      ====================================================== */}

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">

        <h2 className="text-lg font-semibold text-slate-900">
          Quality Result Distribution
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          Inspection outcomes for the selected period.
        </p>


        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

          <ResultCard
            title="PASS"
            value={passed}
            percentage={
              total
                ? (passed / total) * 100
                : 0
            }
            className="text-green-600"
          />


          <ResultCard
            title="FAILED"
            value={failed}
            percentage={
              total
                ? (failed / total) * 100
                : 0
            }
            className="text-red-600"
          />


          <ResultCard
            title="REWORK"
            value={rework}
            percentage={
              total
                ? (rework / total) * 100
                : 0
            }
            className="text-yellow-600"
          />


          <ResultCard
            title="REVIEW"
            value={review}
            percentage={
              total
                ? (review / total) * 100
                : 0
            }
            className="text-orange-600"
          />

        </div>

      </div>


      {/* =====================================================
          SEVERITY DISTRIBUTION
      ====================================================== */}

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">

        <h2 className="text-lg font-semibold text-slate-900">
          Severity Distribution
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          Distribution of detected defect severity levels.
        </p>


        <div className="mt-6">

          <ResponsiveContainer
            width="100%"
            height={320}
          >

            <BarChart
              data={severityChartData}
              margin={{
                top: 10,
                right: 20,
                left: 0,
                bottom: 10,
              }}
            >

              <CartesianGrid
                strokeDasharray="3 3"
              />

              <XAxis
                dataKey="severity"
              />

              <YAxis
                allowDecimals={false}
              />

              <Tooltip />

              {/* CHANGED COLOR */}

              <Bar
                dataKey="count"
                name="Inspections"
                fill="#6366f1"
                radius={[6, 6, 0, 0]}
              />

            </BarChart>

          </ResponsiveContainer>

        </div>

      </div>


      {/* =====================================================
          DEFECT TYPE DISTRIBUTION
      ====================================================== */}

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">

        <h2 className="text-lg font-semibold text-slate-900">
          Defect Type Distribution
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          Number of inspections for each detected defect type.
        </p>


        {defectChartData.length === 0 ? (

          <div className="mt-6 rounded-lg bg-slate-50 p-8 text-center">

            <p className="text-sm text-slate-500">
              No defect data available for this period.
            </p>

          </div>

        ) : (

          <div className="mt-6">

            <ResponsiveContainer
              width="100%"
              height={Math.max(
                320,
                defectChartData.length * 55
              )}
            >

              <BarChart
                data={defectChartData}
                layout="vertical"
                margin={{
                  top: 10,
                  right: 20,
                  left: 20,
                  bottom: 10,
                }}
              >

                <CartesianGrid
                  strokeDasharray="3 3"
                />

                <XAxis
                  type="number"
                  allowDecimals={false}
                />

                <YAxis
                  type="category"
                  dataKey="defect"
                  width={140}
                />

                <Tooltip />

                {/* CHANGED COLOR */}

                <Bar
                  dataKey="count"
                  name="Inspections"
                  fill="#0ea5e9"
                  radius={[0, 6, 6, 0]}
                />

              </BarChart>

            </ResponsiveContainer>

          </div>

        )}

      </div>


      {/* =====================================================
          REPORT SUMMARY
      ====================================================== */}

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">

        <h2 className="text-lg font-semibold text-slate-900">
          Report Summary
        </h2>


        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

          {/* QUALITY DECIDED */}

          <div className="rounded-lg bg-slate-50 p-4">

            <p className="text-xs text-slate-500">
              Quality Decided
            </p>

            <p className="mt-1 text-xl font-bold text-slate-900">
              {report?.quality_decided_inspections ?? 0}
            </p>

          </div>


          {/* REWORK */}

          <div className="rounded-lg bg-slate-50 p-4">

            <p className="text-xs text-slate-500">
              Rework Required
            </p>

            <p className="mt-1 text-xl font-bold text-slate-900">
              {rework}
            </p>

          </div>


          {/* MANUAL REVIEW */}

          <div className="rounded-lg bg-slate-50 p-4">

            <p className="text-xs text-slate-500">
              Manual Review
            </p>

            <p className="mt-1 text-xl font-bold text-slate-900">
              {manualReview}
            </p>

          </div>


          {/* REPORTING PERIOD */}

          <div className="rounded-lg bg-slate-50 p-4">

            <p className="text-xs text-slate-500">
              Reporting Period
            </p>

            <p className="mt-1 text-xl font-bold text-slate-900">
              {days} days
            </p>

          </div>

        </div>

      </div>

    </div>
  );
}




function ResultCard({
  title,
  value,
  percentage,
  className,
}) {

  return (

    <div className="rounded-lg border border-slate-200 p-5">

      <p className="text-sm font-medium text-slate-500">
        {title}
      </p>

      <p
        className={`mt-2 text-3xl font-bold ${className}`}
      >
        {value}
      </p>

      <p className="mt-1 text-xs text-slate-500">
        {percentage.toFixed(1)}%
      </p>

    </div>

  );
}




function formatDefectName(name) {

  return name
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) =>
      char.toUpperCase()
    );

}


export default Reports;