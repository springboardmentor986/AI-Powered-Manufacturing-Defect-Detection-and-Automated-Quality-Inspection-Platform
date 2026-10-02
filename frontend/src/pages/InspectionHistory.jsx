import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
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

function parseResult(item) {
  if (!item?.result) return null;

  if (typeof item.result === "object") {
    return item.result;
  }

  try {
    return JSON.parse(item.result);
  } catch {
    return null;
  }
}

function getOutcome(item) {
  const result = parseResult(item);

  const value = String(
    result?.status ||
      result?.prediction ||
      result?.classification?.prediction ||
      result?.classification?.label ||
      ""
  ).toLowerCase();

  if (value === "good" || value === "pass") return "GOOD";
  if (value === "defect" || value === "defective") return "DEFECT";

  const status = String(item?.status || "").toLowerCase();

  if (status === "failed") return "FAILED";
  if (status === "processing" || status === "pending") return "PROCESSING";

  return item?.result ? "COMPLETED" : "—";
}

function getDefectCount(item) {
  const result = parseResult(item);
  return Array.isArray(result?.defects) ? result.defects.length : 0;
}

function getCategory(item) {
  const result = parseResult(item);
  return (
    result?.category ||
    result?.inspection_category ||
    item?.category ||
    "unknown"
  );
}

