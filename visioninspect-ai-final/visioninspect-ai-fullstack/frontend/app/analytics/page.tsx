"use client";
import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { api } from "@/lib/api";
import { Bar, Line } from "react-chartjs-2";
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement, PointElement, Tooltip, Legend,
} from "chart.js";
ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, Tooltip, Legend);

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<any>(null);

  useEffect(() => {
    api.analyticsSummary().then(setSummary).catch(() => {});
  }, []);

  if (!summary) return <div className="flex"><Sidebar /><main className="flex-1 p-8">Loading…</main></div>;

  const trendData = {
    labels: Object.keys(summary.inspections_over_time),
    datasets: [{ label: "Inspections", data: Object.values(summary.inspections_over_time), backgroundColor: "#F0B43C" }],
  };
  const typeData = {
    labels: Object.keys(summary.defect_type_counts),
    datasets: [{ label: "Defects", data: Object.values(summary.defect_type_counts), backgroundColor: "#F0B43C" }],
  };
  const severityData = {
    labels: Object.keys(summary.severity_counts),
    datasets: [{ label: "Defects", data: Object.values(summary.severity_counts),
      backgroundColor: ["#E5484D", "#F0924A", "#38C9C9", "#4CB782"] }],
  };

  const noData = summary.total_inspections === 0;

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-8">
        <h1 className="text-2xl font-bold mb-1">Defect Trend Dashboard</h1>
        <p className="text-muted text-sm mb-6">Production quality insights and defect trend analysis.</p>
        {noData && (
          <div className="card p-4 mb-6">
            <p className="text-muted text-sm">No inspections yet, so there is nothing to chart. Upload an image first.</p>
          </div>
        )}
        <div className="card p-4 mb-4">
          <p className="font-semibold mb-2">Inspections Over Time</p>
          <Line data={trendData} />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="card p-4">
            <p className="font-semibold mb-2">Defect Type Distribution</p>
            <Bar data={typeData} />
          </div>
          <div className="card p-4">
            <p className="font-semibold mb-2">Severity Distribution</p>
            <Bar data={severityData} />
          </div>
        </div>
      </main>
    </div>
  );
}
