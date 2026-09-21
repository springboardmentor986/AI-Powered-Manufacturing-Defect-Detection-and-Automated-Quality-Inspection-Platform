"use client";

import { useState } from "react";
import Link from "next/link";
import ProtectedPage from "@/components/ProtectedPage";
import api from "@/lib/api";
import { InspectionImage } from "@/lib/types";
import { StatusBadge, SeverityBadge } from "@/components/Badges";

function UploadContent() {
  const [files, setFiles] = useState<File[]>([]);
  const [productLine, setProductLine] = useState("");
  const [batchId, setBatchId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<InspectionImage[]>([]);

  function handleFilePick(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (files.length === 0) {
      setError("Select at least one image to inspect.");
      return;
    }
    setError(null);
    setBusy(true);
    setResults([]);
    try {
      const form = new FormData();
      if (files.length === 1) {
        form.append("file", files[0]);
        if (productLine) form.append("product_line", productLine);
        if (batchId) form.append("batch_id", batchId);
        const res = await api.post("/api/images/upload", form, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        setResults([res.data]);
      } else {
        files.forEach((f) => form.append("files", f));
        if (productLine) form.append("product_line", productLine);
        if (batchId) form.append("batch_id", batchId);
        const res = await api.post("/api/images/upload-batch", form, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        setResults(res.data);
      }
      setFiles([]);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Upload failed. Check the file type and try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="mb-7">
        <p className="eyebrow mb-1">Image Acquisition</p>
        <h1 className="font-display text-2xl font-semibold">Upload &amp; Inspect</h1>
        <p className="text-sm text-muted mt-1">
          Upload one or more product images for automated defect detection and severity scoring.
        </p>
      </div>

      <div className="card px-6 py-6 mb-8">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs text-muted mb-1.5">Product image(s)</label>
            <input
              type="file"
              multiple
              accept=".jpg,.jpeg,.png,.bmp,.tiff,.tif,.webp"
              onChange={handleFilePick}
              className="input-field file:mr-3 file:py-1.5 file:px-3 file:rounded file:border-0 file:bg-panel-2 file:text-ink file:text-xs"
            />
            {files.length > 0 && (
              <p className="text-xs text-muted mt-1.5">
                {files.length} file{files.length > 1 ? "s" : ""} selected
              </p>
            )}
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-muted mb-1.5">Product line (optional)</label>
              <input
                className="input-field"
                placeholder="e.g. Line-A"
                value={productLine}
                onChange={(e) => setProductLine(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs text-muted mb-1.5">Batch ID (optional)</label>
              <input
                className="input-field"
                placeholder="e.g. BATCH-2026-09-10"
                value={batchId}
                onChange={(e) => setBatchId(e.target.value)}
              />
            </div>
          </div>
          {error && <p className="text-sm text-critical">{error}</p>}
          <button type="submit" disabled={busy} className="btn-primary">
            {busy ? "Running inspection pipeline…" : "Upload & Inspect"}
          </button>
        </form>
      </div>

      {results.length > 0 && (
        <div className="space-y-4">
          <p className="text-sm font-medium">Inspection Results</p>
          {results.map((r) => (
            <div key={r.id} className="card px-5 py-4">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <p className="font-mono text-sm">{r.filename}</p>
                  <p className="text-xs text-muted">
                    {r.width}×{r.height}px · {r.defects.length} defect{r.defects.length !== 1 ? "s" : ""} found
                  </p>
                </div>
                <StatusBadge status={r.status} />
              </div>
              {r.defects.length === 0 ? (
                <p className="text-sm text-pass">No defects detected — surface clean.</p>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-muted text-xs uppercase border-b border-line">
                      <th className="pb-2 font-medium">Type</th>
                      <th className="pb-2 font-medium">Severity Score</th>
                      <th className="pb-2 font-medium">Level</th>
                    </tr>
                  </thead>
                  <tbody>
                    {r.defects.map((d) => (
                      <tr key={d.id} className="border-b border-line/50 last:border-0">
                        <td className="py-2 capitalize">{d.defect_type}</td>
                        <td className="py-2 font-mono">{d.severity_score.toFixed(1)}</td>
                        <td className="py-2">
                          <SeverityBadge level={d.severity_level} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
              <Link href={`/inspections/${r.id}`} className="text-xs text-amber hover:underline mt-3 inline-block">
                View full detail & annotated image →
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function UploadPage() {
  return (
    <ProtectedPage>
      <UploadContent />
    </ProtectedPage>
  );
}
