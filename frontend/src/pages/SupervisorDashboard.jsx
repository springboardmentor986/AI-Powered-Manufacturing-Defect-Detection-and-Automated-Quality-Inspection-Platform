import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  BarChart,
  Bar,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import Navbar from "../components/Navbar";

import {
  getCurrentUser,
  getSupervisorReviewQueue,
  getAnalyticsSummary,
  getImageBlobUrl,
  reviewImage,
  AuthError,
  ForbiddenError,
  ApiError,
} from "../services/api";


function SupervisorDashboard() {
  const navigate = useNavigate();

  const [user, setUser] = useState(null);
  const [images, setImages] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [thumbnails, setThumbnails] = useState({});

  const [notesByImage, setNotesByImage] = useState({});
  const [reviewingId, setReviewingId] = useState(null);

  const [loading, setLoading] = useState(true);

  const [filter, setFilter] = useState("all");

  const [error, setError] = useState(null);
  const [errorType, setErrorType] = useState(null);

  const [actionMessage, setActionMessage] = useState(null);

  const [refreshTrigger, setRefreshTrigger] = useState(0);


  /*
   * ---------------------------------------------------------
   * Load Supervisor Dashboard
   * ---------------------------------------------------------
   */

  useEffect(() => {
    let active = true;

    const fetchSupervisorData = async () => {
      setLoading(true);
      setError(null);
      setErrorType(null);

      try {
        // 1. Current user
        const userData = await getCurrentUser();

        if (!active) {
          return;
        }

        setUser(userData);

        // Only Factory Supervisor can access this dashboard
        if (userData.role_id !== 2) {
          setError(
            "You do not have permission to access the Factory Supervisor console."
          );
          setErrorType("forbidden");
          return;
        }


        // 2. Supervisor review queue
        const imageData = await getSupervisorReviewQueue();

        if (!active) {
          return;
        }

        setImages(imageData);


        // 3. Analytics
        const analyticsData = await getAnalyticsSummary();

        if (!active) {
          return;
        }

        setAnalytics(analyticsData);


        // 4. Existing supervisor notes
        const initialNotes = {};

        imageData.forEach((img) => {
          if (img.supervisor_notes) {
            initialNotes[img.id] = img.supervisor_notes;
          }
        });

        setNotesByImage(initialNotes);


        // 5. Load thumbnails
        imageData.slice(0, 15).forEach(async (img) => {
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
        if (!active) {
          return;
        }

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
            "Unable to connect to the plant inspection service."
          );
          setErrorType("server");
        }

      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    fetchSupervisorData();

    return () => {
      active = false;
    };

  }, [navigate, refreshTrigger]);


  /*
   * ---------------------------------------------------------
   * Refresh
   * ---------------------------------------------------------
   */

  const handleRefresh = () => {
    setLoading(true);
    setError(null);
    setErrorType(null);
    setActionMessage(null);

    setRefreshTrigger((prev) => prev + 1);
  };


  /*
   * ---------------------------------------------------------
   * Supervisor Notes
   * ---------------------------------------------------------
   */

  const handleNotesChange = (imageId, value) => {
    setNotesByImage((prev) => ({
      ...prev,
      [imageId]: value,
    }));
  };


  /*
   * ---------------------------------------------------------
   * Supervisor Review
   * ---------------------------------------------------------
   */

  const handleReview = async (imageId, decision) => {
    const notes = (notesByImage[imageId] || "").trim();

    if (decision === "rejected" && !notes) {
      setActionMessage({
        type: "error",
        text:
          `Inspection #${imageId} rejection requires supervisor audit notes. ` +
          `Please enter a note explaining the rejection reason.`,
      });

      return;
    }

    setReviewingId(imageId);
    setActionMessage(null);

    try {
      const updatedImage = await reviewImage(
        imageId,
        decision,
        notes
      );

      setImages((prev) =>
        prev.map((img) =>
          img.id === imageId
            ? updatedImage
            : img
        )
      );

      setActionMessage({
        type: "success",
        text:
          `Inspection #${imageId} ` +
          `(${updatedImage.original_filename}) marked as ` +
          `${decision.toUpperCase()}.`,
      });

    } catch (err) {

      if (err instanceof AuthError) {
        setError(err.message);
        setErrorType("auth");

      } else {
        setActionMessage({
          type: "error",
          text:
            err.message ||
            "Failed to submit review decision.",
        });
      }

    } finally {
      setReviewingId(null);
    }
  };


  /*
   * ---------------------------------------------------------
   * Loading
   * ---------------------------------------------------------
   */

  if (loading) {
    return (
      <div className="app-shell">
        <Navbar />

        <main className="main-content">
          <div className="state-container">

            <div className="spinner" />

            <div className="state-desc">
              Loading supervisor analytics and review queue...
            </div>

          </div>
        </main>
      </div>
    );
  }


  /*
   * ---------------------------------------------------------
   * Error
   * ---------------------------------------------------------
   */

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
                    : "Access Restricted"}
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

                  ) : errorType === "forbidden" ? (

                    <button
                      className="btn btn-primary"
                      onClick={() =>
                        navigate("/dashboard")
                      }
                    >
                      Back to Dashboard
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


  /*
   * ---------------------------------------------------------
   * Queue Statistics
   * ---------------------------------------------------------
   */

  const totalQueue = images.length;

  const pendingCount = images.filter(
    (img) =>
      !img.supervisor_decision ||
      img.supervisor_decision === "pending"
  ).length;

  const reviewedCount = images.filter(
    (img) =>
      img.inspection_status === "reviewed"
  ).length;

  const approvedCount = images.filter(
    (img) =>
      img.supervisor_decision === "approved"
  ).length;

  const rejectedCount = images.filter(
    (img) =>
      img.supervisor_decision === "rejected"
  ).length;


  /*
   * ---------------------------------------------------------
   * Filters
   * ---------------------------------------------------------
   */

  const filteredImages = images.filter((img) => {

    if (filter === "pending") {
      return (
        !img.supervisor_decision ||
        img.supervisor_decision === "pending"
      );
    }

    if (filter === "approved") {
      return (
        img.supervisor_decision === "approved"
      );
    }

    if (filter === "rejected") {
      return (
        img.supervisor_decision === "rejected"
      );
    }

    return true;
  });


  /*
   * ---------------------------------------------------------
   * Analytics Chart Data
   * ---------------------------------------------------------
   */

  const severityData = [
    {
      name: "Critical",
      value: analytics?.severity?.critical ?? 0,
    },
    {
      name: "High",
      value: analytics?.severity?.high ?? 0,
    },
    {
      name: "Medium",
      value: analytics?.severity?.medium ?? 0,
    },
    {
      name: "Low",
      value: analytics?.severity?.low ?? 0,
    },
  ];


  const decisionData = [
    {
      name: "Accepted",
      value: analytics?.accepted ?? 0,
    },
    {
      name: "Rejected",
      value: analytics?.rejected ?? 0,
    },
  ];


  const defectTypeData = (
    analytics?.defect_types ?? []
  ).map((item) => ({
    name: item.defect_type,
    count: item.count,
  }));


  const categoryData = (
    analytics?.categories ?? []
  ).map((item) => ({
    name: item.category,
    count: item.count,
  }));


  /*
   * ---------------------------------------------------------
   * Chart Colors
   * ---------------------------------------------------------
   *
   * These colors are deliberately chosen for the dark UI.
   *
   * Cyan   = main analytics
   * Green  = accepted / healthy
   * Red    = rejected / critical
   * Amber  = warning
   * Purple = secondary category information
   *
   */

  const COLORS = {
    cyan: "#22d3ee",
    green: "#34d399",
    red: "#f87171",
    amber: "#fbbf24",
    purple: "#a78bfa",

    text: "#cbd5e1",
    grid: "#263449",

    tooltipBackground: "#111827",
    tooltipBorder: "#334155",
  };


  const severityColors = [
    COLORS.red,
    COLORS.amber,
    COLORS.purple,
    COLORS.green,
  ];


  const decisionColors = [
    COLORS.green,
    COLORS.red,
  ];


  /*
   * ---------------------------------------------------------
   * Render
   * ---------------------------------------------------------
   */

  return (
    <div className="app-shell">

      <Navbar />

      <main className="main-content">

        {/* =================================================
            HEADER
        ================================================= */}

        <div className="page-header">

          <div className="page-title-group">

            <h1 className="page-title">

              Factory Supervisor Dashboard

              <span className="badge badge-role">
                Supervisor Console
              </span>

            </h1>

            <p className="page-subtitle">
              Logged in as{" "}
              <strong
                style={{
                  color: "var(--text-primary)",
                }}
              >
                {user?.name}
              </strong>
            </p>

          </div>


          <div className="page-actions">

            <button
              className="btn btn-secondary"
              onClick={handleRefresh}
            >
              ↻ Refresh Dashboard
            </button>

          </div>

        </div>


        {/* =================================================
            ACTION MESSAGE
        ================================================= */}

        {actionMessage && (
          <div
            className={`alert ${actionMessage.type === "success"
              ? "alert-success"
              : "alert-error"
              }`}
          >
            <span>
              {actionMessage.text}
            </span>
          </div>
        )}


        {/* =================================================
            SUPERVISOR KPI CARDS
        ================================================= */}

        <div className="kpi-grid">

          <div className="kpi-card">

            <div className="kpi-card-header">
              <span className="kpi-lbl">
                Total Queue
              </span>
            </div>

            <div className="kpi-val">
              {totalQueue}
            </div>

          </div>


          <div className="kpi-card">

            <div className="kpi-card-header">
              <span className="kpi-lbl">
                Pending Review
              </span>
            </div>

            <div className="kpi-val val-pending">
              {pendingCount}
            </div>

          </div>


          <div className="kpi-card">

            <div className="kpi-card-header">
              <span className="kpi-lbl">
                Reviewed
              </span>
            </div>

            <div className="kpi-val">
              {reviewedCount}
            </div>

          </div>


          <div className="kpi-card">

            <div className="kpi-card-header">
              <span className="kpi-lbl">
                Approved
              </span>
            </div>

            <div className="kpi-val val-approved">
              {approvedCount}
            </div>

          </div>


          <div className="kpi-card">

            <div className="kpi-card-header">
              <span className="kpi-lbl">
                Rejected
              </span>
            </div>

            <div
              className="kpi-val"
              style={{
                color: COLORS.red,
              }}
            >
              {rejectedCount}
            </div>

          </div>

        </div>


        {/* =================================================
            AI QUALITY SUMMARY
        ================================================= */}

        <div
          className="kpi-grid"
          style={{
            marginTop: "1rem",
          }}
        >

          <div className="kpi-card">

            <div className="kpi-card-header">
              <span className="kpi-lbl">
                AI Inspections
              </span>
            </div>

            <div className="kpi-val">
              {analytics?.total_inspections ?? 0}
            </div>

          </div>


          <div className="kpi-card">

            <div className="kpi-card-header">
              <span className="kpi-lbl">
                Average Confidence
              </span>
            </div>

            <div className="kpi-val">
              {Number(
                analytics?.average?.confidence ?? 0
              ).toFixed(1)}
              %
            </div>

          </div>


          <div className="kpi-card">

            <div className="kpi-card-header">
              <span className="kpi-lbl">
                Average Severity
              </span>
            </div>

            <div className="kpi-val">
              {Number(
                analytics?.average?.severity ?? 0
              ).toFixed(1)}
            </div>

          </div>


          <div className="kpi-card">

            <div className="kpi-card-header">
              <span className="kpi-lbl">
                Critical Inspections
              </span>
            </div>

            <div
              className="kpi-val"
              style={{
                color: COLORS.red,
              }}
            >
              {analytics?.severity?.critical ?? 0}
            </div>

          </div>

        </div>


        {/* =================================================
            ANALYTICS SECTION
        ================================================= */}

        <div
          style={{
            marginTop: "1.5rem",
            marginBottom: "0.75rem",
          }}
        >

          <h2
            style={{
              margin: 0,
              fontSize: "1.1rem",
              color: "var(--text-primary)",
            }}
          >
            Manufacturing Quality Analytics
          </h2>

          <p
            style={{
              marginTop: "0.35rem",
              color: "var(--text-secondary)",
              fontSize: "0.85rem",
            }}
          >
            Overview of AI inspection results and quality decisions.
          </p>

        </div>


        {/* =================================================
            CHART GRID
        ================================================= */}

        <div
          style={{
            display: "grid",
            gridTemplateColumns:
              "repeat(auto-fit, minmax(340px, 1fr))",
            gap: "1rem",
          }}
        >

          {/* =================================================
              SEVERITY DISTRIBUTION
          ================================================= */}

          <div className="card">

            <div className="card-header">

              <h2 className="card-title">
                Severity Distribution
              </h2>

            </div>


            <div
              className="card-body"
              style={{
                height: "330px",
              }}
            >

              <ResponsiveContainer
                width="100%"
                height="100%"
              >

                <BarChart
                  data={severityData}
                  margin={{
                    top: 15,
                    right: 15,
                    left: 0,
                    bottom: 10,
                  }}
                >

                  <CartesianGrid
                    stroke={COLORS.grid}
                    strokeDasharray="3 3"
                  />

                  <XAxis
                    dataKey="name"
                    tick={{
                      fill: COLORS.text,
                      fontSize: 12,
                    }}
                    axisLine={{
                      stroke: COLORS.grid,
                    }}
                    tickLine={{
                      stroke: COLORS.grid,
                    }}
                  />

                  <YAxis
                    allowDecimals={false}
                    tick={{
                      fill: COLORS.text,
                      fontSize: 12,
                    }}
                    axisLine={{
                      stroke: COLORS.grid,
                    }}
                    tickLine={{
                      stroke: COLORS.grid,
                    }}
                  />

                  <Tooltip
                    contentStyle={{
                      backgroundColor:
                        COLORS.tooltipBackground,
                      border:
                        `1px solid ${COLORS.tooltipBorder}`,
                      borderRadius: "8px",
                      color: "#ffffff",
                    }}
                    labelStyle={{
                      color: "#ffffff",
                    }}
                    itemStyle={{
                      color: COLORS.text,
                    }}
                  />

                  <Bar
                    dataKey="value"
                    name="Inspections"
                    radius={[5, 5, 0, 0]}
                  >

                    {severityData.map(
                      (entry, index) => (
                        <Cell
                          key={`severity-${index}`}
                          fill={
                            severityColors[index]
                          }
                        />
                      )
                    )}

                  </Bar>

                </BarChart>

              </ResponsiveContainer>

            </div>

          </div>


          {/* =================================================
              QUALITY DECISIONS
          ================================================= */}

          <div className="card">

            <div className="card-header">

              <h2 className="card-title">
                Quality Decisions
              </h2>

            </div>


            <div
              className="card-body"
              style={{
                height: "330px",
              }}
            >

              <ResponsiveContainer
                width="100%"
                height="100%"
              >

                <PieChart>

                  <Pie
                    data={decisionData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="45%"
                    outerRadius={100}
                    innerRadius={45}
                    paddingAngle={3}
                    label={({ name, value }) =>
                      `${name}: ${value}`
                    }
                  >

                    {decisionData.map(
                      (entry, index) => (
                        <Cell
                          key={`decision-${index}`}
                          fill={
                            decisionColors[index]
                          }
                        />
                      )
                    )}

                  </Pie>


                  <Tooltip
                    contentStyle={{
                      backgroundColor:
                        COLORS.tooltipBackground,
                      border:
                        `1px solid ${COLORS.tooltipBorder}`,
                      borderRadius: "8px",
                      color: "#ffffff",
                    }}
                    labelStyle={{
                      color: "#ffffff",
                    }}
                    itemStyle={{
                      color: COLORS.text,
                    }}
                  />


                  <Legend
                    wrapperStyle={{
                      color: COLORS.text,
                    }}
                  />

                </PieChart>

              </ResponsiveContainer>

            </div>

          </div>


          {/* =================================================
              DEFECT TYPES
          ================================================= */}

          <div className="card">

            <div className="card-header">

              <h2 className="card-title">
                Defect Types
              </h2>

            </div>


            <div
              className="card-body"
              style={{
                height: "330px",
              }}
            >

              {defectTypeData.length === 0 ? (

                <div className="state-container">

                  <div className="state-icon">
                    📊
                  </div>

                  <div className="state-desc">
                    No defect type data available yet.
                  </div>

                </div>

              ) : (

                <ResponsiveContainer
                  width="100%"
                  height="100%"
                >

                  <BarChart
                    data={defectTypeData}
                    layout="vertical"
                    margin={{
                      top: 10,
                      right: 20,
                      left: 15,
                      bottom: 10,
                    }}
                  >

                    <CartesianGrid
                      stroke={COLORS.grid}
                      strokeDasharray="3 3"
                    />

                    <XAxis
                      type="number"
                      allowDecimals={false}
                      tick={{
                        fill: COLORS.text,
                        fontSize: 12,
                      }}
                      axisLine={{
                        stroke: COLORS.grid,
                      }}
                      tickLine={{
                        stroke: COLORS.grid,
                      }}
                    />

                    <YAxis
                      type="category"
                      dataKey="name"
                      width={90}
                      tick={{
                        fill: COLORS.text,
                        fontSize: 12,
                      }}
                      axisLine={{
                        stroke: COLORS.grid,
                      }}
                      tickLine={{
                        stroke: COLORS.grid,
                      }}
                    />

                    <Tooltip
                      contentStyle={{
                        backgroundColor:
                          COLORS.tooltipBackground,
                        border:
                          `1px solid ${COLORS.tooltipBorder}`,
                        borderRadius: "8px",
                        color: "#ffffff",
                      }}
                      labelStyle={{
                        color: "#ffffff",
                      }}
                      itemStyle={{
                        color: COLORS.text,
                      }}
                    />

                    <Bar
                      dataKey="count"
                      name="Inspections"
                      fill={COLORS.cyan}
                      radius={[0, 5, 5, 0]}
                    />

                  </BarChart>

                </ResponsiveContainer>

              )}

            </div>

          </div>


          {/* =================================================
              PRODUCT CATEGORIES
          ================================================= */}

          <div className="card">

            <div className="card-header">

              <h2 className="card-title">
                Product Categories
              </h2>

            </div>


            <div
              className="card-body"
              style={{
                height: "330px",
              }}
            >

              {categoryData.length === 0 ? (

                <div className="state-container">

                  <div className="state-icon">
                    📦
                  </div>

                  <div className="state-desc">
                    No category data available yet.
                  </div>

                </div>

              ) : (

                <ResponsiveContainer
                  width="100%"
                  height="100%"
                >

                  <BarChart
                    data={categoryData}
                    margin={{
                      top: 10,
                      right: 20,
                      left: 0,
                      bottom: 55,
                    }}
                  >

                    <CartesianGrid
                      stroke={COLORS.grid}
                      strokeDasharray="3 3"
                    />

                    <XAxis
                      dataKey="name"
                      angle={-35}
                      textAnchor="end"
                      interval={0}
                      tick={{
                        fill: COLORS.text,
                        fontSize: 11,
                      }}
                      axisLine={{
                        stroke: COLORS.grid,
                      }}
                      tickLine={{
                        stroke: COLORS.grid,
                      }}
                    />

                    <YAxis
                      allowDecimals={false}
                      tick={{
                        fill: COLORS.text,
                        fontSize: 12,
                      }}
                      axisLine={{
                        stroke: COLORS.grid,
                      }}
                      tickLine={{
                        stroke: COLORS.grid,
                      }}
                    />

                    <Tooltip
                      contentStyle={{
                        backgroundColor:
                          COLORS.tooltipBackground,
                        border:
                          `1px solid ${COLORS.tooltipBorder}`,
                        borderRadius: "8px",
                        color: "#ffffff",
                      }}
                      labelStyle={{
                        color: "#ffffff",
                      }}
                      itemStyle={{
                        color: COLORS.text,
                      }}
                    />

                    <Bar
                      dataKey="count"
                      name="Inspections"
                      fill={COLORS.purple}
                      radius={[5, 5, 0, 0]}
                    />

                  </BarChart>

                </ResponsiveContainer>

              )}

            </div>

          </div>

        </div>


        {/* =================================================
            REVIEW QUEUE
        ================================================= */}

        <div
          className="card"
          style={{
            marginTop: "1.5rem",
          }}
        >

          <div className="card-header">

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "1rem",
                flexWrap: "wrap",
              }}
            >

              <h2 className="card-title">
                Inspection Review Queue
              </h2>


              <div
                style={{
                  display: "flex",
                  gap: "0.4rem",
                  flexWrap: "wrap",
                }}
              >

                <button
                  type="button"
                  className={
                    `btn btn-sm ${filter === "all"
                      ? "btn-primary"
                      : "btn-secondary"
                    }`
                  }
                  onClick={() =>
                    setFilter("all")
                  }
                >
                  All ({totalQueue})
                </button>


                <button
                  type="button"
                  className={
                    `btn btn-sm ${filter === "pending"
                      ? "btn-primary"
                      : "btn-secondary"
                    }`
                  }
                  onClick={() =>
                    setFilter("pending")
                  }
                >
                  Pending ({pendingCount})
                </button>


                <button
                  type="button"
                  className={
                    `btn btn-sm ${filter === "approved"
                      ? "btn-primary"
                      : "btn-secondary"
                    }`
                  }
                  onClick={() =>
                    setFilter("approved")
                  }
                >
                  Approved ({approvedCount})
                </button>


                <button
                  type="button"
                  className={
                    `btn btn-sm ${filter === "rejected"
                      ? "btn-primary"
                      : "btn-secondary"
                    }`
                  }
                  onClick={() =>
                    setFilter("rejected")
                  }
                >
                  Rejected ({rejectedCount})
                </button>

              </div>

            </div>

          </div>


          <div
            className="card-body"
            style={{
              padding: 0,
            }}
          >

            {filteredImages.length === 0 ? (

              <div className="state-container">

                <div className="state-icon">
                  📋
                </div>

                <h3 className="state-title">
                  No Inspections Found
                </h3>

                <p className="state-desc">

                  {filter === "all"
                    ? "No inspection batches are currently logged in the system."
                    : `No inspection records match the "${filter}" filter criteria.`}

                </p>

              </div>

            ) : (

              <div className="table-wrapper">

                <table className="data-table">

                  <thead>

                    <tr>

                      <th
                        style={{
                          width: "64px",
                        }}
                      >
                        Visual
                      </th>

                      <th>
                        Filename & ID
                      </th>

                      <th>
                        Uploaded By
                      </th>

                      <th>
                        Timestamp
                      </th>

                      <th>
                        AI Result
                      </th>

                      <th>
                        Current Decision
                      </th>

                      <th
                        style={{
                          minWidth: "220px",
                        }}
                      >
                        Supervisor Audit Notes
                      </th>

                      <th
                        style={{
                          textAlign: "right",
                          minWidth: "180px",
                        }}
                      >
                        Sign-off Action
                      </th>

                    </tr>

                  </thead>


                  <tbody>

                    {filteredImages.map(
                      (image) => {

                        const isApproved =
                          image.supervisor_decision ===
                          "approved";

                        const isRejected =
                          image.supervisor_decision ===
                          "rejected";

                        const isProcessing =
                          reviewingId === image.id;

                        const hasAIInspection =
                          image.severity_score !== null &&
                          image.severity_score !==
                          undefined;


                        return (

                          <tr key={image.id}>

                            {/* Visual */}

                            <td>

                              {thumbnails[image.id] ? (

                                <img
                                  src={
                                    thumbnails[image.id]
                                  }
                                  alt={
                                    image.original_filename
                                  }
                                  className="table-thumb"
                                />

                              ) : (

                                <div className="table-thumb-placeholder">
                                  📷
                                </div>

                              )}

                            </td>


                            {/* Filename */}

                            <td>

                              <Link
                                to={`/images/${image.id}`}
                                className="table-file-name"
                              >
                                {image.original_filename}
                              </Link>

                              <span className="table-meta-sub">
                                Inspection Record #
                                {image.id}
                              </span>

                            </td>


                            {/* Uploaded By */}

                            <td>

                              <span
                                style={{
                                  fontWeight: 500,
                                }}
                              >
                                {image.uploaded_by?.name ||
                                  "Operator"}
                              </span>

                            </td>


                            {/* Timestamp */}

                            <td>

                              <span
                                className="table-meta-sub"
                                style={{
                                  fontFamily:
                                    "var(--font-mono)",
                                }}
                              >
                                {new Date(
                                  image.uploaded_at
                                ).toLocaleString()}
                              </span>

                            </td>


                            {/* AI Result */}

                            <td>

                              {hasAIInspection ? (

                                <div
                                  style={{
                                    display: "flex",
                                    flexDirection:
                                      "column",
                                    gap: "0.25rem",
                                  }}
                                >

                                  <span
                                    className="badge badge-approved"
                                  >
                                    <span className="badge-dot" />

                                    {image.severity_level ||
                                      "Completed"}

                                  </span>

                                  <span
                                    className="table-meta-sub"
                                  >
                                    Score:{" "}
                                    {Number(
                                      image.severity_score
                                    ).toFixed(1)}
                                  </span>

                                </div>

                              ) : (

                                <span className="badge badge-pending">

                                  <span className="badge-dot" />

                                  Pending AI

                                </span>

                              )}

                            </td>


                            {/* Decision */}

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

                                <span className="badge badge-pending">
                                  <span className="badge-dot" />
                                  Pending Review
                                </span>

                              )}

                            </td>


                            {/* Audit Notes */}

                            <td>

                              <textarea
                                className="form-textarea"
                                rows="2"
                                placeholder={
                                  isApproved ||
                                    isRejected
                                    ? "Review completed"
                                    : "Enter audit observations..."
                                }
                                value={
                                  notesByImage[
                                  image.id
                                  ] ??
                                  image.supervisor_notes ??
                                  ""
                                }
                                onChange={(e) =>
                                  handleNotesChange(
                                    image.id,
                                    e.target.value
                                  )
                                }
                                disabled={
                                  isProcessing ||
                                  isApproved ||
                                  isRejected
                                }
                                style={{
                                  fontSize:
                                    "0.825rem",
                                  padding:
                                    "0.4rem 0.6rem",
                                  opacity:
                                    isApproved ||
                                      isRejected
                                      ? 0.65
                                      : 1,
                                }}
                              />


                              {image.reviewed_by && (
                                <span
                                  className="table-meta-sub"
                                  style={{
                                    display:
                                      "block",
                                    marginTop:
                                      "0.25rem",
                                  }}
                                >
                                  Reviewed by{" "}
                                  {
                                    image
                                      .reviewed_by
                                      .name
                                  }{" "}
                                  at{" "}
                                  {new Date(
                                    image.reviewed_at
                                  ).toLocaleTimeString()}
                                </span>
                              )}

                            </td>


                            {/* Sign-off */}

                            <td
                              style={{
                                textAlign: "right",
                              }}
                            >

                              {!isApproved &&
                                !isRejected ? (

                                <div
                                  style={{
                                    display: "flex",
                                    gap: "0.4rem",
                                    justifyContent:
                                      "flex-end",
                                  }}
                                >

                                  <button
                                    type="button"
                                    className="btn btn-success btn-sm"
                                    onClick={() =>
                                      handleReview(
                                        image.id,
                                        "approved"
                                      )
                                    }
                                    disabled={
                                      isProcessing
                                    }
                                    title="Approve visual inspection batch"
                                  >
                                    {isProcessing
                                      ? "..."
                                      : "Approve"}
                                  </button>


                                  <button
                                    type="button"
                                    className="btn btn-danger btn-sm"
                                    onClick={() =>
                                      handleReview(
                                        image.id,
                                        "rejected"
                                      )
                                    }
                                    disabled={
                                      isProcessing
                                    }
                                    title="Reject visual inspection batch (requires notes)"
                                  >
                                    {isProcessing
                                      ? "..."
                                      : "Reject"}
                                  </button>

                                </div>

                              ) : (

                                <span className="table-meta-sub">
                                  Review completed
                                </span>

                              )}

                            </td>

                          </tr>

                        );

                      }
                    )}

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


export default SupervisorDashboard;