import { useEffect, useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import Navbar from "../components/Navbar";
import {
  getCurrentUser,
  getImage,
  getImageBlobUrl,
  getInspectionOverlayBlobUrl,
  reviewImage,
  AuthError,
  ForbiddenError,
  NotFoundError,
  ApiError,
} from "../services/api";

function ImageDetails() {
  const { imageId } = useParams();
  const navigate = useNavigate();

  const [user, setUser] = useState(null);
  const [image, setImage] = useState(null);

  const [imageUrl, setImageUrl] = useState(null);
  const [inspectionOverlayUrl, setInspectionOverlayUrl] =
    useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [errorType, setErrorType] = useState(null);

  const [supervisorNotes, setSupervisorNotes] = useState("");
  const [reviewing, setReviewing] = useState(false);
  const [reviewFeedback, setReviewFeedback] = useState(null);

  useEffect(() => {
    let active = true;

    let loadedImageUrl = null;
    let loadedOverlayUrl = null;

    const fetchImageRecord = async () => {
      setLoading(true);
      setError(null);
      setErrorType(null);

      try {
        const userData = await getCurrentUser();

        if (!active) return;

        setUser(userData);

        const data = await getImage(imageId);

        if (!active) return;

        setImage(data);
        setSupervisorNotes(data.supervisor_notes || "");

        // Load original image
        loadedImageUrl = await getImageBlobUrl(imageId);

        if (!active) {
          URL.revokeObjectURL(loadedImageUrl);
          return;
        }

        setImageUrl(loadedImageUrl);

        // Load AI defect overlay if inspection has produced one
        if (data.inspection_overlay_available) {
          try {
            loadedOverlayUrl =
              await getInspectionOverlayBlobUrl(imageId);

            if (!active) {
              URL.revokeObjectURL(loadedOverlayUrl);
              return;
            }

            setInspectionOverlayUrl(
              loadedOverlayUrl
            );
          } catch {
            if (active) {
              setInspectionOverlayUrl(null);
            }
          }
        } else {
          setInspectionOverlayUrl(null);
        }
      } catch (err) {
        if (!active) return;

        if (err instanceof AuthError) {
          setError(err.message);
          setErrorType("auth");
        } else if (err instanceof ForbiddenError) {
          setError(err.message);
          setErrorType("forbidden");
        } else if (err instanceof NotFoundError) {
          setError(
            `Inspection record #${imageId} was not found in the plant database.`
          );
          setErrorType("notfound");
        } else if (err instanceof ApiError) {
          setError(err.message);
          setErrorType("server");
        } else {
          setError(
            "Failed to fetch inspection details from plant server."
          );
          setErrorType("server");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    fetchImageRecord();

    return () => {
      active = false;

      if (loadedImageUrl) {
        URL.revokeObjectURL(loadedImageUrl);
      }

      if (loadedOverlayUrl) {
        URL.revokeObjectURL(loadedOverlayUrl);
      }
    };
  }, [imageId]);

  const handleSupervisorReview = async (decision) => {
    if (
      decision === "rejected" &&
      !supervisorNotes.trim()
    ) {
      setReviewFeedback({
        type: "error",
        text: "Supervisor audit note is required when rejecting an inspection batch.",
      });
      return;
    }

    setReviewing(true);
    setReviewFeedback(null);

    try {
      const updated = await reviewImage(
        imageId,
        decision,
        supervisorNotes.trim()
      );

      setImage(updated);

      setReviewFeedback({
        type: "success",
        text: `Inspection batch #${imageId} successfully marked as ${decision.toUpperCase()}.`,
      });
    } catch (err) {
      setReviewFeedback({
        type: "error",
        text:
          err.message ||
          "Failed to submit review.",
      });
    } finally {
      setReviewing(false);
    }
  };

  const isSupervisor = user?.role_id === 2;

  const returnDashboardPath = isSupervisor
    ? "/supervisor/dashboard"
    : "/dashboard";

  if (loading) {
    return (
      <div className="app-shell">
        <Navbar />

        <main className="main-content">
          <div className="state-container">
            <div className="spinner" />

            <div className="state-desc">
              Loading high-resolution inspection record #
              {imageId}...
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div className="app-shell">
        <Navbar />

        <main className="main-content">
          <div
            className="card"
            style={{
              maxWidth: "600px",
              margin: "3rem auto",
            }}
          >
            <div className="card-body">
              <div
                className="state-container"
                style={{
                  padding: "1.5rem",
                }}
              >
                <div
                  className="state-icon"
                  style={{
                    color: "var(--danger)",
                  }}
                >
                  ⚠️
                </div>

                <h2 className="state-title">
                  {errorType === "auth"
                    ? "Session Expired"
                    : errorType === "notfound"
                      ? "Inspection Record Not Found"
                      : "Console Notice"}
                </h2>

                <p className="state-desc">
                  {error}
                </p>

                <div
                  style={{
                    marginTop: "1rem",
                    display: "flex",
                    gap: "0.75rem",
                  }}
                >
                  {errorType === "auth" ? (
                    <button
                      className="btn btn-primary"
                      onClick={() =>
                        navigate("/login")
                      }
                    >
                      Log in again
                    </button>
                  ) : (
                    <Link
                      to={returnDashboardPath}
                      className="btn btn-primary"
                    >
                      Return to Dashboard
                    </Link>
                  )}
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  const isApproved =
    image.supervisor_decision === "approved";

  const isRejected =
    image.supervisor_decision === "rejected";

  const hasInspection =
    image.severity_score !== null &&
    image.severity_score !== undefined;

  return (
    <div className="app-shell">
      <Navbar />

      <main className="main-content">
        {/* Header */}
        <div className="page-header">
          <div className="page-title-group">
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
                marginBottom: "0.25rem",
              }}
            >
              <Link
                to={returnDashboardPath}
                style={{
                  fontSize: "0.85rem",
                  color: "var(--text-muted)",
                }}
              >
                ← Dashboard
              </Link>

              <span
                style={{
                  color: "var(--border-default)",
                }}
              >
                /
              </span>

              <span
                style={{
                  fontSize: "0.85rem",
                  color: "var(--text-secondary)",
                }}
              >
                Inspection #{image.id}
              </span>
            </div>

            <h1 className="page-title">
              {image.original_filename}

              {isApproved ? (
                <span className="badge badge-approved">
                  <span className="badge-dot" /> Approved
                </span>
              ) : isRejected ? (
                <span className="badge badge-rejected">
                  <span className="badge-dot" /> Rejected
                </span>
              ) : (
                <span className="badge badge-pending">
                  <span className="badge-dot" /> Pending Review
                </span>
              )}
            </h1>

            <p className="page-subtitle">
              Acquisition Timestamp:{" "}
              {new Date(
                image.uploaded_at
              ).toLocaleString()}
            </p>
          </div>

          <div className="page-actions">
            <Link
              to={returnDashboardPath}
              className="btn btn-secondary"
            >
              Back to Dashboard
            </Link>
          </div>
        </div>

        {/* Review feedback */}
        {reviewFeedback && (
          <div
            className={`alert ${reviewFeedback.type === "success"
              ? "alert-success"
              : "alert-error"
              }`}
          >
            <span>{reviewFeedback.text}</span>
          </div>
        )}

        <div
          style={{
            display: "grid",
            gridTemplateColumns:
              inspectionOverlayUrl
                ? "1fr 1fr"
                : "1fr",
            gap: "1.5rem",
            marginBottom: "1.5rem",
          }}
        >
          {/* Original Image */}
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">
                High-Resolution Visual Inspection Feed
              </h2>

              <span className="badge badge-neutral">
                Raw Sensor Frame
              </span>
            </div>

            <div
              className="card-body"
              style={{ padding: "1rem" }}
            >
              <div className="image-viewer-frame">
                {imageUrl ? (
                  <img
                    src={imageUrl}
                    alt={image.original_filename}
                  />
                ) : (
                  <div className="state-container">
                    <div className="spinner" />

                    <p className="state-desc">
                      Loading image...
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* AI Defect Highlight */}
          {inspectionOverlayUrl && (
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">
                  AI Defect Highlight
                </h2>

                {(image.resolved_defect_status === "normal" || image.defect_type === "normal" || image.quality_decision === "Accept") ? (
                  <span className="badge badge-approved">
                    No Defect Detected
                  </span>
                ) : (
                  <span className="badge badge-rejected">
                    Predicted Defect Region
                  </span>
                )}
              </div>

              <div
                className="card-body"
                style={{ padding: "1rem" }}
              >
                <div className="image-viewer-frame">
                  <img
                    src={inspectionOverlayUrl}
                    alt="AI predicted defect region"
                  />
                </div>

                <div
                  style={{
                    marginTop: "0.75rem",
                    fontSize: "0.8rem",
                    color: "var(--text-muted)",
                    textAlign: "center",
                  }}
                >
                  {image.defect_type === "normal" || image.quality_decision === "Accept"
                    ? "AI analysis confirmed no defect detected in this frame."
                    : "Red region indicates the area predicted by the AI segmentation model as defective."}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Main workspace */}
        <div className="inspection-grid">
          {/* RIGHT COLUMN */}
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "1.5rem",
            }}
          >
            {/* Image Information */}
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">
                  Image Information
                </h3>
              </div>

              <div className="card-body">
                <table className="meta-table">
                  <tbody>
                    <tr>
                      <th>Original Filename</th>
                      <td>
                        {image.original_filename}
                      </td>
                    </tr>

                    <tr>
                      <th>Uploaded By</th>
                      <td>
                        {image.uploaded_by?.name ||
                          "Unknown"}
                      </td>
                    </tr>

                    <tr>
                      <th>Upload Date</th>
                      <td>
                        {new Date(
                          image.uploaded_at
                        ).toLocaleDateString()}
                      </td>
                    </tr>

                    <tr>
                      <th>Upload Time</th>
                      <td>
                        {new Date(
                          image.uploaded_at
                        ).toLocaleTimeString()}
                      </td>
                    </tr>

                    <tr>
                      <th>Inspection Status</th>
                      <td>
                        {image.inspection_status ||
                          "pending"}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* AI Inspection */}
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">
                  AI Defect Inspection
                </h3>

                {hasInspection ? (
                  <span className="badge badge-approved">
                    Inspection Complete
                  </span>
                ) : (
                  <span className="badge badge-neutral">
                    Pending Inspection
                  </span>
                )}
              </div>

              <div className="card-body">
                {!hasInspection ? (
                  <div
                    style={{
                      padding: "1rem",
                      textAlign: "center",
                      color: "var(--text-muted)",
                    }}
                  >
                    AI inspection has not been
                    completed for this image.
                  </div>
                ) : (
                  <table className="meta-table">
                    <tbody>
                      <tr>
                        <th>Product Category</th>
                        <td>
                          <span style={{ textTransform: "capitalize", fontWeight: 600 }}>
                            {image.predicted_category || image.category || "—"}
                          </span>
                          {image.predicted_category && (
                            <span className="badge badge-neutral" style={{ marginLeft: "0.5rem", fontSize: "0.7rem" }}>
                              ResNet18 AI
                            </span>
                          )}
                        </td>
                      </tr>

                      <tr>
                        <th>AI Defect Type</th>
                        <td>
                          <span style={{ textTransform: "capitalize", fontWeight: 600 }}>
                            {image.predicted_defect_type || "—"}
                          </span>
                          {image.predicted_defect_type && (
                            <span className="badge badge-neutral" style={{ marginLeft: "0.5rem", fontSize: "0.7rem" }}>
                              Hierarchical ML
                            </span>
                          )}
                        </td>
                      </tr>

                      <tr>
                        <th>Classification Confidence</th>
                        <td>
                          {image.classification_confidence != null ? (
                            <strong>
                              {Number(image.classification_confidence).toFixed(1)}%
                            </strong>
                          ) : (
                            "—"
                          )}
                        </td>
                      </tr>

                      <tr>
                        <th>Resolved Defect Status</th>
                        <td>
                          <span
                            className={`badge ${
                              (image.resolved_defect_status === "normal" || image.defect_type === "normal" || image.quality_decision === "Accept")
                                ? "badge-approved"
                                : "badge-rejected"
                            }`}
                            style={{ textTransform: "capitalize" }}
                          >
                            {image.resolved_defect_status || image.defect_type || "—"}
                          </span>
                        </td>
                      </tr>

                      <tr>
                        <th>Anomaly Score</th>
                        <td>
                          {Number(
                            image.anomaly_score
                          ).toFixed(4)}
                        </td>
                      </tr>

                      <tr>
                        <th>Detection Confidence</th>
                        <td>
                          {Number(
                            image.confidence_score
                          ).toFixed(2)}
                          %
                        </td>
                      </tr>

                      <tr>
                        <th>Predicted Defect Area</th>
                        <td>
                          {Number(
                            image.predicted_area_percent
                          ).toFixed(2)}
                          %
                        </td>
                      </tr>

                      <tr>
                        <th>Size Score</th>
                        <td>
                          {Number(
                            image.size_score
                          ).toFixed(2)}
                        </td>
                      </tr>

                      <tr>
                        <th>Location Score</th>
                        <td>
                          {Number(
                            image.location_score
                          ).toFixed(2)}
                        </td>
                      </tr>

                      <tr>
                        <th>Defect Type Score</th>
                        <td>
                          {Number(
                            image.defect_type_score
                          ).toFixed(2)}
                        </td>
                      </tr>

                      <tr>
                        <th>Severity Score</th>
                        <td>
                          <strong>
                            {Number(
                              image.severity_score
                            ).toFixed(2)}
                          </strong>
                        </td>
                      </tr>

                      <tr>
                        <th>Severity Level</th>
                        <td>
                          <strong>
                            {image.severity_level ||
                              "—"}
                          </strong>
                        </td>
                      </tr>

                      <tr>
                        <th>Quality Decision</th>
                        <td>
                          <strong
                            style={{
                              color:
                                image.quality_decision ===
                                  "Reject"
                                  ? "var(--danger)"
                                  : "var(--success)",
                            }}
                          >
                            {image.quality_decision ||
                              "—"}
                          </strong>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                )}
              </div>
            </div>

            {/* Supervisor Review */}
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">
                  Factory Supervisor Sign-off
                </h3>

                {isApproved ? (
                  <span className="badge badge-approved">
                    Approved
                  </span>
                ) : isRejected ? (
                  <span className="badge badge-rejected">
                    Rejected
                  </span>
                ) : (
                  <span className="badge badge-neutral">
                    Awaiting Review
                  </span>
                )}
              </div>

              <div className="card-body">
                <table
                  className="meta-table"
                  style={{
                    marginBottom: "1rem",
                  }}
                >
                  <tbody>
                    <tr>
                      <th>Supervisor Decision</th>
                      <td>
                        {image.supervisor_decision
                          ? image.supervisor_decision.toUpperCase()
                          : "—"}
                      </td>
                    </tr>

                    <tr>
                      <th>Reviewed By</th>
                      <td>
                        {image.reviewed_by?.name ||
                          "—"}
                      </td>
                    </tr>

                    <tr>
                      <th>Review Timestamp</th>
                      <td>
                        {image.reviewed_at
                          ? new Date(
                            image.reviewed_at
                          ).toLocaleString()
                          : "—"}
                      </td>
                    </tr>
                  </tbody>
                </table>

                {isSupervisor && !image.supervisor_decision ? (
                  <div
                    style={{
                      borderTop:
                        "1px solid var(--border-subtle)",
                      paddingTop: "1rem",
                    }}
                  >
                    <div className="form-group">
                      <label
                        className="form-label"
                        htmlFor="auditNotes"
                      >
                        Supervisor Audit Notes{" "}
                        {image.supervisor_decision ===
                          "rejected" && (
                            <span
                              style={{
                                color:
                                  "var(--danger)",
                              }}
                            >
                              *
                            </span>
                          )}
                      </label>

                      <textarea
                        id="auditNotes"
                        className="form-textarea"
                        rows="3"
                        placeholder="Provide QA rationale, defect notes, or acceptance remarks..."
                        value={supervisorNotes}
                        onChange={(e) =>
                          setSupervisorNotes(
                            e.target.value
                          )
                        }
                        disabled={reviewing}
                      />
                    </div>

                    <div
                      style={{
                        display: "flex",
                        gap: "0.75rem",
                        marginTop: "1rem",
                      }}
                    >
                      <button
                        type="button"
                        className={`btn ${isApproved
                          ? "btn-secondary"
                          : "btn-success"
                          }`}
                        onClick={() =>
                          handleSupervisorReview(
                            "approved"
                          )
                        }
                        disabled={reviewing}
                        style={{
                          flex: 1,
                        }}
                      >
                        {reviewing
                          ? "Processing..."
                          : isApproved
                            ? "✓ Approved"
                            : "Approve Batch"}
                      </button>

                      <button
                        type="button"
                        className={`btn ${isRejected
                          ? "btn-secondary"
                          : "btn-danger"
                          }`}
                        onClick={() =>
                          handleSupervisorReview(
                            "rejected"
                          )
                        }
                        disabled={reviewing}
                        style={{
                          flex: 1,
                        }}
                      >
                        {reviewing
                          ? "Processing..."
                          : isRejected
                            ? "✕ Rejected"
                            : "Reject Batch"}
                      </button>
                    </div>
                  </div>
                ) : (
                  <div>
                    <div
                      style={{
                        fontSize: "0.85rem",
                        fontWeight: 600,
                        color:
                          "var(--text-secondary)",
                        marginBottom:
                          "0.35rem",
                      }}
                    >
                      Supervisor Audit Notes:
                    </div>

                    <div
                      style={{
                        padding:
                          "0.75rem 1rem",
                        background:
                          "var(--bg-main)",
                        borderRadius:
                          "var(--radius-md)",
                        border:
                          "1px solid var(--border-subtle)",
                        fontSize:
                          "0.875rem",
                        color:
                          image.supervisor_notes
                            ? "var(--text-primary)"
                            : "var(--text-muted)",
                        fontStyle:
                          image.supervisor_notes
                            ? "normal"
                            : "italic",
                      }}
                    >
                      {image.supervisor_notes ||
                        "No notes recorded for this inspection batch."}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default ImageDetails;