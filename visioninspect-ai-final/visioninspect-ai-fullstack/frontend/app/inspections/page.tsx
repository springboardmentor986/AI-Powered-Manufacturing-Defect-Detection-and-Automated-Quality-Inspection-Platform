"use client";
import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { api } from "@/lib/api";

export default function InspectionsPage() {
  const [items, setItems] = useState<any[]>([]);

  useEffect(() => {
    api.listInspections().then(setItems).catch(() => {});
  }, []);

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-8">
        <h1 className="text-2xl font-bold mb-6">Inspections</h1>
        <table className="w-full text-sm">
          <thead className="text-muted text-left border-b border-line">
            <tr><th className="py-2">File</th><th>Product Line</th><th>Status</th><th>Defects</th><th>Uploaded</th></tr>
          </thead>
          <tbody>
            {items.map((i) => (
              <tr key={i.id} className="border-b border-line">
                <td className="py-2">{i.filename}</td>
                <td>{i.product_line || "—"}</td>
                <td><span className={`badge badge-${i.status === "fail" ? "critical" : i.status === "review" ? "medium" : "low"}`}>{i.status}</span></td>
                <td>{i.defects.length}</td>
                <td className="text-muted">{new Date(i.uploaded_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <p className="text-muted mt-4">No inspections yet.</p>}
      </main>
    </div>
  );
}
