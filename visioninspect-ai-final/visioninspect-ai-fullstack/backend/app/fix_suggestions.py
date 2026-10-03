"""
Ported from the client-side app: for each detected defect, suggest a likely
cause and a corrective action. This does NOT edit the image - it only
recommends next steps for the quality team, same as the "What Can Be Fixed"
column in the single-file demo.
"""
FIX_SUGGESTIONS = {
    "crack":         {"cause": "material stress, poor curing, or handling damage",
                       "fix": "Weld, seal, or replace the part depending on crack depth."},
    "scratch":       {"cause": "handling, packaging friction, or tooling contact",
                       "fix": "Buff or repaint the surface; re-inspect the finish."},
    "dent":          {"cause": "impact during handling, transit, or assembly",
                       "fix": "Panel-beat / reshape the area, or replace if it is structural."},
    "contamination": {"cause": "dust, oil, or residue picked up from an upstream step",
                       "fix": "Clean or re-wash the surface, then re-inspect."},
}
SEVERITY_ACTION = {
    "critical": "Stop the line - scrap or send to rework immediately.",
    "high":     "Send to rework before this unit ships.",
    "medium":   "Rework recommended before shipping.",
    "low":      "Cosmetic only - rework optional, monitor the trend.",
}

def suggest_fix(defect_type: str, severity_level: str) -> dict:
    s = FIX_SUGGESTIONS.get(defect_type, {"cause": "an unclassified defect pattern",
                                           "fix": "Inspect manually and rework as needed."})
    return {
        "defect_type": defect_type,
        "severity_level": severity_level,
        "likely_cause": s["cause"],
        "suggested_fix": s["fix"],
        "required_action": SEVERITY_ACTION.get(severity_level, "Review manually."),
    }
