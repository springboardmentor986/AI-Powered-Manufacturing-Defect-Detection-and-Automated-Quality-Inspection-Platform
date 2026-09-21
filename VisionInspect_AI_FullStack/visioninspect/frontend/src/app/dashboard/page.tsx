"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import ProtectedPage from "@/components/ProtectedPage";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/api";
import { AnalyticsSummary, InspectionSummary } from "@/lib/types";
import { StatusBadge, SeverityBadge } from "@/components/Badges";

function StatCard({ label, value, accent }: { label: string; value: string | number; accent?: string }) {
  return (
    <div className="card px-5 py-4">
      <p className="text-xs text-muted uppercase tracking-wide mb-2">{label}</p>
      <p className={`font-display text-2xl font-semibold ${accent || ""}`}>{value}</p>
    </div>
  );
}

function DashboardContent() {
  const { user } = useAuth();
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [recent, setRecent] = useState<InspectionSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get("/api/analytics/summary"),
      api.get("/api/inspections", { params: { limit: 8 } }),
    ])
      .then(([a, i]) => {
        setSummary(a.data);
        setRecent(i.data);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="mb-7">
        <p className="eyebrow mb-1">Overview</p>
        <h1 className="font-display text-2xl font-semibold">
          Welcome back{user ? `, ${user.full_name.split(" ")[0]}` : ""}
        </h1>
        <p className="text-sm text-muted mt-1">
          Production quality monitoring for the last 30 days
        </p>
      </div>

      {loading || !summary ? (
        <p className="text-muted text-sm">Loading dashboard…</p>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <StatCard label="Images Inspected" value={summary.total_images} />
            <StatCard label="Defects Found" value={summary.total_defects} />
            <StatCard label="Pass Rate" value={`${summary.pass_rate}%`} accent="text-pass" />
            <StatCard label="Failed" value={summary.fail_count} accent="text-critical" />
          </div>

          <div className="grid md:grid-cols-2 gap-5 mb-8">
            <div className="card px-5 py-4">
              <p className="text-sm font-medium mb-3">Defect Type Breakdown</p>
              {summary.defect_type_breakdown.length === 0 ? (
                <p className="text-sm text-muted">No defects recorded yet.</p>
              ) : (
                <ul className="space-y-2">
                  {summary.defect_type_breakdown.map((d) => (
                    <li key={d.defect_type} className="flex justify-between text-sm">
                      <span className="capitalize text-muted">{d.defect_type}</span>
                      <span className="font-mono">{d.count}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div className="card px-5 py-4">
              <p className="text-sm font-medium mb-3">Severity Breakdown</p>
              {summary.severity_breakdown.length === 0 ? (
                <p className="text-sm text-muted">No defects recorded yet.</p>
              ) : (
                <ul className="space-y-2">
                  {summary.severity_breakdown.map((s) => (
                    <li key={s.severity_level} className="flex justify-between items-center text-sm">
                      <SeverityBadge level={s.severity_level as any} />
                      <span className="font-mono">{s.count}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </>
      )}

      <div className="card px-5 py-4">
        <div className="flex items-center justify-between mb-3">
          <p className="text-sm font-medium">Recent Inspections</p>
          <Link href="/inspections" className="text-xs text-amber hover:underline">
            View all →
          </Link>
        </div>
        {recent.length === 0 ? (
          <p className="text-sm text-muted">
            No inspections yet.{" "}
            <Link href="/upload" className="text-amber hover:underline">
              Upload an image
            </Link>{" "}
            to get started.
          </p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-muted text-xs uppercase border-b border-line">
                <th className="pb-2 font-medium">File</th>
                <th className="pb-2 font-medium">Defects</th>
                <th className="pb-2 font-medium">Max Severity</th>
                <th className="pb-2 font-medium">Status</th>
                <th className="pb-2 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {recent.map((r) => (
                <tr key={r.id} className="border-b border-line/50 last:border-0">
                  <td className="py-2 font-mono text-xs">{r.filename}</td>
                  <td className="py-2">{r.defect_count}</td>
                  <td className="py-2">
                    <SeverityBadge level={r.max_severity} />
                  </td>
                  <td className="py-2">
                    <StatusBadge status={r.status} />
                  </td>
                  <td className="py-2 text-right">
                    <Link href={`/inspections/${r.id}`} className="text-amber text-xs hover:underline">
                      Details
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <ProtectedPage>
      <DashboardContent />
    </ProtectedPage>
  );
}
