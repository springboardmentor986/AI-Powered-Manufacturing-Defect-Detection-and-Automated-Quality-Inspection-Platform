"use client";

import { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  BarChart,
  Bar,
} from "recharts";
import ProtectedPage from "@/components/ProtectedPage";
import api from "@/lib/api";
import { AnalyticsSummary } from "@/lib/types";

function AnalyticsContent() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get("/api/analytics/summary", { params: { days } })
      .then((res) => setSummary(res.data))
      .finally(() => setLoading(false));
  }, [days]);

  return (
    <div>
      <div className="mb-7 flex items-start justify-between">
        <div>
          <p className="eyebrow mb-1">Manufacturing Analytics</p>
          <h1 className="font-display text-2xl font-semibold">Defect Trend Dashboard</h1>
          <p className="text-sm text-muted mt-1">
            Production quality insights and defect trend analysis.
          </p>
        </div>
        <div className="flex gap-2">
          {[7, 30, 90].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`text-xs px-3 py-1.5 rounded border ${
                days === d ? "border-amber text-amber bg-panel-2" : "border-line text-muted"
              }`}
            >
              {d}d
            </button>
          ))}
        </div>
      </div>

      {loading || !summary ? (
        <p className="text-sm text-muted">Loading analytics…</p>
      ) : (
        <div className="space-y-6">
          <div className="card px-5 py-4">
            <p className="text-sm font-medium mb-4">Inspections &amp; Defects Over Time</p>
            {summary.trend.length === 0 ? (
              <p className="text-sm text-muted">Not enough data yet — upload some images first.</p>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={summary.trend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#383E44" />
                  <XAxis dataKey="date" stroke="#9AA0A6" fontSize={11} />
                  <YAxis stroke="#9AA0A6" fontSize={11} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{ background: "#24282C", border: "1px solid #383E44", fontSize: 12 }}
                  />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Line type="monotone" dataKey="total_inspections" name="Inspections" stroke="#F5A623" strokeWidth={2} />
                  <Line type="monotone" dataKey="total_defects" name="Defects" stroke="#E4572E" strokeWidth={2} />
                  <Line type="monotone" dataKey="fail_count" name="Failed" stroke="#E08A3D" strokeWidth={2} />
                  <Line type="monotone" dataKey="pass_count" name="Passed" stroke="#4FA65B" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <div className="card px-5 py-4">
              <p className="text-sm font-medium mb-4">Defect Type Distribution</p>
              {summary.defect_type_breakdown.length === 0 ? (
                <p className="text-sm text-muted">No defects recorded yet.</p>
              ) : (
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={summary.defect_type_breakdown}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#383E44" />
                    <XAxis dataKey="defect_type" stroke="#9AA0A6" fontSize={11} />
                    <YAxis stroke="#9AA0A6" fontSize={11} allowDecimals={false} />
                    <Tooltip contentStyle={{ background: "#24282C", border: "1px solid #383E44", fontSize: 12 }} />
                    <Bar dataKey="count" fill="#F5A623" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
            <div className="card px-5 py-4">
              <p className="text-sm font-medium mb-4">Severity Distribution</p>
              {summary.severity_breakdown.length === 0 ? (
                <p className="text-sm text-muted">No defects recorded yet.</p>
              ) : (
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={summary.severity_breakdown}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#383E44" />
                    <XAxis dataKey="severity_level" stroke="#9AA0A6" fontSize={11} />
                    <YAxis stroke="#9AA0A6" fontSize={11} allowDecimals={false} />
                    <Tooltip contentStyle={{ background: "#24282C", border: "1px solid #383E44", fontSize: 12 }} />
                    <Bar dataKey="count" fill="#E08A3D" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function AnalyticsPage() {
  return (
    <ProtectedPage>
      <AnalyticsContent />
    </ProtectedPage>
  );
}