function formatCategory(value = "unknown") {
  return String(value)
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";

  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function InspectionHistory() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const role = localStorage.getItem("role");
  const isEngineer = role === "quality_engineer";

  const [inspections, setInspections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");
  const [resultFilter, setResultFilter] = useState(
    searchParams.get("status") || "all"
  );
  const [sortOrder, setSortOrder] = useState("newest");
  const [page, setPage] = useState(1);

  const pageSize = 8;

  const loadInspections = async (refresh = false) => {
    try {
      if (refresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      setError("");

      const response = await api.get("/inspections/");
      const data = Array.isArray(response.data)
        ? response.data
        : response.data?.items || [];

      setInspections(data);
    } catch (err) {
      console.error("Failed to load inspection history:", err);
      setError(
        err.response?.data?.detail ||
          "Unable to load inspection history."
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadInspections();
  }, []);

  const filteredInspections = useMemo(() => {
    const query = search.trim().toLowerCase();

    const filtered = inspections.filter((item) => {
      const filename = String(
        item?.filename || item?.stored_filename || ""
      ).toLowerCase();

      const itemCategory = String(getCategory(item)).toLowerCase();
      const outcome = getOutcome(item);

      const matchesSearch =
        !query ||
        filename.includes(query) ||
        itemCategory.includes(query);

      const matchesCategory =
        category === "all" ||
        itemCategory === category.toLowerCase();

      const matchesResult =
        resultFilter === "all" ||
        outcome === resultFilter;

      return (
        matchesSearch &&
        matchesCategory &&
        matchesResult
      );
    });

    return filtered.sort((a, b) => {
      const dateA = new Date(a.created_at || 0).getTime();
      const dateB = new Date(b.created_at || 0).getTime();

      return sortOrder === "newest"
        ? dateB - dateA
        : dateA - dateB;
    });
  }, [
    inspections,
    search,
    category,
    resultFilter,
    sortOrder,
  ]);

  useEffect(() => {
    setPage(1);
  }, [search, category, resultFilter, sortOrder]);

  const totalPages = Math.max(
    1,
    Math.ceil(filteredInspections.length / pageSize)
  );

  const safePage = Math.min(page, totalPages);

  const visibleInspections = filteredInspections.slice(
    (safePage - 1) * pageSize,
    safePage * pageSize
  );

  const stats = useMemo(() => {
    const good = inspections.filter(
      (item) => getOutcome(item) === "GOOD"
    ).length;

    const defective = inspections.filter(
      (item) => getOutcome(item) === "DEFECT"
    ).length;

    const completed = inspections.filter(
      (item) => item.status === "completed"
    ).length;

    return {
      total: inspections.length,
      good,
      defective,
      completed,
    };
  }, [inspections]);

  const clearFilters = () => {
    setSearch("");
    setCategory("all");
    setResultFilter("all");
    setSortOrder("newest");
    setPage(1);
  };

  const retryInspection = async (inspection) => {
    try {
      const category = getCategory(inspection);
      const query = category !== "unknown"
        ? `?category=${encodeURIComponent(category)}`
        : "";
      await api.post(
        `/inspections/${inspection.id}/retry${query}`
      );
      await loadInspections(true);
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to retry the interrupted inspection.");
    }
  };

  return (
    <div className="dashboard-layout history-v3">

      {/* SIDEBAR */}
      <Sidebar />

      {/* MAIN */}
      <main className="dashboard-main history-main-v3">

        <header className="dashboard-header history-header-v3">
          <div>
            <div className="dashboard-breadcrumb">
              Workspace / Inspection History
            </div>

            <h1>Inspection History</h1>

            <p>
              Review and filter previous AI-powered quality
              inspections.
            </p>
          </div>

          <div className="history-header-actions-v3">
            <button
              className="history-refresh-v3"
              onClick={() => loadInspections(true)}
              disabled={refreshing}
            >
              <span className={refreshing ? "refresh-spin" : ""}>
                ↻
              </span>
              {refreshing ? "Refreshing..." : "Refresh"}
            </button>

            {isEngineer && (
              <button
                className="history-new-v3"
                onClick={() => navigate("/inspection")}
              >
                + New Inspection
              </button>
            )}
          </div>
        </header>

        {/* KPI CARDS */}
        <section className="history-kpis-v3">
          <div className="history-kpi-v3">
            <div className="history-kpi-icon blue">▤</div>
            <div>
              <span>Total Inspections</span>
              <strong>{stats.total}</strong>
              <small>All records</small>
            </div>
          </div>

          <div className="history-kpi-v3">
            <div className="history-kpi-icon green">✓</div>
            <div>
              <span>Good Parts</span>
              <strong>{stats.good}</strong>
              <small>Passed inspections</small>
            </div>
          </div>

          <div className="history-kpi-v3">
            <div className="history-kpi-icon red">!</div>
            <div>
              <span>Defective Parts</span>
              <strong>{stats.defective}</strong>
              <small>Defects detected</small>
            </div>
          </div>

          <div className="history-kpi-v3">
            <div className="history-kpi-icon purple">◷</div>
            <div>
              <span>Completed</span>
              <strong>{stats.completed}</strong>
              <small>Successfully processed</small>
            </div>
          </div>
        </section>

        {error && (
          <div className="history-error-v3">
            <span>!</span>
            {error}
          </div>
        )}

        {/* HISTORY CARD */}
        <section className="history-card-v3">

          <div className="history-card-header-v3">
            <div>
              <span className="history-eyebrow">
                QUALITY RECORDS
              </span>
              <h2>Inspection Records</h2>
              <p>
                {filteredInspections.length} record
                {filteredInspections.length !== 1 ? "s" : ""}{" "}
                matching current filters
              </p>
            </div>

            <div className="history-record-count">
              {inspections.length} total
            </div>
          </div>

          {/* FILTERS */}
          <div className="history-filters-v3">

            <div className="history-search-v3">
              <span>⌕</span>
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by filename..."
              />

              {search && (
                <button
                  type="button"
                  onClick={() => setSearch("")}
                  aria-label="Clear search"
                >
                  ×
                </button>
              )}
            </div>

            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              <option value="all">All Categories</option>
              {CATEGORIES.map((item) => (
                <option key={item} value={item}>
                  {formatCategory(item)}
                </option>
              ))}
            </select>

            <select
              value={resultFilter}
              onChange={(e) =>
                setResultFilter(e.target.value)
              }
            >
              <option value="all">All Results</option>
              <option value="GOOD">GOOD</option>
              <option value="DEFECT">DEFECT</option>
              <option value="PROCESSING">PROCESSING</option>
              <option value="FAILED">FAILED</option>
            </select>

            <select
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value)}
            >
              <option value="newest">Newest First</option>
              <option value="oldest">Oldest First</option>
            </select>

            {(search ||
              category !== "all" ||
              resultFilter !== "all" ||
              sortOrder !== "newest") && (
              <button
                type="button"
                className="history-clear-v3"
                onClick={clearFilters}
              >
                Clear
              </button>
            )}
          </div>

          {/* TABLE */}
          <div className="history-table-scroll-v3">
            <table className="history-table-v3">
              <thead>
                <tr>
                  <th>#</th>
                  <th>FILE NAME</th>
                  <th>CATEGORY</th>
                  <th>STATUS</th>
                  <th>RESULT</th>
                  <th>DEFECTS</th>
                  <th>DATE & TIME</th>
                </tr>
              </thead>

              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan="7">
                      <div className="history-loading-v3">
                        <div className="history-spinner-v3" />
                        <strong>
                          Loading inspection history
                        </strong>
                        <span>
                          Fetching your PostgreSQL inspection records...
                        </span>
                      </div>
                    </td>
                  </tr>
                ) : visibleInspections.length === 0 ? (
                  <tr>
                    <td colSpan="7">
                      <div className="history-empty-v3">
                        <div className="history-empty-icon-v3">
                          ◌
                        </div>
                        <strong>No inspections found</strong>
                        <span>
                          Try changing your filters or perform
                          a new inspection.
                        </span>

                        {(search ||
                          category !== "all" ||
                          resultFilter !== "all") && (
                          <button
                            type="button"
                            onClick={clearFilters}
                          >
                            Clear Filters
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ) : (
                  visibleInspections.map((inspection, index) => {
                    const outcome = getOutcome(inspection);
                    const defectCount =
                      getDefectCount(inspection);

                    const status = String(
                      inspection.status || "unknown"
                    ).toLowerCase();

                    return (
                      <tr
                        key={
                          inspection.id ||
                          `${inspection.filename}-${index}`
                        }
                      >
                        <td className="history-index-v3">
                          {(safePage - 1) * pageSize +
                            index +
                            1}
                        </td>

                        <td>
                          <div className="history-file-v3">
                            <div className="history-file-icon-v3">
                              ▧
                            </div>

                            <div>
                              <strong>
                                {inspection.filename ||
                                  inspection.stored_filename ||
                                  "Unnamed image"}
                              </strong>
                              <span>
                                Inspection #
                                {inspection.id ?? "—"}
                              </span>
                            </div>
                          </div>
                        </td>

                        <td>
                          <span className="history-category-v3">
                            {formatCategory(getCategory(inspection))}
                          </span>
                        </td>

                        <td>
                          <span
                            className={`history-status-v3 ${status}`}
                          >
                            <i />
                            {status === "completed"
                              ? "Completed"
                              : status === "failed"
                              ? "Failed"
                              : status === "pending" || status === "processing"
                              ? "In Progress"
                              : status}
                          </span>
                        </td>

                        <td>
                          <span
                            className={`history-result-v3 ${
                              outcome === "GOOD"
                                ? "good"
                                : outcome === "DEFECT"
                                ? "defect"
                                : "neutral"
                            }`}
                          >
                            {outcome === "GOOD"
                              ? "✓ GOOD"
                              : outcome === "DEFECT"
                              ? "! DEFECT"
                              : outcome}
                          </span>
                        </td>

                        <td>
                          <span
                            className={`history-defects-v3 ${
                              defectCount > 0 ? "has-defects" : ""
                            }`}
                          >
                            {defectCount}
                          </span>
                        </td>

                        <td className="history-date-v3">
                          <div>{formatDate(inspection.created_at)}</div>
                          {(status === "pending" || status === "processing") && (
                            <button
                              type="button"
                              className="history-retry-button"
                              onClick={() => retryInspection(inspection)}
                            >
                              Retry inspection
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* PAGINATION */}
          {!loading && filteredInspections.length > 0 && (
            <div className="history-pagination-v3">
              <span>
                Showing{" "}
                {(safePage - 1) * pageSize + 1}
                {"–"}
                {Math.min(
                  safePage * pageSize,
                  filteredInspections.length
                )}{" "}
                of {filteredInspections.length}
              </span>

              <div>
                <button
                  type="button"
                  disabled={safePage === 1}
                  onClick={() =>
                    setPage((current) =>
                      Math.max(1, current - 1)
                    )
                  }
                >
                  ←
                </button>

                <strong>{safePage}</strong>

                <button
                  type="button"
                  disabled={safePage === totalPages}
                  onClick={() =>
                    setPage((current) =>
                      Math.min(totalPages, current + 1)
                    )
                  }
                >
                  →
                </button>
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default InspectionHistory;
