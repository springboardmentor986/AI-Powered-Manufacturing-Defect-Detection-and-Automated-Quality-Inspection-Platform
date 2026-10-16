from collections import Counter
from datetime import datetime

from backend.inspection_history import get_inspections


def get_defect_analytics():
    inspections = get_inspections()

    total_inspections = len(inspections)
    good_products = 0
    defective_products = 0

    defect_types = Counter()
    severity_levels = Counter()
    risk_levels = Counter()

    # Trend monitoring
    daily_trend = {}

    for inspection in inspections:

        prediction = inspection.get("prediction")

        if prediction == "GOOD":
            good_products += 1

        elif prediction == "DEFECT":
            defective_products += 1

        # Defect type
        defect_type = inspection.get("defect_type")

        if defect_type:
            defect_types[defect_type] += 1

        # Severity
        severity_report = inspection.get("severity_report")

        if severity_report:
            severity_level = severity_report.get("severity_level")

            if severity_level:
                severity_levels[severity_level] += 1

        # Risk
        risk_report = inspection.get("risk_report")

        if risk_report:
            risk_level = risk_report.get("risk_level")

            if risk_level:
                risk_levels[risk_level] += 1

        # -----------------------------
        # TREND MONITORING
        # -----------------------------

        inspection_time = inspection.get("inspection_time")

        if inspection_time:

            try:
                date_value = datetime.fromisoformat(
                    inspection_time
                ).strftime("%Y-%m-%d")

                if date_value not in daily_trend:
                    daily_trend[date_value] = {
                        "total_inspections": 0,
                        "good_products": 0,
                        "defective_products": 0
                    }

                daily_trend[date_value]["total_inspections"] += 1

                if prediction == "GOOD":
                    daily_trend[date_value]["good_products"] += 1

                elif prediction == "DEFECT":
                    daily_trend[date_value]["defective_products"] += 1

            except ValueError:
                pass

    # Overall defect rate
    if total_inspections > 0:
        defect_rate = (
            defective_products / total_inspections
        ) * 100
    else:
        defect_rate = 0

    # Calculate daily defect rate
    trend_data = []

    for date_value in sorted(daily_trend.keys()):

        data = daily_trend[date_value]

        if data["total_inspections"] > 0:
            daily_defect_rate = (
                data["defective_products"]
                / data["total_inspections"]
            ) * 100
        else:
            daily_defect_rate = 0

        trend_data.append({
            "date": date_value,
            "total_inspections": data["total_inspections"],
            "good_products": data["good_products"],
            "defective_products": data["defective_products"],
            "defect_rate": round(
                daily_defect_rate,
                2
            )
        })

    return {
        "total_inspections": total_inspections,
        "good_products": good_products,
        "defective_products": defective_products,
        "defect_rate": round(
            defect_rate,
            2
        ),
        "defects_by_type": dict(
            defect_types
        ),
        "severity_distribution": dict(
            severity_levels
        ),
        "risk_distribution": dict(
            risk_levels
        ),

        # Trend monitoring output
        "trend_monitoring": {
            "daily_trend": trend_data
        }
    }