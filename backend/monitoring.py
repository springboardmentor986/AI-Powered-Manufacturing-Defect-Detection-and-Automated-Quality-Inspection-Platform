from fastapi import APIRouter

from backend.inspection_history import (
    get_inspections,
    get_statistics
)

from backend.analytics import (
    get_defect_analytics
)


router = APIRouter()


# ==========================================
# Inspection History
# ==========================================

@router.get("/inspections")
def inspections():

    return {
        "message": "Inspection history retrieved successfully",
        "inspections": get_inspections()
    }


# ==========================================
# Inspection Statistics
# ==========================================

@router.get("/inspection-statistics")
def inspection_statistics():

    return {
        "message": "Inspection statistics retrieved successfully",
        "statistics": get_statistics()
    }


# ==========================================
# Defect Analytics
# ==========================================

@router.get("/defect-analytics")
def defect_analytics():

    return {
        "message": "Defect analytics retrieved successfully",
        "analytics": get_defect_analytics()
    }