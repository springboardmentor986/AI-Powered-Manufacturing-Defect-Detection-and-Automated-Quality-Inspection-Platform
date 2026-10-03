"use client";
import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { api } from "@/lib/api";

export default function DashboardPage() {
  const [summary, setSummary] = useState<any>(null);

  useEffect(() => {
    api.analyticsSummary().then(setSummary).catch(() => {});
  }, []);

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-8">
        <p className="text-muted text-xs tracking-widest uppercase">Overview</p>
        <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
        <div className="grid grid-cols-4 gap-4">
          <Stat label="Total Inspections" value={summary?.total_inspections ?? "—"} />
          <Stat label="Passed" value={summary?.pass_count ?? "—"} color="text-pass" />
          <Stat label="Failed" value={summary?.fail_count ?? "—"} color="text-critical" />
          <Stat label="Needs Review" value={summary?.review_count ?? "—"} color="text-high" />
        </div>
        <p className="text-muted text-sm mt-6">
          Upload or generate a sample on the Upload &amp; Inspect page to populate these numbers.
        </p>
      </main>
    </div>
  );
}

function Stat({ label, value, color = "text-ink" }: { label: string; value: any; color?: string }) {
  return (
    <div className="card p-4">
      <p className="text-muted text-xs">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
    </div>
  );
}
