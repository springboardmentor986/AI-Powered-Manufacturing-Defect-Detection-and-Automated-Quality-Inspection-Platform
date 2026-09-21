import { InspectionStatus, SeverityLevel } from "@/lib/types";

export function StatusBadge({ status }: { status: InspectionStatus }) {
  const label = status === "pass" ? "Pass" : status === "fail" ? "Fail" : status === "review" ? "Review" : "Pending";
  return <span className={`badge badge-${status}`}>{label}</span>;
}

export function SeverityBadge({ level }: { level: SeverityLevel | null | undefined }) {
  if (!level || level === "none") {
    return <span className="badge badge-low">None</span>;
  }
  return <span className={`badge badge-${level}`}>{level}</span>;
}
