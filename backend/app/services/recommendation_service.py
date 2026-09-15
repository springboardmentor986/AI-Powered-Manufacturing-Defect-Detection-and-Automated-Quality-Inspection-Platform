from typing import Any, Dict, Optional


def get_quality_recommendation(
    defect_type: Optional[str],
    quality_decision: Optional[str],
    severity_level: Optional[str] = None,
    severity_score: Optional[Any] = None,
) -> Dict[str, str]:
    """
    Pure deterministic downstream recommendation function mapping
    inspection results to shop-floor quality guidance (PASS, CLEAN, REWORK, SCRAP).
    """
    if quality_decision is None and defect_type is None:
        return {
            "action": "PENDING",
            "action_label": "Pending Inspection",
            "rationale": "AI inspection has not yet been executed for this image.",
            "guidance": "Run AI inspection to generate automated quality recommendations.",
        }

    dt = (defect_type or "").lower().strip()
    decision = (quality_decision or "").strip()
    sev_level = (severity_level or "").strip()

    # A. PASS
    if decision == "Accept" or dt in ("normal", "good", "none", "ok"):
        return {
            "action": "PASS",
            "action_label": "Pass to Production",
            "rationale": "Part satisfies inspection criteria with acceptable quality metrics.",
            "guidance": "No corrective action required. Proceed according to the normal production workflow.",
        }

    # If quality_decision == "Reject":
    # B. CLEAN
    clean_types = ["contamination", "stain", "glue", "color"]
    if any(k in dt for k in clean_types):
        return {
            "action": "CLEAN",
            "action_label": "Clean & Re-inspect",
            "rationale": f"Surface {defect_type or 'contamination'} detected without irreversible structural damage.",
            "guidance": "Remove the identified surface contamination or residue using the approved cleaning process, then re-inspect the part.",
        }

    # C. REWORK
    rework_types = [
        "cut_outer_insulation",
        "bent_wire",
        "bent",
        "scratch",
        "rough",
        "deformation",
        "misplaced",
    ]
    if any(k in dt for k in rework_types):
        return {
            "action": "REWORK",
            "action_label": "Route for Rework",
            "rationale": f"Non-critical geometric or surface deviation ({defect_type or 'flaw'}) capable of corrective repair.",
            "guidance": "Route the part to the approved rework process and perform a repeat inspection after rework.",
        }

    # D. SCRAP
    scrap_types = [
        "crack",
        "broken_large",
        "broken",
        "hole",
        "cut_inner_insulation",
        "cut",
    ]
    if sev_level == "Critical" or any(k in dt for k in scrap_types):
        return {
            "action": "SCRAP",
            "action_label": "Quarantine for Scrap",
            "rationale": f"Critical or irreversible structural defect ({defect_type or 'fracture'}) exceeding allowable repair limits.",
            "guidance": "Quarantine the part for scrap or engineering disposition according to the approved quality procedure.",
        }

    # E. FALLBACK
    return {
        "action": "SCRAP",
        "action_label": "Quarantine for Disposition",
        "rationale": f"Unresolved or unclassified defect ({defect_type or 'anomaly'}) requiring quality engineering evaluation.",
        "guidance": "Quarantine the part for quality/engineering disposition and do not release it without an approved decision.",
    }
