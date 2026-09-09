import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";
import {
  getCurrentUser,
  uploadImage,
  inspectImage,
  AuthError,
  ForbiddenError,
  ApiError,
} from "../services/api";

const CATEGORIES = [
  "bottle",
  "cable",
  "capsule",
  "carpet",
  "grid",
  "hazelnut",
  "leather",
  "metal_nut",
  "pill",
  "screw",
  "tile",
  "toothbrush",
  "transistor",
  "wood",
  "zipper",
];

const DEFECT_TYPES = [
  "crack",
  "hole",
  "cut",
  "scratch",
  "contamination",
  "broken",
  "bent",
  "deformation",
  "color",
  "stain",
  "rough",
  "missing",
  "misplaced",
];

function Upload() {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);

  const [category, setCategory] = useState("");
  const [defectType, setDefectType] = useState("");
  const [autoClassify, setAutoClassify] = useState(true);
  const [inspectionStep, setInspectionStep] = useState(0);

  const [uploading, setUploading] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);

  const [successData, setSuccessData] = useState(null);
  const [error, setError] = useState(null);
  const [errorType, setErrorType] = useState(null);

  const navigate = useNavigate();

  useEffect(() => {
    const checkRole = async () => {
      try {
        const userData = await getCurrentUser();

        if (userData.role_id === 2) {
          setError(
            "Factory Supervisors do not have upload privileges. Inspection image uploads are restricted to Quality Engineers."
          );
          setErrorType("forbidden");
        }
      } catch (err) {
        if (err instanceof AuthError) {
          setError(err.message);
          setErrorType("auth");
        }
      }
    };

    checkRole();
  }, []);

  const handleFileSelect = (selectedFile) => {
    setError(null);
    setSuccessData(null);

    if (!selectedFile) return;

    if (!["image/jpeg", "image/png"].includes(selectedFile.type)) {
      setError(
        "Invalid file format. Only JPEG and PNG images are supported."
      );
      setErrorType("api");
      return;
    }

    if (selectedFile.size > 5 * 1024 * 1024) {
      setError("File size exceeds maximum limit of 5 MB.");
      setErrorType("api");
      return;
    }

    setFile(selectedFile);
    setPreviewUrl(URL.createObjectURL(selectedFile));
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async (event) => {
    event.preventDefault();

    setError(null);
    setErrorType(null);
    setSuccessData(null);

    if (!autoClassify) {
      if (!category) {
        setError("Please select the product category.");
        setErrorType("api");
        return;
      }

      if (!defectType) {
        setError("Please select the defect type.");
        setErrorType("api");
        return;
      }
    }

    if (!file) {
      setError("Please select an inspection image to upload.");
      setErrorType("api");
      return;
    }

    setUploading(true);
    setInspectionStep(1);

    let stepTimer = null;

    try {
      /*
       * Step 1:
       * Store the uploaded image in the backend.
       */
      const uploadedImage = await uploadImage(file);
      setInspectionStep(2);

      stepTimer = setInterval(() => {
        setInspectionStep((prev) => (prev < 4 ? prev + 1 : prev));
      }, 600);

      /*
       * Step 2:
       * Run the real AI inspection pipeline with automatic classification.
       */
      const inspectionResult = await inspectImage(
        uploadedImage.id,
        autoClassify ? (category || null) : category,
        autoClassify ? (defectType || null) : defectType
      );

      if (stepTimer) clearInterval(stepTimer);
      setInspectionStep(5);

      /*
       * Combine upload information with the
       * actual inspection result.
       */
      setSuccessData({
        ...uploadedImage,
        inspection: inspectionResult,
      });

      setFile(null);
      setPreviewUrl(null);
      if (!autoClassify) {
        setCategory("");
        setDefectType("");
      }
    } catch (err) {
      if (stepTimer) clearInterval(stepTimer);
      if (err instanceof AuthError) {
        setError(err.message);
        setErrorType("auth");
      } else if (err instanceof ForbiddenError) {
        setError(err.message);
        setErrorType("forbidden");
      } else if (err instanceof ApiError) {
        setError(err.message);
        setErrorType("api");
      } else {
        setError(
          "Unable to complete the image inspection. Please check the backend server."
        );
        setErrorType("api");
      }
    } finally {
      setUploading(false);
      setInspectionStep(0);
    }
  };

  if (errorType === "forbidden") {
    return (
      <div className="app-shell">
        <Navbar />

        <main className="main-content">
          <div
            className="card"
            style={{ maxWidth: "600px", margin: "3rem auto" }}
          >
            <div className="card-body">
              <div
                className="state-container"
                style={{ padding: "1.5rem" }}
              >
                <div
                  className="state-icon"
                  style={{ color: "var(--danger)" }}
                >
                  🚫
                </div>

                <h2 className="state-title">Upload Restricted</h2>

                <p className="state-desc">{error}</p>

                <div style={{ marginTop: "1rem" }}>
                  <button
                    className="btn btn-primary"
                    onClick={() =>
                      navigate("/supervisor/dashboard")
                    }
                  >
                    Go to Supervisor Console
                  </button>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (errorType === "auth") {
    return (
      <div className="app-shell">
        <Navbar />

        <main className="main-content">
          <div
            className="card"
            style={{ maxWidth: "600px", margin: "3rem auto" }}
          >
            <div className="card-body">
              <div
                className="state-container"
                style={{ padding: "1.5rem" }}
              >
                <div
                  className="state-icon"
                  style={{ color: "var(--danger)" }}
                >
                  ⚠️
                </div>

                <h2 className="state-title">Session Expired</h2>

                <p className="state-desc">{error}</p>

                <div style={{ marginTop: "1rem" }}>
                  <button
                    className="btn btn-primary"
                    onClick={() => navigate("/login")}
                  >
                    Log in again
                  </button>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <Navbar />

      <main className="main-content">
        <div className="page-header">
          <div className="page-title-group">
            <h1 className="page-title">AI Image Inspection</h1>

            <p className="page-subtitle">
              Upload a manufacturing image and run the VisionInspect
              inspection pipeline.
            </p>
          </div>

          <div className="page-actions">
            <Link
              to="/dashboard"
              className="btn btn-secondary"
            >
              ← Back to Dashboard
            </Link>
          </div>
        </div>
        {error && (
          <div className="alert alert-error">
            <span>{error}</span>
          </div>
        )}

        {successData && (
          <div
            className="alert alert-success"
            style={{
              flexDirection: "column",
              gap: "1rem",
              padding: "1.25rem",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.5rem" }}>
              <div style={{ fontWeight: 700, fontSize: "1.05rem" }}>
                ✓ Image "{successData.original_filename}" Inspected Successfully
              </div>
              <span
                className={`badge ${
                  successData.inspection?.quality_decision === "Accept"
                    ? "badge-approved"
                    : "badge-rejected"
                }`}
                style={{ fontSize: "0.9rem", padding: "0.3rem 0.75rem" }}
              >
                Decision: {successData.inspection?.quality_decision || "Completed"}
              </span>
            </div>

            {/* Quick Metrics Grid */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))",
                gap: "0.75rem",
                marginTop: "0.25rem",
              }}
            >
              <div style={{ background: "rgba(255, 255, 255, 0.05)", padding: "0.6rem 0.8rem", borderRadius: "6px" }}>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>AI Category</div>
                <div style={{ fontWeight: 600, textTransform: "capitalize" }}>
                  {successData.inspection?.predicted_category || successData.inspection?.category || "—"}
                </div>
              </div>

              <div style={{ background: "rgba(255, 255, 255, 0.05)", padding: "0.6rem 0.8rem", borderRadius: "6px" }}>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>AI Defect Type</div>
                <div style={{ fontWeight: 600, textTransform: "capitalize" }}>
                  {successData.inspection?.resolved_defect_status || successData.inspection?.predicted_defect_type || successData.inspection?.defect_type || "—"}
                </div>
              </div>

              <div style={{ background: "rgba(255, 255, 255, 0.05)", padding: "0.6rem 0.8rem", borderRadius: "6px" }}>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Confidence</div>
                <div style={{ fontWeight: 600 }}>
                  {successData.inspection?.classification_confidence != null
                    ? `${Number(successData.inspection.classification_confidence).toFixed(1)}%`
                    : "—"}
                </div>
              </div>

              <div style={{ background: "rgba(255, 255, 255, 0.05)", padding: "0.6rem 0.8rem", borderRadius: "6px" }}>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Severity Level</div>
                <div style={{ fontWeight: 600 }}>
                  {successData.inspection?.severity_level || "—"}
                </div>
              </div>
            </div>

            <div
              style={{
                display: "flex",
                gap: "0.75rem",
                marginTop: "0.5rem",
              }}
            >
              <Link
                to={`/images/${successData.id}`}
                className="btn btn-sm btn-primary"
              >
                View Full Inspection #{successData.id} →
              </Link>

              <button
                type="button"
                className="btn btn-sm btn-secondary"
                onClick={() => setSuccessData(null)}
              >
                Inspect Another Sample
              </button>
            </div>
          </div>
        )}

        <div
          className="card"
          style={{ maxWidth: "720px", margin: "0 auto" }}
        >
          <div className="card-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h2 className="card-title">Inspection Sample</h2>

            <span className="badge badge-neutral">
              Max 5 MB • JPEG / PNG
            </span>
          </div>

          <div className="card-body">
            <form onSubmit={handleUpload}>
              {/* Automated AI Mode Banner / Toggle */}
              <div
                style={{
                  padding: "0.75rem 1rem",
                  background: autoClassify ? "rgba(59, 130, 246, 0.08)" : "var(--surface)",
                  borderRadius: "8px",
                  border: `1px solid ${autoClassify ? "var(--primary)" : "var(--border)"}`,
                  marginBottom: "1.25rem",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <span style={{ fontSize: "1.2rem" }}>⚡</span>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: "0.95rem" }}>
                        {autoClassify ? "Automatic AI Classification Active" : "Manual Specification Mode"}
                      </div>
                      <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                        {autoClassify
                          ? "VisionInspect AI will automatically classify product category (15 classes) and defect type."
                          : "Manually select product category and defect type below."}
                      </div>
                    </div>
                  </div>

                  <button
                    type="button"
                    className="btn btn-xs btn-secondary"
                    onClick={() => setAutoClassify(!autoClassify)}
                    disabled={uploading}
                    style={{ whiteSpace: "nowrap", marginLeft: "0.5rem" }}
                  >
                    {autoClassify ? "Switch to Manual" : "Switch to Auto AI"}
                  </button>
                </div>
              </div>

              {/* Product Category & Defect Type Dropdowns (Shown in manual mode or collapsed) */}
              {!autoClassify && (
                <div style={{ padding: "1rem", background: "var(--surface)", borderRadius: "8px", border: "1px solid var(--border)", marginBottom: "1.25rem" }}>
                  <div className="form-group">
                    <label
                      className="form-label"
                      htmlFor="category"
                    >
                      Product Category *
                    </label>

                    <select
                      id="category"
                      className="form-input"
                      value={category}
                      onChange={(e) => setCategory(e.target.value)}
                      disabled={uploading}
                    >
                      <option value="">
                        Select product category
                      </option>

                      {CATEGORIES.map((item) => (
                        <option key={item} value={item}>
                          {item.replace("_", " ").replace(/\b\w/g, (c) =>
                            c.toUpperCase()
                          )}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div
                    className="form-group"
                    style={{ marginTop: "1rem" }}
                  >
                    <label
                      className="form-label"
                      htmlFor="defectType"
                    >
                      Defect Type *
                    </label>

                    <select
                      id="defectType"
                      className="form-input"
                      value={defectType}
                      onChange={(e) => setDefectType(e.target.value)}
                      disabled={uploading}
                    >
                      <option value="">
                        Select defect type
                      </option>

                      {DEFECT_TYPES.map((item) => (
                        <option key={item} value={item}>
                          {item.replace("_", " ").replace(/\b\w/g, (c) =>
                            c.toUpperCase()
                          )}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              )}

              {/* Image Upload Dropzone */}
              <div style={{ marginTop: autoClassify ? "0" : "1rem" }}>
                <div
                  className={`dropzone ${isDragOver ? "dragover" : ""
                    }`}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  onClick={() =>
                    document
                      .getElementById("file-input")
                      ?.click()
                  }
                  style={{ cursor: uploading ? "not-allowed" : "pointer" }}
                >
                  <input
                    id="file-input"
                    type="file"
                    accept="image/jpeg,image/png"
                    onChange={(e) =>
                      handleFileSelect(e.target.files[0])
                    }
                    style={{ display: "none" }}
                    disabled={uploading}
                  />

                  <div className="dropzone-icon">📷</div>

                  <div className="dropzone-title">
                    {file
                      ? file.name
                      : "Drag and drop sensor frame, or browse"}
                  </div>

                  <div className="dropzone-hint">
                    Supports JPEG and PNG manufacturing frames up to 5 MB
                  </div>
                </div>
              </div>

              {/* Selected File Preview */}
              {file && (
                <div
                  className="preview-container"
                  style={{ marginTop: "1rem" }}
                >
                  {previewUrl && (
                    <img
                      src={previewUrl}
                      alt="Preview"
                      className="preview-image"
                    />
                  )}

                  <div className="preview-meta">
                    <div className="preview-filename">
                      {file.name}
                    </div>

                    <div className="preview-filesize">
                      {(file.size / 1024).toFixed(1)} KB •{" "}
                      {file.type}
                    </div>
                  </div>

                  <button
                    type="button"
                    className="btn btn-sm btn-secondary"
                    onClick={(e) => {
                      e.stopPropagation();
                      setFile(null);
                      setPreviewUrl(null);
                    }}
                    disabled={uploading}
                  >
                    Remove
                  </button>
                </div>
              )}

              {/* Progressive Inspection Status Indicator */}
              {uploading && (
                <div
                  style={{
                    margin: "1.25rem 0",
                    padding: "1rem",
                    background: "rgba(59, 130, 246, 0.05)",
                    borderRadius: "8px",
                    border: "1px solid var(--border)",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.75rem", fontWeight: 600 }}>
                    <span className="spinner" style={{ width: "16px", height: "16px" }} />
                    <span>AI Multi-Stage Inspection in Progress...</span>
                  </div>

                  <div style={{ fontSize: "0.85rem", display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                    <div style={{ color: inspectionStep >= 1 ? "var(--text)" : "var(--text-muted)" }}>
                      {inspectionStep > 1 ? "✓" : inspectionStep === 1 ? "●" : "○"} 1. Uploading sensor frame to plant repository...
                    </div>
                    <div style={{ color: inspectionStep >= 2 ? "var(--text)" : "var(--text-muted)" }}>
                      {inspectionStep > 2 ? "✓" : inspectionStep === 2 ? "●" : "○"} 2. Classifying product category (ResNet18 15-class classifier)...
                    </div>
                    <div style={{ color: inspectionStep >= 3 ? "var(--text)" : "var(--text-muted)" }}>
                      {inspectionStep > 3 ? "✓" : inspectionStep === 3 ? "●" : "○"} 3. Evaluating defect type & ResNet18 Layer3 anomaly score...
                    </div>
                    <div style={{ color: inspectionStep >= 4 ? "var(--text)" : "var(--text-muted)" }}>
                      {inspectionStep > 4 ? "✓" : inspectionStep === 4 ? "●" : "○"} 4. Running U-Net segmentation & severity scoring engine...
                    </div>
                    <div style={{ color: inspectionStep >= 5 ? "var(--text)" : "var(--text-muted)" }}>
                      {inspectionStep >= 5 ? "✓" : "○"} 5. Generating visual defect overlay & quality decision...
                    </div>
                  </div>
                </div>
              )}

              {/* Submit Button */}
              <div
                style={{
                  marginTop: "1.5rem",
                  display: "flex",
                  justifyContent: "flex-end",
                }}
              >
                <button
                  type="submit"
                  className="btn btn-primary btn-lg"
                  disabled={
                    !file ||
                    (!autoClassify && (!category || !defectType)) ||
                    uploading
                  }
                >
                  {uploading ? (
                    <>
                      <span
                        className="spinner"
                        style={{
                          width: "16px",
                          height: "16px",
                        }}
                      />
                      <span>Running Inspection...</span>
                    </>
                  ) : autoClassify ? (
                    "Upload & Auto-Inspect"
                  ) : (
                    "Upload & Run Inspection"
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}

export default Upload;