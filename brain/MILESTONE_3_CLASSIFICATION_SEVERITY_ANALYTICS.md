# Milestone 3: Week 5 & 6 — Defect Classification & Manufacturing Analytics

## 1. Objectives & Scope
Transform visual defect detections into actionable quality control intelligence:
- Implement defect categorization workflows (e.g., surface scratches, structural cracks, missing components, contaminations).
- Compute 4-parameter weighted severity scores adhering strictly to project specifications.
- Automate Pass/Fail/Review decisions based on quality threshold rules.
- Deliver executive manufacturing analytics dashboards with real-time yield KPIs, scrap rates, and trend monitoring.

---

## 2. 4-Factor Severity Scoring Framework
Defect severity is calculated mathematically using:

$$\text{Severity Score} = (\text{Defect Size} \times 30\%) + (\text{Defect Location} \times 25\%) + (\text{Defect Type} \times 25\%) + (\text{Detection Confidence} \times 20\%)$$

### Parameter Weights:
- **Defect Size (30%)**: Physical area occupied by the anomaly relative to the product surface (Small scratch = Low, Large crack = High).
- **Defect Location (25%)**: Critical functional area vs cosmetic surface area.
- **Defect Type (25%)**: Structural flaw (Crack/Breakage = High) vs Cosmetic variation (Color smudge = Low).
- **Detection Confidence (20%)**: Model certainty (>95% = High reliability, <70% = Requires operator review).

---

## 3. Severity Levels & Automated Actions
| Severity Score | Level | Operational Interpretation | Automated System Decision |
| :--- | :--- | :--- | :--- |
| **0 – 39** | **Low** | Minor cosmetic defect; product generally acceptable | **PASS** (Release to downstream assembly) |
| **40 – 59** | **Medium** | Moderate quality concern; requires review | **REVIEW** (Send to supervisor triage queue) |
| **60 – 79** | **High** | Significant quality issue; repair or rework | **FAIL** (Route to rework station) |
| **80 – 100** | **Critical** | Major structural defect; product rejection required | **FAIL & SCRAP** (Trigger plant alert) |

---

## 4. Manufacturing Quality Analytics Dashboard
- **Plant Quality Yield (%)**: $\frac{\text{Passed Inspections}}{\text{Total Inspections}} \times 100$
- **Critical Rejection Rate (%)**: $\frac{\text{Failed / Scrapped Inspections}}{\text{Total Inspections}} \times 100$
- **15-Category MVTec Benchmark Matrix**: Cross-category quality comparison.
- **Tamper-Evident Audit Trail**: Complete traceability of all inspection verdicts and operator overrides.
