# ==========================================
# Inspection History
# ==========================================

inspection_history = []


def add_inspection(report):
    """
    Store a completed inspection report.
    """

    inspection_history.append(report)

    return report


def get_inspections():
    """
    Return all inspection reports.
    """

    return inspection_history


def get_statistics():
    """
    Calculate basic inspection statistics.
    """

    total = len(inspection_history)

    good = 0
    defect = 0

    for report in inspection_history:

        if report["prediction"] == "GOOD":
            good += 1

        elif report["prediction"] == "DEFECT":
            defect += 1

    return {
        "total_inspections": total,
        "good_products": good,
        "defective_products": defect
    }