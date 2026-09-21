"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import ProtectedPage from "@/components/ProtectedPage";
import api from "@/lib/api";
import { InspectionImage } from "@/lib/types";
import { StatusBadge, SeverityBadge } from "@/components/Badges";

function InspectionDetailContent() {
  const params = useParams();
  const id = params?.id;
  const [inspection, setInspection] = useState<InspectionImage | null>(null);
  const [loading, setLoading] = useState(true);
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    if (!id) return;
    api
      .get(`/api/inspections/${id}`)
      .then((res) => setInspection(res.data))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p className="text-sm text-muted">Loading…</p>;
  if (!inspection) return <p className="text-sm text-critical">Inspection not found.</p>;

  return (
    <div>
      <div className="mb-6 flex items-start justify-between">
        <div>
          <p className="eyebrow mb-1">Inspection #{inspection.id}</p>
          <h1 className="font-display text-2xl font-semibold font-mono">{inspection.filename}</h1>
          <p className="text-sm text-muted mt-1">
            {inspection.width}×{inspection.height}px · uploaded{" "}
            {new Date(inspection.uploaded_at).toLocaleString()}
            {inspection.product_line ? ` · Line: ${inspection.product_line}` : ""}
            {inspection.batch_id ? ` · Batch: ${inspection.batch_id}` : ""}
          </p>
        </div>
        <StatusBadge status={inspection.status} />
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="card px-5 py-4">
          <p className="text-sm font-medium mb-3">Annotated Image</p>
          <img
            src={`${apiUrl}/api/images/${inspection.id}/annotated`}
            alt={inspection.filename}
            className="w-full rounded border border-line"
          />
          <p className="text-xs text-muted mt-2">
            Bounding boxes are colored by severity level (critical → red, high → orange, medium → teal, low → green).
          </p>
        </div>

        <div className="card px-5 py-4">
          <p className="text-sm font-medium mb-3">
            Detected Defects ({inspection.defects.length})
          </p>
          {inspection.defects.length === 0 ? (
            <p className="text-sm text-pass">No defects detected — product passed inspection.</p>
          ) : (
            <div className="space-y-3">
              {inspection.defects.map((d) => (
                <div key={d.id} className="border border-line rounded p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="capitalize font-medium text-sm">{d.defect_type}</span>
                    <SeverityBadge level={d.severity_level} />
                  </div>
                  <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-muted font-mono">
                    <span>Size score: {d.size_score.toFixed(1)}</span>
                    <span>Location score: {d.location_score.toFixed(1)}</span>
                    <span>Type score: {d.type_score.toFixed(1)}</span>
                    <span>Confidence: {d.confidence_score.toFixed(1)}%</span>
                    <span className="col-span-2 text-ink">
                      Severity Score: {d.severity_score.toFixed(1)} / 100
                    </span>
                    <span className="col-span-2">
                      BBox: ({d.bbox_x}, {d.bbox_y}) {d.bbox_w}×{d.bbox_h}px · area {d.area_px}px²
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function InspectionDetailPage() {
  return (
    <ProtectedPage>
      <InspectionDetailContent />
    </ProtectedPage>
  );
}
