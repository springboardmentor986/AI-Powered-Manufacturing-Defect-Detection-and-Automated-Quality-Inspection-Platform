// ============================================================
// VISIONINSPECT AI
// FRONTEND CONTROLLER
// ============================================================

const API_BASE = "http://127.0.0.1:8000";

// ------------------------------------------------------------
// DOM ELEMENTS
// ------------------------------------------------------------

const imageInput = document.getElementById("imageInput");
const categorySelect = document.getElementById("categorySelect");
const analyzeBtn = document.getElementById("analyzeBtn");

const previewContainer = document.getElementById("previewContainer");
const previewImage = document.getElementById("previewImage");

const fileName = document.getElementById("fileName");
const fileSize = document.getElementById("fileSize");

const resultContent = document.getElementById("resultContent");
const inspectionHistory = document.getElementById("inspectionHistory");

const totalInspections = document.getElementById("totalInspections");
const goodProducts = document.getElementById("goodProducts");
const defectiveProducts = document.getElementById("defectiveProducts");


// ------------------------------------------------------------
// PAGE START
// ------------------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {

    loadStatistics();
    loadInspectionHistory();

});


// ------------------------------------------------------------
// IMAGE SELECTION
// ------------------------------------------------------------

if (imageInput) {

    imageInput.addEventListener("change", function () {

        const file = this.files[0];

        if (!file) {
            return;
        }

        const reader = new FileReader();

        reader.onload = function (event) {

            if (previewImage) {
                previewImage.src = event.target.result;
            }

            if (previewContainer) {
                previewContainer.classList.remove("hidden");
            }

        };

        reader.readAsDataURL(file);

        if (fileName) {
            fileName.textContent = file.name;
        }

        if (fileSize) {
            fileSize.textContent = formatFileSize(file.size);
        }

    });

}


// ------------------------------------------------------------
// ANALYZE BUTTON
// ------------------------------------------------------------

if (analyzeBtn) {

    analyzeBtn.addEventListener("click", analyzeImage);

}


// ------------------------------------------------------------
// ANALYZE IMAGE
// ------------------------------------------------------------

async function analyzeImage() {

    const file = imageInput ? imageInput.files[0] : null;
    const category = categorySelect ? categorySelect.value : "";

    if (!file) {

        showMessage(
            "Please select an image first."
        );

        return;
    }

    if (!category) {

        showMessage(
            "Please select a product category."
        );

        return;
    }


    // Loading state

    analyzeBtn.disabled = true;

    analyzeBtn.innerHTML = "⟳ AI ANALYZING...";


    if (resultContent) {

        resultContent.innerHTML = `
            <div class="result-loading">

                <div class="loading-spinner"></div>

                <h3>
                    AI Inspection Running
                </h3>

                <p>
                    VisionInspect AI is analyzing the product image...
                </p>

            </div>
        `;

    }


    try {

        const formData = new FormData();

        formData.append("category", category);
        formData.append("file", file);


        const response = await fetch(
            `${API_BASE}/upload`,
            {
                method: "POST",
                body: formData
            }
        );


        const data = await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                data.message ||
                "Inspection failed."
            );

        }


        if (
            data.inspection_report
        ) {

            displayInspectionResult(
                data.inspection_report
            );

        }


        // Refresh dashboard data

        await loadStatistics();
        await loadInspectionHistory();


    } catch (error) {

        console.error(
            "Inspection error:",
            error
        );


        if (resultContent) {

            resultContent.innerHTML = `

                <div class="result-error">

                    <h3>
                        Inspection Failed
                    </h3>

                    <p>
                        ${escapeHtml(error.message)}
                    </p>

                </div>

            `;

        }

    } finally {

        analyzeBtn.disabled = false;

        analyzeBtn.innerHTML =
            "🔍 Analyze Image";

    }

}


// ------------------------------------------------------------
// DISPLAY INSPECTION RESULT
// ------------------------------------------------------------

