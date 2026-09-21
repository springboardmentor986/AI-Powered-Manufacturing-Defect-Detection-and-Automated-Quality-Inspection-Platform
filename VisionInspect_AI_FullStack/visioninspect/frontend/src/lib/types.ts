export type UserRole =
  | "admin"
  | "quality_engineer"
  | "factory_supervisor"
  | "production_manager";

export interface User {
  id: number;
  full_name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export type SeverityLevel = "critical" | "high" | "medium" | "low" | "none";
export type InspectionStatus = "pending" | "pass" | "fail" | "review";

export interface DefectRecord {
  id: number;
  defect_type: string;
  bbox_x: number;
  bbox_y: number;
  bbox_w: number;
  bbox_h: number;
  area_px: number;
  size_score: number;
  location_score: number;
  type_score: number;
  confidence_score: number;
  severity_score: number;
  severity_level: SeverityLevel;
}

export interface InspectionImage {
  id: number;
  filename: string;
  product_line: string | null;
  batch_id: string | null;
  uploaded_at: string;
  width: number | null;
  height: number | null;
  status: InspectionStatus;
  processed: boolean;
  defects: DefectRecord[];
}

export interface InspectionSummary {
  id: number;
  filename: string;
  status: InspectionStatus;
  uploaded_at: string;
  defect_count: number;
  max_severity: SeverityLevel | null;
}

export interface AnalyticsSummary {
  total_images: number;
  total_defects: number;
  pass_count: number;
  fail_count: number;
  review_count: number;
  pass_rate: number;
  defect_type_breakdown: { defect_type: string; count: number }[];
  severity_breakdown: { severity_level: string; count: number }[];
  trend: {
    date: string;
    total_inspections: number;
    total_defects: number;
    fail_count: number;
    pass_count: number;
  }[];
}
