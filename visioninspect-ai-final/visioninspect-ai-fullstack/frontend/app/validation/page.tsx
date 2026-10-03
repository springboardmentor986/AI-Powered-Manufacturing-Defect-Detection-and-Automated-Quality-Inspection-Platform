"use client";
import { useState } from "react";
import Sidebar from "@/components/Sidebar";
import { api } from "@/lib/api";

export default function ValidationPage() {
  const [result, setResult] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function runSuite() {
    setBusy(true); setError(""); setResult(null);
    try {
      const r = await api.runValidation(25);
      setResult(r);
    } catch (err: any) {
      setError(err.message || "Validation failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-8">
        <h1 className="text-2xl font-bold mb-1">Validation &amp; Testing</h1>
        <p className="text-muted text-sm mb-6">
          Milestone 4 — generates a fresh labeled synthetic dataset and runs the real
          detection pipeline on it, live, to measure accuracy.
        </p>
        <button className="btn-primary mb-6" onClick={runSuite} disabled={busy}>
          {busy ? "Running…" : "Run Validation Suite"}
        </button>
        {error && <p className="text-critical">{error}</p>}
        {result && (
          <>
            <div className="grid grid-cols-4 gap-4 mb-6">
              <Metric label="Precision" value={result.precision} />
              <Metric label="Recall" value={result.recall} />
              <Metric label="F1 Score" value={result.f1} />
              <Metric label="mAP" value={result.mAP} />
            </div>
            <div className="card p-4 mb-4">
              <p className="font-semibold mb-2">Per-Class Average Precision</p>
              {Object.entries(result.per_class_ap).map(([cls, ap]: any) => (
                <div key={cls} className="flex justify-between text-sm py-1 border-b border-line">
                  <span className="capitalize">{cls}</span><span>{ap}</span>
                </div>
              ))}
            </div>
            <div className="card p-4 mb-4">
              <p className="font-semibold mb-2">Confusion Matrix (true → predicted)</p>
              {Object.entries(result.confusion_matrix).map(([trueCls, preds]: any) => (
                <p key={trueCls} className="text-sm text-muted">
                  <span className="text-ink capitalize">{trueCls}</span>: {Object.entries(preds).map(([p, n]: any) => `${p} ×${n}`).join(", ")}
                </p>
              ))}
            </div>
            <p className="text-xs text-muted border border-line rounded-md p-3">{result.caveat}</p>
          </>
        )}
      </main>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="card p-4 text-center">
      <p className="text-2xl font-bold text-amber">{value}</p>
      <p className="text-muted text-xs">{label}</p>
    </div>
  );
}