function displayInspectionResult(report) {

    if (!resultContent) {
        return;
    }


    const isDefect =
        report.prediction === "DEFECT";


    const severity =
        report.severity_report || {};


    const risk =
        report.risk_report || {};


    const quality =
        report.quality_report || {};


    const resultClass =
        isDefect
            ? "anomaly"
            : "good";


    const resultTitle =
        isDefect
            ? "ANOMALY DETECTED"
            : "PRODUCT PASSED";


    const defectType =
        report.defect_type
            ? formatText(report.defect_type)
            : "No defect detected";


    resultContent.innerHTML = `

        <div class="result-live">

            <div class="result-status ${resultClass}">

                <span class="status-dot"></span>

                <strong>
                    ${resultTitle}
                </strong>

            </div>


            <h3>
                ${isDefect
            ? defectType
            : "GOOD PRODUCT"
        }
            </h3>


            <p class="result-description">

                ${isDefect
            ? "The AI detected a visual anomaly in the inspected product."
            : "The AI found no significant visual anomaly in the inspected product."
        }

            </p>


            <div class="result-id">

                Inspection ID:
                <strong>
                    ${escapeHtml(report.inspection_id)}
                </strong>

            </div>


            <div class="result-grid">


                <div class="result-metric">

                    <span>
                        Category
                    </span>

                    <strong>
                        ${formatText(report.category)}
                    </strong>

                </div>


                <div class="result-metric">

                    <span>
                        Anomaly Score
                    </span>

                    <strong>
                        ${report.anomaly_score ?? "--"}
                    </strong>

                </div>


                <div class="result-metric">

                    <span>
                        Threshold
                    </span>

                    <strong>
                        ${report.threshold ?? "--"}
                    </strong>

                </div>


                <div class="result-metric">

                    <span>
                        Confidence
                    </span>

                    <strong>
                        ${severity.confidence_score !== undefined
            ? severity.confidence_score + "%"
            : "--"
        }
                    </strong>

                </div>


                <div class="result-metric">

                    <span>
                        Severity
                    </span>

                    <strong class="severity-value">
                        ${severity.severity_level
            ? formatText(severity.severity_level)
            : "NORMAL"
        }
                    </strong>

                </div>


                <div class="result-metric">

                    <span>
                        Risk
                    </span>

                    <strong>
                        ${risk.risk_level
            ? formatText(risk.risk_level)
            : "LOW"
        }
                    </strong>

                </div>


            </div>


            <div class="product-decision">

                <span>
                    PRODUCT STATUS
                </span>

                <strong>
                    ${escapeHtml(report.product_status || "--")}
                </strong>

            </div>


            ${isDefect
            ? `
                        <div class="recommendation">

                            <span>
                                RECOMMENDED ACTION
                            </span>

                            <strong>
                                ${escapeHtml(
                risk.recommended_action || "REVIEW"
            )}
                            </strong>

                        </div>
                    `
            : ""
        }


            <div class="quality-section">

                <h4>
                    IMAGE QUALITY
                </h4>


                <div class="quality-row">

                    <span>
                        Status
                    </span>

                    <strong>
                        ${escapeHtml(
            quality.quality_status || "--"
        )}
                    </strong>

                </div>


                <div class="quality-row">

                    <span>
                        Resolution
                    </span>

                    <strong>
                        ${quality.resolution
            ? `${quality.resolution.width} × ${quality.resolution.height}`
            : "--"
        }
                    </strong>

                </div>


                <div class="quality-row">

                    <span>
                        Brightness
                    </span>

                    <strong>
                        ${quality.brightness ?? "--"}
                    </strong>

                </div>


                <div class="quality-row">

                    <span>
                        Contrast
                    </span>

                    <strong>
                        ${quality.contrast ?? "--"}
                    </strong>

                </div>


                <div class="quality-row">

                    <span>
                        Sharpness
                    </span>

                    <strong>
                        ${quality.sharpness ?? "--"}
                    </strong>

                </div>

            </div>

        </div>

    `;

}


// ------------------------------------------------------------
// LOAD INSPECTION HISTORY
// ------------------------------------------------------------

async function loadInspectionHistory() {

    if (!inspectionHistory) {
        return;
    }


    try {

        const response = await fetch(
            `${API_BASE}/inspections`
        );


        if (!response.ok) {

            throw new Error(
                "Could not load inspection history."
            );

        }


        const data =
            await response.json();


        const inspections =
            data.inspections || [];


        renderInspectionHistory(
            inspections
        );


    } catch (error) {

        console.error(
            "History error:",
            error
        );


        inspectionHistory.innerHTML = `

            <tr>

                <td
                    colspan="6"
                    class="empty-history"
                >
                    Unable to load inspection history
                </td>

            </tr>

        `;

    }

}


