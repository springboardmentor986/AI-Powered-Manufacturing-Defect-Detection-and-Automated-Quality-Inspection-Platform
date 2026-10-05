import sqlite3
from collections import Counter
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "visioninspect.db"


def get_analytics():
    """
    Read-only manufacturing analytics.
    Does not modify the database.
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        cursor = conn.cursor()

        # ---------------------------------------------------------
        # Basic inspection statistics
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT
                COUNT(*) AS total_inspections,
                SUM(CASE WHEN status = 'NORMAL' THEN 1 ELSE 0 END) AS normal,
                SUM(CASE WHEN status = 'DEFECTIVE' THEN 1 ELSE 0 END) AS defective
            FROM inspections
        """)

        stats = cursor.fetchone()

        total = stats["total_inspections"] or 0
        normal = stats["normal"] or 0
        defective = stats["defective"] or 0

        defect_rate = round((defective / total) * 100, 2) if total else 0
        normal_rate = round((normal / total) * 100, 2) if total else 0

        # ---------------------------------------------------------
        # Defect distribution
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT defect_type, COUNT(*) AS count
            FROM inspections
            WHERE defect_type IS NOT NULL
              AND defect_type != ''
            GROUP BY defect_type
            ORDER BY count DESC
        """)

        defect_distribution = {
            row["defect_type"]: row["count"]
            for row in cursor.fetchall()
        }

        # ---------------------------------------------------------
        # Severity distribution
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT severity_level, COUNT(*) AS count
            FROM inspections
            WHERE severity_level IS NOT NULL
              AND severity_level != ''
            GROUP BY severity_level
        """)

        severity_distribution = {
            row["severity_level"]: row["count"]
            for row in cursor.fetchall()
        }

        # ---------------------------------------------------------
        # Risk distribution
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT risk_level, COUNT(*) AS count
            FROM inspections
            WHERE risk_level IS NOT NULL
              AND risk_level != ''
            GROUP BY risk_level
        """)

        risk_distribution = {
            row["risk_level"]: row["count"]
            for row in cursor.fetchall()
        }

        # ---------------------------------------------------------
        # Daily inspection trend
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT
                DATE(upload_time) AS date,
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'NORMAL' THEN 1 ELSE 0 END) AS normal,
                SUM(CASE WHEN status = 'DEFECTIVE' THEN 1 ELSE 0 END) AS defective
            FROM inspections
            GROUP BY DATE(upload_time)
            ORDER BY DATE(upload_time)
        """)

        daily_trend = []

        for row in cursor.fetchall():
            daily_trend.append({
                "date": row["date"],
                "total": row["total"] or 0,
                "normal": row["normal"] or 0,
                "defective": row["defective"] or 0
            })

        # ---------------------------------------------------------
        # Defect trend by date
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT
                DATE(upload_time) AS date,
                defect_type,
                COUNT(*) AS count
            FROM inspections
            WHERE defect_type IS NOT NULL
              AND defect_type != ''
              AND defect_type != 'No Defect'
            GROUP BY DATE(upload_time), defect_type
            ORDER BY DATE(upload_time)
        """)

        defect_trend = []

        for row in cursor.fetchall():
            defect_trend.append({
                "date": row["date"],
                "defect_type": row["defect_type"],
                "count": row["count"]
            })

        # ---------------------------------------------------------
        # Average quality score
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT
                ROUND(AVG(quality_score), 2) AS average_quality_score
            FROM inspections
            WHERE quality_score IS NOT NULL
        """)

        quality = cursor.fetchone()

        average_quality_score = (
            quality["average_quality_score"]
            if quality["average_quality_score"] is not None
            else 0
        )

        # ---------------------------------------------------------
        # Average severity score
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT
                ROUND(AVG(severity_score), 2) AS average_severity_score
            FROM inspections
            WHERE severity_score IS NOT NULL
        """)

        severity = cursor.fetchone()

        average_severity_score = (
            severity["average_severity_score"]
            if severity["average_severity_score"] is not None
            else 0
        )

        # ---------------------------------------------------------
        # Final analytics result
        # ---------------------------------------------------------
        return {
            "total_inspections": total,
            "normal": normal,
            "defective": defective,
            "normal_rate": normal_rate,
            "defect_rate": defect_rate,
            "average_quality_score": average_quality_score,
            "average_severity_score": average_severity_score,
            "defect_distribution": defect_distribution,
            "severity_distribution": severity_distribution,
            "risk_distribution": risk_distribution,
            "daily_trend": daily_trend,
            "defect_trend": defect_trend
        }

    finally:
        conn.close()