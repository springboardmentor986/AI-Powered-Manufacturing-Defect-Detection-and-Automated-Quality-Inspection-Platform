import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import Sidebar from "../components/Sidebar";

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

const formatCategory = (value = "") =>
  value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());

function Inspection() {
  const navigate = useNavigate();
  const imageRef = useRef(null);
  const previewFrameRef = useRef(null);
  const fileInputRef = useRef(null);

  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [category, setCategory] = useState("bottle");
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageLayout, setImageLayout] = useState(null);

  const measureImageLayout = () => {
    const loadedImage = imageRef.current;
    const frame = previewFrameRef.current;
    if (!loadedImage || !frame || !loadedImage.complete) return;

    const imageRect = loadedImage.getBoundingClientRect();
    const frameRect = frame.getBoundingClientRect();

    setImageLayout({
      naturalWidth: loadedImage.naturalWidth,
      naturalHeight: loadedImage.naturalHeight,
      renderedWidth: imageRect.width,
      renderedHeight: imageRect.height,
      frameWidth: frameRect.width,
      frameHeight: frameRect.height,
      imageLeft: imageRect.left - frameRect.left,
      imageTop: imageRect.top - frameRect.top,
    });
  };

  useEffect(() => {
    if (!imageLoaded) return undefined;

    const resizeObserver = new ResizeObserver(measureImageLayout);
    if (imageRef.current) resizeObserver.observe(imageRef.current);
    if (previewFrameRef.current) resizeObserver.observe(previewFrameRef.current);
    window.addEventListener("resize", measureImageLayout);

    return () => {
      resizeObserver.disconnect();
      window.removeEventListener("resize", measureImageLayout);
    };
  }, [imageLoaded]);

  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview);
    };
  }, [preview]);

  const handleImageChange = (file) => {
    if (!file) return;

    setError("");
    setResult(null);

    if (!file.type.startsWith("image/")) {
      setError("Please select a valid image file.");
      return;
    }

    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
      setError("Supported formats are JPG, PNG and WEBP.");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError("Please select an image smaller than 10 MB.");
      return;
    }

    if (preview) URL.revokeObjectURL(preview);

    setImage(file);
    setPreview(URL.createObjectURL(file));
    setImageLoaded(false);
    setImageLayout(null);
  };

  const handleFileInput = (event) => {
    handleImageChange(event.target.files?.[0]);
    event.target.value = "";
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setDragActive(false);
    handleImageChange(event.dataTransfer.files?.[0]);
  };

  const removeImage = () => {
    if (preview) URL.revokeObjectURL(preview);
    setImage(null);
    setPreview(null);
    setImageLoaded(false);
    setImageLayout(null);
    setResult(null);
    setError("");
  };

  const handleUpload = async (event) => {
    event.preventDefault();

    if (!image) {
      setError("Please select a product image first.");
      return;
    }

    setUploading(true);
    setError("");
    setResult(null);

    const formData = new FormData();
    formData.append("file", image);

    try {
      const response = await api.post(
        `/inspections/upload?category=${encodeURIComponent(category)}`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      setResult(response.data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Image upload or AI inspection failed."
      );
    } finally {
      setUploading(false);
    }
  };

  const mlResult = result?.result;
  const classification = mlResult?.classification;
  const quality = mlResult?.quality_assessment;
  const severity = quality?.severity;
  const imageQuality = mlResult?.image_quality;
  const detections = Array.isArray(mlResult?.defects)
    ? mlResult.defects
    : [];

  const status = String(mlResult?.status || "").toUpperCase();
  const isDefect = status === "DEFECT";

  const downloadImageQualityReport = async () => {
    if (!result || !imageQuality) return;

    try {
      const { jsPDF } = await import("jspdf");
      const pdf = new jsPDF();
      const pageWidth = pdf.internal.pageSize.getWidth();

      pdf.setFont("helvetica", "bold");
      pdf.setFontSize(20);
      pdf.text("VisionInspect AI", 20, 20);

      pdf.setFontSize(15);
      pdf.text("Image Quality Report", 20, 30);

      pdf.setFont("helvetica", "normal");
      pdf.setFontSize(10);
      pdf.text(
        `Generated: ${new Date().toLocaleString()}`,
        20,
        38
      );

      if (image) {
        const imageData = await new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve(reader.result);
          reader.onerror = reject;
          reader.readAsDataURL(image);
        });

        const imageFormat =
          image.type === "image/png" ? "PNG" : "JPEG";

        pdf.setFont("helvetica", "bold");
        pdf.setFontSize(12);
        pdf.text("Inspected Image", 20, 52);

        pdf.addImage(
          imageData,
          imageFormat,
          20,
          58,
          70,
          70
        );
      }

      const tableX = 105;
      let y = 58;

      pdf.setFont("helvetica", "bold");
      pdf.setFontSize(12);
      pdf.text("Inspection Details", tableX, y);

      y += 10;
      pdf.setFont("helvetica", "normal");
      pdf.setFontSize(10);

      const details = [
        ["Inspection ID", result.inspection_id || "-"],
        ["Category", result.category || category || "-"],
        ["File", result.filename || image?.name || "-"],
        ["Inspection Status", mlResult?.status || "-"],
      ];

      details.forEach(([label, value]) => {
        pdf.setFont("helvetica", "bold");
        pdf.text(`${label}:`, tableX, y);
        pdf.setFont("helvetica", "normal");
        pdf.text(String(value), tableX + 38, y);
        y += 7;
      });

      y = 145;

      pdf.setFont("helvetica", "bold");
      pdf.setFontSize(14);
      pdf.text("Image Quality Assessment", 20, y);

      y += 12;

      const rows = [
        ["Overall Status", imageQuality.quality_status],
        [
          "Quality Score",
          `${Number(imageQuality.quality_score).toFixed(2)} / 100`,
        ],
        ["Resolution", imageQuality.resolution],
        ["Brightness", Number(imageQuality.brightness).toFixed(2)],
        ["Contrast", Number(imageQuality.contrast).toFixed(2)],
        ["Sharpness", Number(imageQuality.sharpness).toFixed(2)],
        ["Noise", Number(imageQuality.noise).toFixed(2)],
      ];

      rows.forEach(([label, value]) => {
        pdf.setDrawColor(220, 220, 220);
        pdf.rect(20, y - 6, pageWidth - 40, 10);

        pdf.setFont("helvetica", "bold");
        pdf.text(label, 25, y);

        pdf.setFont("helvetica", "normal");
        pdf.text(String(value ?? "-"), 90, y);

        y += 10;
      });

      y += 8;
      pdf.setFont("helvetica", "bold");
      pdf.setFontSize(12);
      pdf.text("Assessment", 20, y);

      y += 8;
      pdf.setFont("helvetica", "normal");
      pdf.setFontSize(10);

      const assessment =
        imageQuality.quality_status === "ACCEPTABLE"
          ? "Image quality is acceptable for inspection."
          : "Image quality may affect inspection reliability.";

      const wrappedAssessment = pdf.splitTextToSize(
        assessment,
        pageWidth - 40
      );

      pdf.text(wrappedAssessment, 20, y);
      y += wrappedAssessment.length * 6 + 8;

      pdf.setFont("helvetica", "bold");
      pdf.text("Inspection Decision", 20, y);

      y += 8;
      pdf.setFont("helvetica", "normal");
      pdf.text(
        quality?.quality_decision || mlResult?.status || "-",
        20,
        y
      );

      y += 12;

      if (quality?.recommendation) {
        pdf.setFont("helvetica", "bold");
        pdf.text("Recommendation", 20, y);

        y += 8;
        pdf.setFont("helvetica", "normal");

        const recommendation = pdf.splitTextToSize(
          quality.recommendation,
          pageWidth - 40
        );

        pdf.text(recommendation, 20, y);
      }

      pdf.setFontSize(8);
      pdf.text(
        "VisionInspect AI - Manufacturing Quality Inspection System",
        20,
        285
      );

      pdf.save(
        `VisionInspect_Image_Quality_Report_${
          result.inspection_id || "inspection"
        }.pdf`
      );
    } catch (err) {
      console.error("PDF report generation failed:", err);
      setError(
        "Unable to generate the PDF report. Please try again."
      );
    }
  };

  const workflowSteps = [
    {
      number: 1,
      title: "Upload Image",
      text: "Select the product image for inspection.",
      done: Boolean(image),
    },
    {
      number: 2,
      title: "Anomaly Detection",
      text: "Autoencoder checks for abnormal patterns.",
      done: Boolean(result),
    },
    {
      number: 3,
      title: "Defect Localization",
      text: "YOLO identifies defect locations.",
      done: Boolean(result),
    },
    {
      number: 4,
      title: "Defect Classification",
      text: "Detected defects are classified.",
      done: Boolean(result),
    },
    {
      number: 5,
      title: "Quality Assessment",
      text: "Severity and pass/fail decision are generated.",
      done: Boolean(result),
    },
  ];

  return (
    <div className="vi-inspection-page">
      <Sidebar />

      <main className="vi-inspection-main">
        <header className="vi-inspection-header">
          <div>
            <div className="vi-breadcrumb">
              Dashboard <span>/</span> New Inspection
            </div>
            <h1>New Inspection</h1>
            <p>
              Upload a product image and let VisionInspect AI
              perform an automated quality inspection.
            </p>
          </div>

          <div className="vi-header-actions">
            <button
              className="vi-secondary-button"
              onClick={() => navigate("/history")}
            >
              View History
            </button>
            <button
              className="vi-primary-small"
              onClick={() => fileInputRef.current?.click()}
            >
              + Upload Image
            </button>
          </div>
        </header>

        {error && (
          <div className="vi-error-banner">
            <span>!</span>
            <div>
              <strong>Inspection error</strong>
              <p>{error}</p>
            </div>
            <button onClick={() => setError("")}>×</button>
          </div>
        )}

        <div className="vi-inspection-grid">
          <section className="vi-upload-panel">
            <div className="vi-panel-heading">
              <div>
                <span className="vi-eyebrow">INSPECTION INPUT</span>
                <h2>Product Image</h2>
                <p>
                  Choose the product category and upload the
                  image you want to inspect.
                </p>
              </div>
              <div className="vi-panel-icon">▣</div>
            </div>

            <div className="vi-category-field">
              <label htmlFor="vi-category">
                Product Category
              </label>

              <select
                id="vi-category"
                value={category}
                onChange={(event) => {
                  setCategory(event.target.value);
                  setResult(null);
                  setError("");
                }}
                disabled={uploading}
              >
                {CATEGORIES.map((item) => (
                  <option key={item} value={item}>
                    {formatCategory(item)}
                  </option>
                ))}
              </select>

              <span>
                Model selected: <strong>{formatCategory(category)}</strong>
              </span>
            </div>

            <form onSubmit={handleUpload}>
              {!image ? (
                <label
                  className={`vi-dropzone ${
                    dragActive ? "vi-dropzone-active" : ""
                  }`}
                  onDragEnter={(event) => {
                    event.preventDefault();
                    setDragActive(true);
                  }}
                  onDragOver={(event) => event.preventDefault()}
                  onDragLeave={(event) => {
                    if (!event.currentTarget.contains(event.relatedTarget)) {
                      setDragActive(false);
                    }
                  }}
                  onDrop={handleDrop}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    onChange={handleFileInput}
                    hidden
                  />

                  <div className="vi-upload-icon">↑</div>
                  <h3>Drop your product image here</h3>
                  <p>
                    Drag and drop an image into this area, or
                  </p>

                  <span className="vi-browse-link">
                    Browse files
                  </span>

                  <div className="vi-format-row">
                    <span>JPG</span>
                    <i>•</i>
                    <span>PNG</span>
                    <i>•</i>
                    <span>WEBP</span>
                    <i>•</i>
                    <span>Max 10 MB</span>
                  </div>
                </label>
              ) : (
                <div className="vi-selected-area">
                  <div className="vi-preview-heading">
                    <div>
                      <span className="vi-eyebrow">SELECTED IMAGE</span>
                      <strong>{image.name}</strong>
                    </div>
                    <button
                      type="button"
                      className="vi-change-button"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={uploading}
                    >
                      Change image
                    </button>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      onChange={handleFileInput}
                      hidden
                    />
                  </div>

                  <div
                    ref={previewFrameRef}
                    className="vi-preview-frame"
                  >
                    <div className="vi-image-stage">
                      <img
                        ref={imageRef}
                        src={preview}
                        alt="Selected product"
                        onLoad={() => {
                          setImageLoaded(true);
                          requestAnimationFrame(measureImageLayout);
                        }}
                      />

                    {imageLoaded && imageLayout && detections.map((detection, index) => {
                      const bbox = detection?.bbox;
                      if (
                        !bbox ||
                        !imageLayout
                      ) {
                        return null;
                      }

                      const {
                        naturalWidth: width,
                        naturalHeight: height,
                      } = imageLayout;

                      if (
                        !width ||
                        !height
                      ) {
                        return null;
                      }

                      const x1 = Math.max(
                        0,
                        Math.min(width, Number(bbox.x1) || 0)
                      );
                      const y1 = Math.max(
                        0,
                        Math.min(height, Number(bbox.y1) || 0)
                      );
                      const x2 = Math.max(
                        x1,
                        Math.min(width, Number(bbox.x2) || 0)
                      );
                      const y2 = Math.max(
                        y1,
                        Math.min(height, Number(bbox.y2) || 0)
                      );

                      return (
                        <div
                          key={index}
                          className="vi-bbox"
                          style={{
                            left: `${((x1 / width) * 100).toFixed(4)}%`,
                            top: `${((y1 / height) * 100).toFixed(4)}%`,
                            width: `${(((x2 - x1) / width) * 100).toFixed(4)}%`,
                            height: `${(((y2 - y1) / height) * 100).toFixed(4)}%`,
                          }}
                        >
                          <span>
                            {detection.class === "anomaly_region"
                              ? "ANOMALY REGION - MANUAL REVIEW"
                              : detection.defect_type ||
                              classification?.defect_type ||
                              "DEFECT"}
                            {detection.class !== "anomaly_region" &&
                            detection.confidence !== undefined
                              ? ` ${(detection.confidence * 100).toFixed(1)}%`
                              : ""}
                          </span>
                        </div>
                      );
                    })}
                    </div>

                    <button
                      type="button"
                      className="vi-remove-image"
                      onClick={removeImage}
                      disabled={uploading}
                      aria-label="Remove image"
                    >
                      ×
                    </button>
                  </div>

                  <div className="vi-file-meta">
                    <div>
                      <span className="vi-file-symbol">▣</span>
                      <div>
                        <strong>{image.name}</strong>
                        <small>
                          {(image.size / 1024 / 1024).toFixed(2)} MB
                          &nbsp; • &nbsp;
                          {image.type.split("/")[1].toUpperCase()}
                        </small>
                      </div>
                    </div>
                    <span className="vi-ready-badge">✓ Ready</span>
                  </div>
                </div>
              )}

              <button
                type="submit"
                className="vi-start-button"
                disabled={!image || uploading}
              >
                {uploading ? (
                  <>
                    <span className="vi-spinner"></span>
                    Running AI Inspection...
                  </>
                ) : (
                  <>
                    <span>✦</span>
                    Start AI Inspection
                  </>
                )}
              </button>
            </form>

            <div className="vi-secure-note">
              <span>🔒</span>
              <div>
                <strong>Secure inspection</strong>
                <p>
                  Your image is associated with a protected
                  inspection record.
                </p>
              </div>
            </div>
          </section>

          <aside className="vi-right-column">
            <section className="vi-workflow-card">
              <div className="vi-card-title-row">
                <div>
                  <span className="vi-eyebrow">AI PIPELINE</span>
                  <h3>Inspection Workflow</h3>
                </div>
                <span className="vi-step-count">
                  {result ? "5/5" : uploading ? "2/5" : "1/5"}
                </span>
              </div>

              <p className="vi-card-description">
                VisionInspect AI processes each image through
                multiple computer-vision stages.
              </p>

              <div className="vi-workflow-list">
                {workflowSteps.map((step, index) => (
                  <div
                    className={`vi-workflow-item ${
                      step.done ? "vi-workflow-done" : ""
                    } ${
                      uploading && index === 1
                        ? "vi-workflow-current"
                        : ""
                    }`}
                    key={step.number}
                  >
                    <div className="vi-workflow-marker">
                      {step.done ? "✓" : step.number}
                    </div>

                    <div className="vi-workflow-content">
                      <strong>{step.title}</strong>
                      <span>{step.text}</span>
                    </div>

                    {index < workflowSteps.length - 1 && (
                      <div className="vi-workflow-connector"></div>
                    )}
                  </div>
                ))}
              </div>
            </section>

            {!result ? (
              <section className="vi-info-card">
                <div className="vi-info-icon">✦</div>
                <span className="vi-eyebrow">AUTOMATED QUALITY CONTROL</span>
                <h3>Ready for inspection</h3>
                <p>
                  Select a product category, upload an image,
                  and start the AI inspection to receive defect
                  detection, localization and quality results.
                </p>

                <div className="vi-feature-list">
                  <span>✓ Anomaly detection</span>
                  <span>✓ Defect localization</span>
                  <span>✓ Multiple detections</span>
                  <span>✓ Severity assessment</span>
                  <span>✓ Automated quality decision</span>
                </div>
              </section>
            ) : (
              <section
                className={`vi-result-summary ${
                  isDefect ? "vi-result-defect" : "vi-result-good"
                }`}
              >
                <div className="vi-result-top">
                  <div>
                    <span className="vi-eyebrow">
                      AI INSPECTION COMPLETE
                    </span>
                    <h3>
                      {isDefect
                        ? "Defect Detected"
                        : "Product Passed"}
                    </h3>
                  </div>
                  <span className="vi-result-status">
                    {status || "COMPLETED"}
                  </span>
                </div>

                <div className="vi-result-metrics">
                  <div>
                    <span>
                      {isDefect && detections.length === 0
                        ? "Anomalies"
                        : "Defects"}
                    </span>
                    <strong>
                      {isDefect && detections.length === 0
                        ? "1"
                        : detections.length}
                    </strong>
                  </div>
                  <div>
                    <span>Category</span>
                    <strong>{formatCategory(category)}</strong>
                  </div>
                  <div>
                    <span>Severity</span>
                    <strong>{severity?.level || "—"}</strong>
                  </div>
                </div>

                <div className="vi-result-actions">
                  {imageQuality && (
                    <button
                      type="button"
                      onClick={downloadImageQualityReport}
                      className="vi-report-button"
                    >
                      ↓ &nbsp; Image Quality PDF
                    </button>
                  )}

                  <button
                    type="button"
                    className="vi-dashboard-button"
                    onClick={() => navigate("/dashboard")}
                  >
                    View Dashboard →
                  </button>
                </div>
              </section>
            )}
          </aside>
        </div>

        {result && mlResult && (
          <section className="vi-analysis-panel">
            <div className="vi-analysis-header">
              <div>
                <span className="vi-eyebrow">INSPECTION RESULTS</span>
                <h2>AI Analysis</h2>
                <p>
                  Detailed results returned by the inspection
                  pipeline.
                </p>
              </div>

              <div
                className={`vi-main-result-pill ${
                  isDefect ? "defect" : "good"
                }`}
              >
                <span>{isDefect ? "!" : "✓"}</span>
                {status || "COMPLETED"}
              </div>
            </div>

            <div className="vi-analysis-grid">
              <div className="vi-analysis-card">
                <span className="vi-analysis-icon">⌁</span>
                <span className="vi-analysis-label">
                  Classification
                </span>
                <strong>
                  {classification?.defect_type ||
                    (isDefect ? "Defect detected" : "Good product")}
                </strong>
                {classification?.confidence !== undefined && (
                  <small>
                    {(classification.confidence * 100).toFixed(1)}%
                    confidence
                  </small>
                )}
              </div>

              <div className="vi-analysis-card">
                <span className="vi-analysis-icon">◉</span>
                <span className="vi-analysis-label">
                  Defect Localization
                </span>
                <strong>{detections.length} detected</strong>
                <small>
                  {detections.length
                    ? "Bounding boxes generated"
                    : isDefect
                      ? "Anomaly detected; localization needs review"
                      : "No defect locations detected"}
                </small>
              </div>

              <div className="vi-analysis-card">
                <span className="vi-analysis-icon">◈</span>
                <span className="vi-analysis-label">
                  Severity
                </span>
                <strong>{severity?.level || "—"}</strong>
                <small>
                  {severity?.score !== undefined
                    ? `Score ${Number(severity.score).toFixed(2)} / 100`
                    : "No severity score available"}
                </small>
              </div>

              <div className="vi-analysis-card">
                <span className="vi-analysis-icon">✓</span>
                <span className="vi-analysis-label">
                  Quality Decision
                </span>
                <strong>
                  {quality?.quality_decision ||
                    mlResult?.status ||
                    "—"}
                </strong>
                <small>
                  {quality?.recommendation ||
                    "Automated decision generated by the pipeline."}
                </small>
              </div>
            </div>

            <div className="vi-results-detail-grid">
              <section className="vi-analysis-card vi-detail-card">
                <span className="vi-analysis-label">IMAGE QUALITY ASSESSMENT</span>
                <div className="vi-quality-detail-grid">
                  <div><span>Quality Score</span><strong>{Number.isFinite(Number(imageQuality?.quality_score)) ? `${Number(imageQuality.quality_score).toFixed(2)} / 100` : "—"}</strong></div>
                  <div><span>Quality Status</span><strong>{imageQuality?.quality_status || "—"}</strong></div>
                  <div><span>Resolution</span><strong>{imageQuality?.resolution || "—"}</strong></div>
                  <div><span>Width</span><strong>{imageQuality?.width ?? "—"}</strong></div>
                  <div><span>Height</span><strong>{imageQuality?.height ?? "—"}</strong></div>
                  <div><span>Brightness</span><strong>{imageQuality?.brightness ?? "—"}</strong></div>
                  <div><span>Contrast</span><strong>{imageQuality?.contrast ?? "—"}</strong></div>
                  <div><span>Sharpness</span><strong>{imageQuality?.sharpness ?? "—"}</strong></div>
                  <div><span>Noise</span><strong>{imageQuality?.noise ?? "—"}</strong></div>
                </div>
              </section>

              <section className="vi-analysis-card vi-detail-card">
                <span className="vi-analysis-label">QUALITY RISK ASSESSMENT</span>
                <div className="vi-quality-detail-grid">
                  <div><span>Risk Level</span><strong>{severity?.level || (isDefect ? "Review" : "Low")}</strong></div>
                  <div><span>Severity Score</span><strong>{severity?.score !== undefined ? `${Number(severity.score).toFixed(2)} / 100` : "—"}</strong></div>
                  <div><span>Severity</span><strong>{severity?.level || "—"}</strong></div>
                  <div><span>Defect Type</span><strong>{classification?.defect_type || "None detected"}</strong></div>
                  <div><span>Defect Confidence</span><strong>{classification?.confidence !== undefined ? `${(Number(classification.confidence) * 100).toFixed(1)}%` : "—"}</strong></div>
                  <div><span>Detected Defects</span><strong>{detections.length}</strong></div>
                  <div><span>Quality Decision</span><strong>{quality?.quality_decision || mlResult?.status || "—"}</strong></div>
                  <div className="vi-quality-recommendation"><span>Recommendation</span><strong>{quality?.recommendation || "—"}</strong></div>
                </div>
              </section>
            </div>

            {detections.length > 0 && (
              <div className="vi-detections-section">
                <div className="vi-subsection-header">
                  <div>
                    <h3>Detected Defects</h3>
                    <p>
                      All YOLO detections returned for this image.
                    </p>
                  </div>
                  <span>{detections.length} total</span>
                </div>

                <div className="vi-detection-table">
                  <div className="vi-detection-row vi-detection-head">
                    <span>#</span>
                    <span>DEFECT TYPE</span>
                    <span>CONFIDENCE</span>
                    <span>LOCATION</span>
                  </div>

                  {detections.map((detection, index) => (
                    <div
                      className="vi-detection-row"
                      key={index}
                    >
                      <span className="vi-detection-number">
                        {String(index + 1).padStart(2, "0")}
                      </span>
                      <strong>
                        {formatCategory(
                          detection.defect_type ||
                            detection.class_name ||
                            detection.type ||
                            classification?.defect_type ||
                            "Detected Defect"
                        )}
                      </strong>
                      <span className="vi-confidence">
                        {detection.confidence !== undefined
                          ? `${(detection.confidence * 100).toFixed(1)}%`
                          : "—"}
                      </span>
                      <span className="vi-location">
                        {detection.bbox
                          ? `X: ${Number(detection.bbox.x1).toFixed(0)}–${Number(
                              detection.bbox.x2
                            ).toFixed(0)}  |  Y: ${Number(
                              detection.bbox.y1
                            ).toFixed(0)}–${Number(
                              detection.bbox.y2
                            ).toFixed(0)}`
                          : "—"}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="vi-result-footer">
              <div>
                <span>Inspection ID</span>
                <strong>{result.inspection_id || "—"}</strong>
              </div>
              <div>
                <span>File</span>
                <strong title={result.filename || image?.name}>
                  {result.filename || image?.name || "—"}
                </strong>
              </div>
              <div>
                <span>Category</span>
                <strong>{formatCategory(category)}</strong>
              </div>
              <div>
                <span>Image Quality</span>
                <strong>
                  {imageQuality?.quality_score !== undefined
                    ? `${Number(imageQuality.quality_score).toFixed(1)} / 100`
                    : "—"}
                </strong>
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

export default Inspection;