// ------------------------------------------------------------
// RENDER INSPECTION HISTORY
// ------------------------------------------------------------

function renderInspectionHistory(
    inspections
) {

    if (!inspectionHistory) {
        return;
    }


    // Newest first

    const sorted =
        [...inspections].reverse();


    if (sorted.length === 0) {

        inspectionHistory.innerHTML = `

            <tr>

                <td
                    colspan="6"
                    class="empty-history"
                >
                    NO INSPECTIONS IN CURRENT SESSION
                </td>

            </tr>

        `;

        return;
    }


    // Show latest 10

    const recent =
        sorted.slice(0, 10);


    inspectionHistory.innerHTML =
        recent.map(
            inspection => {

                const isDefect =
                    inspection.prediction === "DEFECT";


                const resultClass =
                    isDefect
                        ? "anomaly"
                        : "good";


                const resultText =
                    isDefect
                        ? "DEFECT"
                        : "GOOD";


                const severity =
                    inspection.severity_report
                        ? inspection.severity_report.severity_level
                        : "—";


                const filename =
                    inspection.filename || "—";


                const category =
                    inspection.category || "—";


                const anomalyScore =
                    inspection.anomaly_score !== undefined
                        ? Number(
                            inspection.anomaly_score
                        ).toFixed(4)
                        : "—";


                return `

                    <tr>

                        <td>

                            <div class="image-placeholder">

                                ${isDefect ? "!" : "✓"}

                            </div>

                        </td>


                        <td>
                            ${escapeHtml(filename)}
                        </td>


                        <td>
                            ${formatText(category)}
                        </td>


                        <td>
                            ${anomalyScore}
                        </td>


                        <td>

                            <span
                                class="badge ${resultClass}"
                            >

                                ${resultText}

                            </span>

                        </td>


                        <td>

                            ${severity !== "—"
                        ? formatText(severity)
                        : "Completed"
                    }

                        </td>

                    </tr>

                `;

            }
        ).join("");

}


// ------------------------------------------------------------
// LOAD DASHBOARD STATISTICS
// ------------------------------------------------------------

async function loadStatistics() {

    try {

        const response = await fetch(
            `${API_BASE}/inspection-statistics`
        );


        if (!response.ok) {
            throw new Error(
                "Statistics unavailable"
            );
        }


        const data =
            await response.json();


        const stats =
            data.statistics || {};


        if (totalInspections) {

            totalInspections.textContent =
                stats.total_inspections ?? 0;

        }


        if (goodProducts) {

            goodProducts.textContent =
                stats.good_products ?? 0;

        }


        if (defectiveProducts) {

            defectiveProducts.textContent =
                stats.defective_products ?? 0;

        }


    } catch (error) {

        console.error(
            "Statistics error:",
            error
        );

    }

}


// ------------------------------------------------------------
// HELPER — FORMAT FILE SIZE
// ------------------------------------------------------------

function formatFileSize(bytes) {

    if (!bytes) {
        return "0 KB";
    }


    const kb =
        bytes / 1024;


    if (kb < 1024) {

        return `${kb.toFixed(1)} KB`;

    }


    return `${(
        kb / 1024
    ).toFixed(2)} MB`;

}


// ------------------------------------------------------------
// HELPER — FORMAT TEXT
// ------------------------------------------------------------

function formatText(value) {

    if (
        value === undefined ||
        value === null ||
        value === ""
    ) {

        return "—";

    }


    return String(value)
        .replaceAll("_", " ")
        .replace(/\b\w/g, char =>
            char.toUpperCase()
        );

}


// ------------------------------------------------------------
// HELPER — ESCAPE HTML
// ------------------------------------------------------------

function escapeHtml(value) {

    if (
        value === undefined ||
        value === null
    ) {

        return "";

    }


    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}


// ------------------------------------------------------------
// SIMPLE MESSAGE
// ------------------------------------------------------------

function showMessage(message) {

    if (!resultContent) {
        alert(message);
        return;
    }


    resultContent.innerHTML = `

        <div class="result-error">

            <h3>
                Action Required
            </h3>

            <p>
                ${escapeHtml(message)}
            </p>

        </div>

    `;

}