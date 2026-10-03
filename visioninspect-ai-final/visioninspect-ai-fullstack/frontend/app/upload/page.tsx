"use client";
import { useRef, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { api } from "@/lib/api";

export default function UploadPage() {
  const [productLine, setProductLine] = useState("");
  const [batchId, setBatchId] = useState("");
  const [result, setResult] = useState<any>(null);
  const [fixes, setFixes] = useState<any[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleFile(file: File) {
    setBusy(true); setError(""); setResult(null); setFixes([]);
    try {
      const inspection = await api.uploadInspection(file, productLine, batchId);
      setResult(inspection);
      const f = await api.getFixes(inspection.id);
      setFixes(f);
    } catch (err: any) {
      setError(err.message || "Upload failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 p-8">
        <p className="text-muted text-xs tracking-widest uppercase">Image Acquisition</p>
        <h1 className="text-2xl font-bold mb-1">Upload &amp; Inspect</h1>
        <p className="text-muted text-sm mb-6">
          Upload a product image to run it through the live defect-detection pipeline.
        </p>

        <div className="card p-5 mb-6 grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm block mb-1">Product line (optional)</label>
            <input className="w-full bg-bg border border-line rounded-md px-3 py-2 text-sm"
              value={productLine} onChange={(e) => setProductLine(e.target.value)} placeholder="e.g. Line-A" />
          </div>
          <div>
            <label className="text-sm block mb-1">Batch ID (optional)</label>
            <input className="w-full bg-bg border border-line rounded-md px-3 py-2 text-sm"
              value={batchId} onChange={(e) => setBatchId(e.target.value)} placeholder="e.g. BATCH-2026-09-10" />
          </div>
        </div>

        <div
          className="card p-10 text-center cursor-pointer mb-6"
          onClick={() => inputRef.current?.click()}
          onDrop={(e) => { e.preventDefault(); if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]); }}
          onDragOver={(e) => e.preventDefault()}
        >
          <p>Click to choose an image, or drop it here</p>
          <p className="text-muted text-xs mt-1">JPG, PNG, BMP, WEBP</p>
          <input ref={inputRef} type="file" accept="image/*" className="hidden"
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])} />
        </div>

        {busy && <p className="text-muted">Running detection pipeline…</p>}
        {error && <p className="text-critical">{error}</p>}

        {result && (
          <div className="grid grid-cols-3 gap-4 items-start">
            <div className="card p-3">
              <p className="text-xs text-muted mb-2">Annotated Image</p>
              <img src={`${process.env.NEXT_PUBLIC_API_URL}/${result.annotated_path}`} className="w-full rounded" />
            </div>
            <div>
              <p className="text-sm font-semibold mb-2">Detected Defects ({result.defects.length})</p>
              {result.defects.length === 0 && <p className="text-pass text-sm">No defects found.</p>}
              {result.defects.map((d: any) => (
                <div key={d.id} className="card p-3 mb-2">
                  <div className="flex justify-between items-center">
                    <span className="capitalize font-semibold text-sm">{d.defect_type}</span>
                    <span className={`badge badge-${d.severity_level}`}>{d.severity_level}</span>
                  </div>
                  <p className="text-muted text-xs mt-1">Severity score: {d.severity_score}/100</p>
                </div>
              ))}
            </div>
            <div>
              <p className="text-sm font-semibold mb-2">What Can Be Fixed</p>
              <p className="text-xs text-muted border border-line rounded-md p-2 mb-2 bg-amber/5">
                Suggested next steps for your team — the tool detects and scores defects, it does not edit the image.
              </p>
              {fixes.length === 0 && <p className="text-pass text-sm">Nothing to fix.</p>}
              {fixes.map((f, i) => (
                <div key={i} className="card p-3 mb-2">
                  <div className="flex justify-between items-center">
                    <span className="capitalize font-semibold text-sm">{f.defect_type}</span>
                    <span className={`badge badge-${f.severity_level}`}>{f.severity_level}</span>
                  </div>
                  <p className="text-xs text-muted mt-2"><strong className="text-ink">Likely cause:</strong> {f.likely_cause}</p>
                  <p className="text-xs mt-1"><strong>Suggested fix:</strong> {f.suggested_fix}</p>
                  <p className="text-xs mt-1 text-amber font-medium">{f.required_action}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
