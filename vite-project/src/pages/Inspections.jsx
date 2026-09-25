import { useEffect, useState } from "react";

function Inspections() {
  const [inspections, setInspections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const API_URL = "http://127.0.0.1:8000";

  // =========================================================
  // FETCH INSPECTION HISTORY
  // =========================================================

  useEffect(() => {
    const fetchInspections = async () => {
      try {
        setLoading(true);
        setError("");

        const token = localStorage.getItem("access_token");

        if (!token) {
          setError("Your session has expired. Please login again.");
          return;
        }

        const response = await fetch(`${API_URL}/inspections`, {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
            Accept: "application/json",
          },
        });

        let data = null;

        try {
          data = await response.json();
        } catch {
          data = null;
        }

        // =====================================================
        // AUTH ERROR
        // =====================================================

        if (response.status === 401) {
          setError("Unauthorized. Please logout and login again.");
          return;
        }

        // =====================================================
        // OTHER API ERROR
        // =====================================================

        if (!response.ok) {
          throw new Error(
            data?.detail ||
              `Failed to fetch inspections (${response.status})`
          );
        }

        // =====================================================
        // SUCCESS
        // =====================================================

        setInspections(
          Array.isArray(data)
            ? data
            : data?.inspections || []
        );

      } catch (err) {
        console.error("Inspection history error:", err);

        setError(
          err.message || "Failed to fetch inspections"
        );

      } finally {
        setLoading(false);
      }
    };

    fetchInspections();
  }, []);

  // =========================================================
  // FORMAT PREDICTION
  // =========================================================

  const formatPrediction = (value) => {
    if (!value) {
      return "-";
    }

    const normalized = String(value)
      .trim()
      .toLowerCase();

    if (
      normalized === "pass" ||
      normalized === "good" ||
      normalized === "normal"
    ) {
      return "PASS";
    }

    if (
      normalized === "defect" ||
      normalized === "anomaly" ||
      normalized === "abnormal"
    ) {
      return "DEFECT";
    }

    return String(value)
      .trim()
      .replaceAll("_", " ")
      .toUpperCase();
  };

  // =========================================================
  // CHECK IF PREDICTION IS PASS
  // =========================================================

  const isPassPrediction = (value) => {
    if (!value) {
      return false;
    }

    const normalized = String(value)
      .trim()
      .toLowerCase();

    return (
      normalized === "pass" ||
      normalized === "good" ||
      normalized === "normal"
    );
  };

  // =========================================================
  // FORMAT DEFECT TYPE
  // =========================================================

  const formatDefectType = (value) => {
    if (!value) {
      return "-";
    }

    return String(value)
      .trim()
      .replaceAll("_", " ")
      .toLowerCase()
      .replace(/\b\w/g, (char) => char.toUpperCase());
  };

  // =========================================================
  // FORMAT ACTION
  // =========================================================

  const formatAction = (value) => {
    if (!value) {
      return "-";
    }

    return String(value)
      .trim()
      .replaceAll("_", " ")
      .toLowerCase()
      .replace(/\b\w/g, (char) => char.toUpperCase());
  };

  // =========================================================
  // FORMAT SEVERITY
  // =========================================================

  const formatSeverity = (value) => {
    if (!value) {
      return "-";
    }

    const normalized = String(value)
      .trim()
      .toLowerCase();

    return (
      normalized.charAt(0).toUpperCase() +
      normalized.slice(1)
    );
  };

  // =========================================================
  // FORMAT CONFIDENCE
  // =========================================================

  const formatConfidence = (value) => {
    if (
      value === null ||
      value === undefined ||
      value === ""
    ) {
      return "-";
    }

    const number = Number(value);

    if (Number.isNaN(number)) {
      return value;
    }

    return `${number.toFixed(2)}%`;
  };

  // =========================================================
  // FORMAT DATE
  // =========================================================

  const formatDate = (date) => {
    if (!date) {
      return "-";
    }

    const parsedDate = new Date(date);

    if (Number.isNaN(parsedDate.getTime())) {
      return date;
    }

    return parsedDate.toLocaleString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // =========================================================
  // SEVERITY STYLE
  // =========================================================

  const getSeverityClass = (severity) => {
    if (!severity) {
      return "bg-slate-100 text-slate-600";
    }

    const normalized = String(severity)
      .trim()
      .toLowerCase();

    switch (normalized) {
      case "critical":
        return "bg-red-100 text-red-700";

      case "high":
        return "bg-orange-100 text-orange-700";

      case "medium":
        return "bg-amber-100 text-amber-700";

      case "low":
        return "bg-green-100 text-green-700";

      default:
        return "bg-slate-100 text-slate-600";
    }
  };

  // =========================================================
  // ACTION STYLE
  // =========================================================

  const getActionClass = (action) => {
    if (!action) {
      return "bg-slate-100 text-slate-600";
    }

    const normalized = String(action)
      .trim()
      .toLowerCase()
      .replaceAll("_", " ");

    switch (normalized) {
      case "reject":
        return "bg-red-100 text-red-700";

      case "rework":
        return "bg-orange-100 text-orange-700";

      case "review":
        return "bg-indigo-100 text-indigo-700";

      case "accept":
        return "bg-green-100 text-green-700";

      case "manual review":
        return "bg-purple-100 text-purple-700";

      default:
        return "bg-slate-100 text-slate-600";
    }
  };

  // =========================================================
  // LOADING
  // =========================================================

  if (loading) {
    return (
      <div className="w-full">

        <div className="mb-6">
          <h1 className="text-2xl font-bold text-slate-900">
            Inspection History
          </h1>

          <p className="mt-1 text-sm text-slate-500">
            View previous inspection records and quality decisions.
          </p>
        </div>

        <div className="flex min-h-[300px] items-center justify-center rounded-xl border border-slate-200 bg-white shadow-sm">

          <div className="text-center">

            <div className="mx-auto h-9 w-9 animate-spin rounded-full border-4 border-slate-200 border-t-blue-600"></div>

            <p className="mt-3 text-sm text-slate-500">
              Loading inspection records...
            </p>

          </div>

        </div>

      </div>
    );
  }

  // =========================================================
  // MAIN PAGE
  // =========================================================

  return (
    <div className="w-full">

      {/* =====================================================
          HEADER
         ===================================================== */}

      <div className="mb-6">

        <h1 className="text-2xl font-bold text-slate-900">
          Inspection History
        </h1>

        <p className="mt-1 text-sm text-slate-500">
          View previous inspection records and quality decisions.
        </p>

      </div>


      {/* =====================================================
          ERROR
         ===================================================== */}

      {error && (
        <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-5 py-4">

          <p className="text-sm font-medium text-red-700">
            {error}
          </p>

        </div>
      )}


      {/* =====================================================
          TABLE
         ===================================================== */}

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">

        <div className="overflow-x-auto">

          <table className="w-full min-w-[950px]">

            {/* =================================================
                TABLE HEADER
               ================================================= */}

            <thead className="border-b border-slate-200 bg-slate-50">

              <tr>

                <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                  ID
                </th>

                <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Prediction
                </th>

                <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Defect Type
                </th>

                <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Confidence
                </th>

                <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Severity
                </th>

                <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Action
                </th>

                <th className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Date
                </th>

              </tr>

            </thead>


            {/* =================================================
                TABLE BODY
               ================================================= */}

            <tbody className="divide-y divide-slate-100">

              {inspections.length === 0 ? (

                <tr>

                  <td
                    colSpan="7"
                    className="px-5 py-12 text-center text-sm text-slate-500"
                  >
                    No inspection records found.
                  </td>

                </tr>

              ) : (

                inspections.map((inspection) => (

                  <tr
                    key={inspection.id}
                    className="transition hover:bg-slate-50"
                  >

                    {/* =================================================
                        ID
                       ================================================= */}

                    <td className="whitespace-nowrap px-5 py-4 text-sm font-semibold text-slate-800">
                      #{inspection.id}
                    </td>


                    {/* =================================================
                        PREDICTION
                       ================================================= */}

                    <td className="whitespace-nowrap px-5 py-4">

                      <span
                        className={`rounded-full px-3 py-1 text-xs font-semibold ${
                          isPassPrediction(
                            inspection.prediction
                          )
                            ? "bg-green-100 text-green-700"
                            : "bg-red-100 text-red-700"
                        }`}
                      >
                        {formatPrediction(
                          inspection.prediction
                        )}
                      </span>

                    </td>


                    {/* =================================================
                        DEFECT TYPE
                       ================================================= */}

                    <td className="whitespace-nowrap px-5 py-4 text-sm font-medium text-slate-700">

                      {formatDefectType(
                        inspection.defect_type
                      )}

                    </td>


                    {/* =================================================
                        CONFIDENCE
                       ================================================= */}

                    <td className="whitespace-nowrap px-5 py-4 text-sm text-slate-700">

                      {formatConfidence(
                        inspection.classification_confidence
                      )}

                    </td>


                    {/* =================================================
                        SEVERITY
                       ================================================= */}

                    <td className="whitespace-nowrap px-5 py-4">

                      {inspection.severity_level ? (

                        <span
                          className={`rounded-full px-3 py-1 text-xs font-semibold ${getSeverityClass(
                            inspection.severity_level
                          )}`}
                        >
                          {formatSeverity(
                            inspection.severity_level
                          )}
                        </span>

                      ) : (

                        <span className="text-sm text-slate-400">
                          -
                        </span>

                      )}

                    </td>


                    {/* =================================================
                        ACTION
                       ================================================= */}

                    <td className="whitespace-nowrap px-5 py-4">

                      {inspection.recommended_action ? (

                        <span
                          className={`rounded-full px-3 py-1 text-xs font-semibold ${getActionClass(
                            inspection.recommended_action
                          )}`}
                        >
                          {formatAction(
                            inspection.recommended_action
                          )}
                        </span>

                      ) : (

                        <span className="text-sm text-slate-400">
                          -
                        </span>

                      )}

                    </td>


                    {/* =================================================
                        DATE
                       ================================================= */}

                    <td className="whitespace-nowrap px-5 py-4 text-sm text-slate-500">

                      {formatDate(
                        inspection.created_at
                      )}

                    </td>

                  </tr>

                ))

              )}

            </tbody>

          </table>

        </div>

      </div>


      {/* =====================================================
          RECORD COUNT
         ===================================================== */}

      <div className="mt-3 text-right text-xs text-slate-400">

        {inspections.length} record
        {inspections.length === 1 ? "" : "s"}

      </div>

    </div>
  );
}

export default Inspections;