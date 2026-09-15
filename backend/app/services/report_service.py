import csv
import io
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.image import Image


def generate_production_quality_report_csv(db: Session) -> str:
    """
    Generates a structured Production Quality Report in CSV format
    containing both executive summary metrics and granular inspection records.
    """
    inspected_records = (
        db.query(Image)
        .filter(Image.severity_score.isnot(None))
        .order_by(Image.id.asc())
        .all()
    )

    total_inspections = len(inspected_records)
    accepted_count = sum(
        1 for img in inspected_records if img.quality_decision == "Accept"
    )
    rejected_count = sum(
        1 for img in inspected_records if img.quality_decision == "Reject"
    )
    pass_yield = (
        (accepted_count / total_inspections * 100.0)
        if total_inspections > 0
        else 0.0
    )
    defect_rate = (
        (rejected_count / total_inspections * 100.0)
        if total_inspections > 0
        else 0.0
    )

    sev_scores = [
        float(img.severity_score)
        for img in inspected_records
        if img.severity_score is not None and img.severity_score != ""
    ]
    avg_severity = sum(sev_scores) / len(sev_scores) if sev_scores else 0.0

    conf_scores = [
        float(img.confidence_score)
        for img in inspected_records
        if img.confidence_score is not None and img.confidence_score != ""
    ]
    avg_confidence = sum(conf_scores) / len(conf_scores) if conf_scores else 0.0

    pending_reviews = sum(
        1
        for img in inspected_records
        if not img.supervisor_decision or img.supervisor_decision == "pending"
    )
    approved_reviews = sum(
        1 for img in inspected_records if img.supervisor_decision == "approved"
    )
    rejected_reviews = sum(
        1 for img in inspected_records if img.supervisor_decision == "rejected"
    )

    gen_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    output = io.StringIO()
    writer = csv.writer(output)

    # REPORT SUMMARY
    writer.writerow(["PRODUCTION QUALITY REPORT SUMMARY"])
    writer.writerow(["Metric", "Value"])
    writer.writerow(["Report Generation Timestamp", gen_timestamp])
    writer.writerow(["Total Inspections", total_inspections])
    writer.writerow(["Accepted Count", accepted_count])
    writer.writerow(["Rejected Count", rejected_count])
    writer.writerow(["Pass/Yield Percentage", f"{pass_yield:.2f}%"])
    writer.writerow(["Defect Rate", f"{defect_rate:.2f}%"])
    writer.writerow(["Average Severity Score", f"{avg_severity:.2f}"])
    writer.writerow(["Average Confidence", f"{avg_confidence:.2f}%"])
    writer.writerow(["Pending Supervisor Reviews", pending_reviews])
    writer.writerow(["Approved Supervisor Reviews", approved_reviews])
    writer.writerow(["Rejected Supervisor Reviews", rejected_reviews])
    writer.writerow([])

    # INSPECTION RECORDS
    writer.writerow(["INSPECTION RECORDS"])
    writer.writerow([
        "Inspection ID",
        "Timestamp",
        "Original Filename",
        "Category",
        "Defect Type",
        "Classification Confidence",
        "Anomaly Score",
        "Predicted Area Percentage",
        "Size Score",
        "Location Score",
        "Defect Type Score",
        "Severity Score",
        "Severity Level",
        "AI Quality Decision",
        "Supervisor Decision",
        "Supervisor Notes",
        "Reviewer ID",
        "Review Timestamp",
    ])

    for img in inspected_records:
        writer.writerow([
            img.id,
            img.uploaded_at.isoformat() if img.uploaded_at else "",
            img.original_filename,
            img.category or "",
            img.defect_type or "",
            img.classification_confidence or "",
            img.anomaly_score or "",
            img.predicted_area_percent or "",
            img.size_score or "",
            img.location_score or "",
            img.defect_type_score or "",
            img.severity_score or "",
            img.severity_level or "",
            img.quality_decision or "",
            img.supervisor_decision or "",
            img.supervisor_notes or "",
            img.reviewed_by if img.reviewed_by is not None else "",
            img.reviewed_at.isoformat() if img.reviewed_at else "",
        ])

    return output.getvalue()
