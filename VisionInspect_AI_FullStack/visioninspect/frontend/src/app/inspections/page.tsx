"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import ProtectedPage from "@/components/ProtectedPage";
import api from "@/lib/api";
import { InspectionSummary, InspectionStatus } from "@/lib/types";
import { StatusBadge, SeverityBadge } from "@/components/Badges";

function InspectionsContent() {
  const [inspections, setInspections] = useState<InspectionSummary[]>([]);
  const [statusFilter, setStatusFilter] = useState<InspectionStatus | "">("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get("/api/inspections", {
        params: { limit: 100, ...(statusFilter ? { status: statusFilter } : {}) },
      })
      .then((res) => setInspections(res.data))
      .finally(() => setLoading(false));
  }, [statusFilter]);

  function exportCsv() {
    window.open(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/inspections/export/csv`, "_blank");
  }

  return (
    <div>
      <div className="mb-7 flex items-start justify-between">
        <div>
          <p className="eyebrow mb-1">Quality Control</p>
          <h1 className="font-display text-2xl font-semibold">Inspections</h1>
          <p className="text-sm text-muted mt-1">Full inspection history and pass/fail decisions.</p>
        </div>
        <button onClick={exportCsv} className="btn-secondary text-sm">
          Export CSV
        </button>
      </div>

      <div className="flex gap-2 mb-4">
        {(["", "pass", "fail", "review", "pending"] as const).map((s) => (
          <button
            key={s || "all"}
            onClick={() => setStatusFilter(s as InspectionStatus | "")}
            className={`text-xs px-3 py-1.5 rounded border ${
              statusFilter === s
                ? "border-amber text-amber bg-panel-2"
                : "border-line text-muted hover:text-ink"
            }`}
          >
            {s === "" ? "All" : s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      <div className="card px-5 py-4">
        {loading ? (
          <p className="text-sm text-muted">Loading…</p>
        ) : inspections.length === 0 ? (
          <p className="text-sm text-muted">No inspections found for this filter.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-muted text-xs uppercase border-b border-line">
                <th className="pb-2 font-medium">ID</th>
                <th className="pb-2 font-medium">File</th>
                <th className="pb-2 font-medium">Uploaded</th>
                <th className="pb-2 font-medium">Defects</th>
                <th className="pb-2 font-medium">Max Severity</th>
                <th className="pb-2 font-medium">Status</th>
                <th className="pb-2 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {inspections.map((r) => (
                <tr key={r.id} className="border-b border-line/50 last:border-0">
                  <td className="py-2 font-mono text-xs text-muted">#{r.id}</td>
                  <td className="py-2 font-mono text-xs">{r.filename}</td>
                  <td className="py-2 text-xs text-muted">
                    {new Date(r.uploaded_at).toLocaleString()}
                  </td>
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

export default function InspectionsPage() {
  return (
    <ProtectedPage>
      <InspectionsContent />
    </ProtectedPage>
  );
}
