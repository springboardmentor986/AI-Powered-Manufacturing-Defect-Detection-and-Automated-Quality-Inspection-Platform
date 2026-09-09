import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";
import {
  getCurrentUser,
  getImages,
  getAnalyticsSummary,
  getImageBlobUrl,
  AuthError,
  ForbiddenError,
  ApiError,
} from "../services/api";

function Dashboard() {
  const navigate = useNavigate();

  const [user, setUser] = useState(null);
  const [images, setImages] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [thumbnails, setThumbnails] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [errorType, setErrorType] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  useEffect(() => {
    let active = true;

    const fetchDashboard = async () => {
      try {
        // 1. Get current authenticated user
        const userData = await getCurrentUser();

        if (!active) return;

        setUser(userData);

        // Supervisors use their own dashboard
        if (userData.role_id === 2) {
          navigate("/supervisor/dashboard", { replace: true });
          return;
        }

        // 2. Fetch inspection records
        const imageData = await getImages();

        if (!active) return;

        setImages(imageData);

        // 3. Fetch analytics from backend
        const analyticsData = await getAnalyticsSummary();

        if (!active) return;

        setAnalytics(analyticsData);

        // 4. Fetch thumbnails
        imageData.slice(0, 10).forEach(async (img) => {
          try {
            const url = await getImageBlobUrl(img.id);

            if (active) {
              setThumbnails((prev) => ({
                ...prev,
                [img.id]: url,
              }));
            }
          } catch {
            // Placeholder remains visible
          }
        });
      } catch (err) {
        if (!active) return;

        if (err instanceof AuthError) {
          setError(err.message);
          setErrorType("auth");
        } else if (err instanceof ForbiddenError) {
          setError(err.message);
          setErrorType("forbidden");
        } else if (err instanceof ApiError) {
          setError(err.message);
          setErrorType("server");
        } else {
          setError(
            "An unexpected error occurred while loading the dashboard."
          );
          setErrorType("server");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    fetchDashboard();

    return () => {
      active = false;
    };
  }, [navigate, refreshTrigger]);

  const handleRefresh = () => {
    setLoading(true);
    setError(null);
    setErrorType(null);
    setRefreshTrigger((prev) => prev + 1);
  };

  if (loading) {
    return (
      <div className="app-shell">
        <Navbar />

        <main className="main-content">
          <div className="state-container">
            <div className="spinner" />

            <div className="state-desc">
              Loading inspection analytics and telemetry...
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

                <h2 className="state-title">
                  {errorType === "auth"
                    ? "Session Expired"
                    : "Inspection Console Notice"}
                </h2>

                <p className="state-desc">{error}</p>

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
                      onClick={() => navigate("/login")}
                    >
                      Log in again
                    </button>
                  ) : errorType === "forbidden" ? (
                    <button
                      className="btn btn-primary"
                      onClick={() =>
                        navigate("/supervisor/dashboard")
                      }
                    >
                      Go to Supervisor Console
                    </button>
                  ) : (
                    <button
                      className="btn btn-primary"
                      onClick={handleRefresh}
                    >
                      Retry Connection
                    </button>
                  )}
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
            <h1 className="page-title">
              Quality Engineer Dashboard
              <span className="badge badge-role">
                Operator Console
              </span>
            </h1>

            <p className="page-subtitle">
              Logged in as{" "}
              <strong style={{ color: "var(--text-primary)" }}>
                {user?.name}
              </strong>
            </p>
          </div>

          <div className="page-actions">
            <Link to="/upload" className="btn btn-primary">
              <span>+ Upload Inspection Batch</span>
            </Link>
          </div>
        </div>

        {/* Analytics KPIs */}
        <div className="kpi-grid">
          <div className="kpi-card">
            <div className="kpi-card-header">
              <span className="kpi-lbl">Total Inspections</span>
            </div>

            <div className="kpi-val">
              {analytics?.total_inspections ?? 0}
            </div>
          </div>

          <div className="kpi-card">
            <div className="kpi-card-header">
              <span className="kpi-lbl">Pending Review</span>
            </div>

            <div className="kpi-val val-pending">
              {analytics?.pending_review ?? 0}
            </div>
          </div>

          <div className="kpi-card">
            <div className="kpi-card-header">
              <span className="kpi-lbl">Reviewed Inspections</span>
            </div>

            <div className="kpi-val val-approved">
              {analytics?.reviewed ?? 0}
            </div>
          </div>
        </div>

        {/* Additional Analytics */}
        <div className="kpi-grid">
          <div className="kpi-card">
            <div className="kpi-card-header">
              <span className="kpi-lbl">Accepted</span>
            </div>

            <div className="kpi-val val-approved">
              {analytics?.accepted ?? 0}
            </div>
          </div>

          <div className="kpi-card">
            <div className="kpi-card-header">
              <span className="kpi-lbl">Rejected</span>
            </div>

            <div className="kpi-val">
              {analytics?.rejected ?? 0}
            </div>
          </div>

          <div className="kpi-card">
            <div className="kpi-card-header">
              <span className="kpi-lbl">Critical</span>
            </div>

            <div className="kpi-val">
              {analytics?.severity?.critical ?? 0}
            </div>
          </div>
        </div>

        {/* Recent inspections */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">
              Recent Visual Inspections
              <span className="badge badge-neutral">
                {images.length} records
              </span>
            </h2>

            <button
              className="btn btn-secondary btn-sm"
              onClick={handleRefresh}
            >
              Refresh Queue
            </button>
          </div>

          <div className="card-body" style={{ padding: 0 }}>
            {images.length === 0 ? (
              <div className="state-container">
                <div className="state-icon">🖼️</div>

                <h3 className="state-title">
                  No Inspection Images Yet
                </h3>

                <p className="state-desc">
                  Start by uploading your first batch of inspection
                  images to log visual quality records.
                </p>

                <Link
                  to="/upload"
                  className="btn btn-primary"
                  style={{ marginTop: "0.5rem" }}
                >
                  Upload Now
                </Link>
              </div>
            ) : (
              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th style={{ width: "64px" }}>Preview</th>
                      <th>Filename & ID</th>
                      <th>Uploaded By</th>
                      <th>Timestamp</th>
                      <th>AI Status</th>
                      <th>Supervisor Decision</th>
                      <th style={{ textAlign: "right" }}>
                        Actions
                      </th>
                    </tr>
                  </thead>

                  <tbody>
                    {images.map((image) => {
                      const isApproved =
                        image.supervisor_decision === "approved";

                      const isRejected =
                        image.supervisor_decision === "rejected";

                      const hasAIInspection =
                        image.severity_score !== null &&
                        image.severity_score !== undefined;

                      return (
                        <tr key={image.id}>
                          <td>
                            {thumbnails[image.id] ? (
                              <img
                                src={thumbnails[image.id]}
                                alt={image.original_filename}
                                className="table-thumb"
                              />
                            ) : (
                              <div className="table-thumb-placeholder">
                                📷
                              </div>
                            )}
                          </td>

                          <td>
                            <Link
                              to={`/images/${image.id}`}
                              className="table-file-name"
                            >
                              {image.original_filename}
                            </Link>

                            <span className="table-meta-sub">
                              Inspection Record #{image.id}
                            </span>
                          </td>

                          <td>
                            <span style={{ fontWeight: 500 }}>
                              {image.uploaded_by?.name || "Operator"}
                            </span>
                          </td>

                          <td>
                            <span
                              className="table-meta-sub"
                              style={{
                                fontFamily: "var(--font-mono)",
                              }}
                            >
                              {new Date(
                                image.uploaded_at
                              ).toLocaleString()}
                            </span>
                          </td>

                          <td>
                            {hasAIInspection ? (
                              <span className="badge badge-approved">
                                <span className="badge-dot" />
                                Completed
                              </span>
                            ) : (
                              <span className="badge badge-pending">
                                <span className="badge-dot" />
                                Pending
                              </span>
                            )}
                          </td>

                          <td>
                            {isApproved ? (
                              <span className="badge badge-approved">
                                <span className="badge-dot" />
                                Approved
                              </span>
                            ) : isRejected ? (
                              <span className="badge badge-rejected">
                                <span className="badge-dot" />
                                Rejected
                              </span>
                            ) : (
                              <span className="badge badge-neutral">
                                Pending
                              </span>
                            )}
                          </td>

                          <td style={{ textAlign: "right" }}>
                            <Link
                              to={`/images/${image.id}`}
                              className="btn btn-secondary btn-sm"
                            >
                              Inspect Record →
                            </Link>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default Dashboard;