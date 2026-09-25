import { useEffect, useRef, useState } from "react";

const API_URL = "http://127.0.0.1:8000";

function Inspection({ user }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const imageRef = useRef(null);
  const overlayRef = useRef(null);

  const [imageLoaded, setImageLoaded] = useState(false);

  // ============================================================
  // SELECT IMAGE
  // ============================================================

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    const newUrl = URL.createObjectURL(file);

    setSelectedFile(file);
    setPreviewUrl(newUrl);

    setResult(null);
    setError("");
    setImageLoaded(false);
  };

  // ============================================================
  // IMAGE LOADED
  // ============================================================

  const handleImageLoad = () => {
    setImageLoaded(true);

    console.log(
      "IMAGE NATURAL WIDTH:",
      imageRef.current?.naturalWidth
    );

    console.log(
      "IMAGE NATURAL HEIGHT:",
      imageRef.current?.naturalHeight
    );

    console.log(
      "IMAGE DISPLAY WIDTH:",
      imageRef.current?.clientWidth
    );

    console.log(
      "IMAGE DISPLAY HEIGHT:",
      imageRef.current?.clientHeight
    );
  };

  // ============================================================
  // CLEAN URL
  // ============================================================

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  // ============================================================
  // SUBMIT INSPECTION
  // ============================================================

  const handleInspection = async () => {
    if (!selectedFile) {
      setError("Please select an image first.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const token = localStorage.getItem("access_token");

      if (!token) {
        throw new Error(
          "Authentication token not found. Please login again."
        );
      }

      const formData = new FormData();

      formData.append("file", selectedFile);

      const response = await fetch(
        `${API_URL}/inspection/predict`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formData,
        }
      );

      const data = await response.json();

      // ========================================================
      // DEBUG RESPONSE
      // ========================================================

      console.log(
        "===================================="
      );

      console.log(
        "FULL INSPECTION RESPONSE:"
      );

      console.log(
        JSON.stringify(data, null, 2)
      );

      console.log(
        "===================================="
      );

      if (!response.ok) {
        throw new Error(
          data.detail || "Inspection failed."
        );
      }

      setResult(data);

      if (imageRef.current) {
        console.log(
          "IMAGE WIDTH:",
          imageRef.current.naturalWidth
        );

        console.log(
          "IMAGE HEIGHT:",
          imageRef.current.naturalHeight
        );
      }
    } catch (err) {
      console.error(
        "INSPECTION ERROR:",
        err
      );

      setError(
        err.message ||
          "Something went wrong during inspection."
      );
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // REMOVE IMAGE
  // ============================================================

  const handleRemove = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    setSelectedFile(null);
    setPreviewUrl(null);
    setResult(null);
    setError("");
    setImageLoaded(false);
  };

  // ============================================================
  // GET DETECTIONS
  // ============================================================

  const detections = Array.isArray(
    result?.detections
  )
    ? result.detections
    : [];

  // ============================================================
  // GET BOUNDING BOX
  // ============================================================

  const getBoundingBox = (detection) => {
    /*
      Supported formats:

      1. bbox: [x1, y1, x2, y2]

      2. box: [x1, y1, x2, y2]

      3. bounding_box: [x1, y1, x2, y2]

      4. bbox:
         {
           x1,
           y1,
           x2,
           y2
         }

      5.
         {
           x1,
           y1,
           x2,
           y2
         }
    */

    if (
      Array.isArray(detection?.bbox) &&
      detection.bbox.length >= 4
    ) {
      return detection.bbox
        .slice(0, 4)
        .map(Number);
    }

    if (
      Array.isArray(detection?.box) &&
      detection.box.length >= 4
    ) {
      return detection.box
        .slice(0, 4)
        .map(Number);
    }

    if (
      Array.isArray(
        detection?.bounding_box
      ) &&
      detection.bounding_box.length >= 4
    ) {
      return detection.bounding_box
        .slice(0, 4)
        .map(Number);
    }

    if (
      detection?.bbox &&
      typeof detection.bbox === "object"
    ) {
      const x1 = Number(
        detection.bbox.x1
      );

      const y1 = Number(
        detection.bbox.y1
      );

      const x2 = Number(
        detection.bbox.x2
      );

      const y2 = Number(
        detection.bbox.y2
      );

      if (
        Number.isFinite(x1) &&
        Number.isFinite(y1) &&
        Number.isFinite(x2) &&
        Number.isFinite(y2)
      ) {
        return [x1, y1, x2, y2];
      }
    }

    if (
      detection?.x1 !== undefined &&
      detection?.y1 !== undefined &&
      detection?.x2 !== undefined &&
      detection?.y2 !== undefined
    ) {
      return [
        Number(detection.x1),
        Number(detection.y1),
        Number(detection.x2),
        Number(detection.y2),
      ];
    }

    return null;
  };

  // ============================================================
  // GET DETECTION LABEL
  // ============================================================

  const getDetectionLabel = (detection) => {
    return (
      detection?.defect_type ||
      detection?.class_name ||
      detection?.className ||
      detection?.class ||
      detection?.label ||
      "Defect"
    );
  };

  // ============================================================
  // GET YOLO CONFIDENCE
  // ============================================================

  const getYoloConfidence = (detection) => {
    let confidence =
      detection?.yolo_confidence ??
      detection?.yoloConfidence ??
      detection?.confidence ??
      detection?.conf ??
      0;

    confidence = Number(confidence);

    if (!Number.isFinite(confidence)) {
      return 0;
    }

    /*
      If backend sends:

      0.7977

      convert to:

      79.77
    */

    if (confidence <= 1) {
      confidence *= 100;
    }

    return confidence;
  };

  // ============================================================
  // FORMAT CONFIDENCE
  // ============================================================

  const formatConfidence = (confidence) => {
    return `${Number(confidence).toFixed(2)}%`;
  };

  // ============================================================
  // GET CLASSIFICATION CONFIDENCE
  // ============================================================

  const getClassificationConfidence = (
    detection
  ) => {
    let confidence =
      detection?.classification_confidence ??
      detection?.classificationConfidence ??
      null;

    if (confidence === null) {
      return null;
    }

    confidence = Number(confidence);

    if (!Number.isFinite(confidence)) {
      return null;
    }

    if (confidence <= 1) {
      confidence *= 100;
    }

    return confidence;
  };

  // ============================================================
  // GET BOUNDING BOX STYLE
  // ============================================================

  const getBoundingBoxStyle = (
    detection
  ) => {
    const bbox =
      getBoundingBox(detection);

    const image =
      imageRef.current;

    if (!bbox || !image) {
      return null;
    }

    const naturalWidth =
      image.naturalWidth;

    const naturalHeight =
      image.naturalHeight;

    const displayedWidth =
      image.clientWidth;

    const displayedHeight =
      image.clientHeight;

    if (
      !naturalWidth ||
      !naturalHeight ||
      !displayedWidth ||
      !displayedHeight
    ) {
      return null;
    }

    const [
      x1,
      y1,
      x2,
      y2,
    ] = bbox;

    // ========================================================
    // SCALE ORIGINAL YOLO COORDINATES
    // TO DISPLAYED IMAGE SIZE
    // ========================================================

    const scaleX =
      displayedWidth /
      naturalWidth;

    const scaleY =
      displayedHeight /
      naturalHeight;

    const left =
      x1 * scaleX;

    const top =
      y1 * scaleY;

    const width =
      (x2 - x1) * scaleX;

    const height =
      (y2 - y1) * scaleY;

    return {
      left: `${left}px`,
      top: `${top}px`,
      width: `${width}px`,
      height: `${height}px`,
    };
  };

  // ============================================================
  // INSPECTION STATUS
  // ============================================================

  /*
    IMPORTANT:

    We determine the displayed product status from
    the actual number of YOLO detections.

    0 detections  -> GOOD
    1+ detections -> DEFECT

    This prevents a situation where the backend says
    "DEFECT" but defect_count is actually 0.
  */

  const defectCount =
    result?.defect_count ??
    detections.length;

  const isDefect =
    Number(defectCount) > 0;

  const status = isDefect
    ? "DEFECT"
    : "GOOD";

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <div className="grid grid-cols-1 gap-7 xl:grid-cols-2">

      {/* ======================================================
          LEFT PANEL
      ====================================================== */}

      <section className="rounded-2xl border border-slate-200 bg-white p-7 shadow-sm">

        {/* ----------------------------------------------------
            HEADER
        ---------------------------------------------------- */}

        <div>
          <h2 className="text-2xl font-bold text-slate-900">
            Product Image
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            Upload an image for quality inspection.
          </p>
        </div>

        {/* ====================================================
            UPLOAD AREA
        ==================================================== */}

        {!previewUrl && (
          <label className="mt-8 flex min-h-[420px] cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 transition hover:border-blue-400 hover:bg-blue-50">

            <div className="text-center">

              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-blue-100 text-3xl text-blue-600">
                +
              </div>

              <h3 className="mt-5 text-lg font-semibold text-slate-800">
                Upload inspection image
              </h3>

              <p className="mt-2 text-sm text-slate-500">
                JPG, JPEG, PNG, BMP, TIFF or WEBP
              </p>

            </div>

            <input
              type="file"
              accept=".jpg,.jpeg,.png,.bmp,.tif,.tiff,.webp"
              onChange={handleFileChange}
              className="hidden"
            />

          </label>
        )}

        {/* ====================================================
            IMAGE
        ==================================================== */}

        {previewUrl && (
          <div className="mt-8">

            <div className="flex min-h-[400px] items-center justify-center overflow-hidden rounded-xl border border-slate-200 bg-slate-950 p-0">

              {/* =================================================
                  IMAGE + BOUNDING BOX WRAPPER
              ================================================== */}

              <div
                ref={overlayRef}
                className="relative inline-block max-h-[520px] max-w-full"
              >

                {/* ---------------------------------------------
                    ACTUAL IMAGE
                --------------------------------------------- */}

                <img
                  ref={imageRef}
                  src={previewUrl}
                  alt="Inspection"
                  onLoad={handleImageLoad}
                  className="block max-h-[520px] max-w-full object-contain"
                />

                {/* =============================================
                    YOLO BOUNDING BOXES
                ============================================= */}

                {imageLoaded &&
                  result &&
                  detections.map(
                    (detection, index) => {

                      const boxStyle =
                        getBoundingBoxStyle(
                          detection
                        );

                      const label =
                        getDetectionLabel(
                          detection
                        );

                      const confidence =
                        getYoloConfidence(
                          detection
                        );

                      console.log(
                        `Detection ${index}:`,
                        {
                          detection,
                          bbox:
                            getBoundingBox(
                              detection
                            ),
                          boxStyle,
                        }
                      );

                      if (!boxStyle) {
                        return null;
                      }

                      return (
                        <div
                          key={index}
                          className="pointer-events-none absolute border-[4px] border-cyan-400"
                          style={boxStyle}
                        >

                          {/* -----------------------------------
                              LABEL
                          ----------------------------------- */}

                          <div className="absolute left-[-4px] top-[-38px] whitespace-nowrap bg-cyan-400 px-2 py-1 text-lg font-medium leading-none text-black">

                            {label}:{" "}
                            {formatConfidence(
                              confidence
                            )}

                          </div>

                        </div>
                      );
                    }
                  )}

              </div>

            </div>

            {/* =================================================
                FILE INFORMATION
            ================================================== */}

            <div className="mt-5 flex items-center justify-between">

              <div>

                <p className="font-semibold text-slate-900">
                  {selectedFile?.name}
                </p>

                <p className="mt-1 text-sm text-slate-500">
                  {selectedFile
                    ? (
                        selectedFile.size /
                        1024
                      ).toFixed(1)
                    : "0"}{" "}
                  KB
                </p>

              </div>

              <button
                type="button"
                onClick={handleRemove}
                className="text-sm font-medium text-red-500 transition hover:text-red-700"
              >
                Remove
              </button>

            </div>

            {/* =================================================
                SUBMIT BUTTON
            ================================================== */}

            <button
              type="button"
              onClick={handleInspection}
              disabled={loading}
              className="mt-6 w-full rounded-xl bg-blue-600 px-5 py-4 font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
            >

              {loading
                ? "Analyzing..."
                : "Submit for Inspection"}

            </button>

          </div>
        )}

        {/* ====================================================
            ERROR
        ==================================================== */}

        {error && (
          <div className="mt-5 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-600">
            {error}
          </div>
        )}

      </section>

      {/* ======================================================
          RIGHT PANEL
      ====================================================== */}

      <section className="rounded-2xl border border-slate-200 bg-white p-7 shadow-sm">

        <div>

          <h2 className="text-2xl font-bold text-slate-900">
            Inspection Result
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            AI analysis results will appear here.
          </p>

        </div>

        {/* ====================================================
            NO RESULT
        ==================================================== */}

        {!result && (
          <div className="mt-10 flex min-h-[400px] items-center justify-center rounded-xl border border-dashed border-slate-300 bg-slate-50">

            <p className="text-sm text-slate-400">
              Submit an image to see inspection results.
            </p>

          </div>
        )}

        {/* ====================================================
            RESULT
        ==================================================== */}

        {result && (
          <div className="mt-8 space-y-6">

            {/* ==================================================
                INSPECTION RESULT
            ================================================== */}

            <div
              className={`rounded-xl border p-7 ${
                isDefect
                  ? "border-red-200 bg-red-50"
                  : "border-green-200 bg-green-50"
              }`}
            >

              <p className="text-sm font-medium uppercase tracking-wide text-slate-500">
                Inspection Result
              </p>

              <h3
                className={`mt-2 text-3xl font-bold ${
                  isDefect
                    ? "text-red-600"
                    : "text-green-600"
                }`}
              >
                {isDefect
                  ? "Defect Detected"
                  : "No Defect Detected"}
              </h3>

              <p
                className={`mt-2 text-sm ${
                  isDefect
                    ? "text-red-600"
                    : "text-green-600"
                }`}
              >
                {isDefect
                  ? "Defect detected in the product."
                  : "No defect detected. Product passed inspection."}
              </p>

            </div>

            {/* ==================================================
                SUMMARY
            ================================================== */}

            <div className="grid grid-cols-2 gap-5">

              {/* ----------------------------------------------
                  DEFECT COUNT
              ----------------------------------------------- */}

              <div className="rounded-xl border border-slate-200 bg-slate-50 p-5">

                <p className="text-sm text-slate-500">
                  Defects Detected
                </p>

                <p className="mt-3 text-3xl font-bold text-slate-900">
                  {defectCount}
                </p>

              </div>

              {/* ----------------------------------------------
                  PRODUCT STATUS
              ----------------------------------------------- */}

              <div className="rounded-xl border border-slate-200 bg-slate-50 p-5">

                <p className="text-sm text-slate-500">
                  Product Status
                </p>

                <p
                  className={`mt-3 text-lg font-bold ${
                    isDefect
                      ? "text-red-600"
                      : "text-green-600"
                  }`}
                >
                  {isDefect
                    ? "DEFECT"
                    : "GOOD"}
                </p>

              </div>

            </div>

            {/* ==================================================
                DETECTION DETAILS
            ================================================== */}

            <div className="rounded-xl border border-slate-200 bg-white p-6">

              <h3 className="text-lg font-bold text-slate-900">
                Detection Details
              </h3>

              {/* ------------------------------------------------
                  NO DETECTIONS
              ------------------------------------------------- */}

              {detections.length === 0 && (
                <div className="mt-5 rounded-lg bg-green-50 p-4 text-sm text-green-700">
                  No defects detected. Product passed inspection.
                </div>
              )}

              {/* ------------------------------------------------
                  DETECTIONS
              ------------------------------------------------- */}

              {detections.map(
                (detection, index) => {

                  const label =
                    getDetectionLabel(
                      detection
                    );

                  const yoloConfidence =
                    getYoloConfidence(
                      detection
                    );

                  const classificationConfidence =
                    getClassificationConfidence(
                      detection
                    );

                  return (
                    <div
                      key={index}
                      className="mt-5"
                    >

                      {/* ----------------------------------------
                          DEFECT TYPE
                      ----------------------------------------- */}

                      <div className="flex items-center justify-between border-b border-slate-100 py-4">

                        <span className="text-sm text-slate-500">
                          Defect Type
                        </span>

                        <span className="font-semibold text-slate-900">
                          {label}
                        </span>

                      </div>

                      {/* ----------------------------------------
                          YOLO CONFIDENCE
                      ----------------------------------------- */}

                      <div className="flex items-center justify-between border-b border-slate-100 py-4">

                        <span className="text-sm text-slate-500">
                          YOLO Confidence
                        </span>

                        <span className="font-semibold text-slate-900">
                          {formatConfidence(
                            yoloConfidence
                          )}
                        </span>

                      </div>

                      {/* ----------------------------------------
                          CLASSIFICATION CONFIDENCE
                      ----------------------------------------- */}

                      {classificationConfidence !==
                        null && (
                        <div className="flex items-center justify-between border-b border-slate-100 py-4">

                          <span className="text-sm text-slate-500">
                            Classification Confidence
                          </span>

                          <span className="font-semibold text-slate-900">
                            {formatConfidence(
                              classificationConfidence
                            )}
                          </span>

                        </div>
                      )}

                      {/* ----------------------------------------
                          SEVERITY SCORE
                      ----------------------------------------- */}

                      {detection.severity_score !==
                        undefined &&
                        detection.severity_score !==
                          null && (
                          <div className="flex items-center justify-between border-b border-slate-100 py-4">

                            <span className="text-sm text-slate-500">
                              Severity Score
                            </span>

                            <span className="font-semibold text-slate-900">
                              {Number(
                                detection.severity_score
                              ).toFixed(2)}
                            </span>

                          </div>
                        )}

                      {/* ----------------------------------------
                          SEVERITY LEVEL
                      ----------------------------------------- */}

                      {detection.severity_level && (
                        <div className="flex items-center justify-between py-4">

                          <span className="text-sm text-slate-500">
                            Severity Level
                          </span>

                          <span
                            className={`rounded-full px-4 py-1 text-sm font-semibold ${
                              detection.severity_level ===
                              "Critical"
                                ? "bg-red-100 text-red-700"
                                : detection.severity_level ===
                                  "High"
                                ? "bg-orange-100 text-orange-700"
                                : detection.severity_level ===
                                  "Medium"
                                ? "bg-yellow-100 text-yellow-700"
                                : "bg-green-100 text-green-700"
                            }`}
                          >
                            {
                              detection.severity_level
                            }
                          </span>

                        </div>
                      )}

                      {/* ----------------------------------------
                          RECOMMENDED ACTION
                      ----------------------------------------- */}

                      {detection.recommended_action && (
                        <div className="flex items-center justify-between border-t border-slate-100 py-4">

                          <span className="text-sm text-slate-500">
                            Recommended Action
                          </span>

                          <span
                            className={`font-semibold ${
                              detection.recommended_action ===
                              "Reject"
                                ? "text-red-600"
                                : detection.recommended_action ===
                                  "Rework"
                                ? "text-orange-600"
                                : detection.recommended_action ===
                                  "Review"
                                ? "text-yellow-600"
                                : "text-green-600"
                            }`}
                          >
                            {
                              detection.recommended_action
                            }
                          </span>

                        </div>
                      )}

                      {/* ----------------------------------------
                          MANUAL REVIEW
                      ----------------------------------------- */}

                      {detection.manual_review !==
                        undefined && (
                        <div className="flex items-center justify-between border-t border-slate-100 py-4">

                          <span className="text-sm text-slate-500">
                            Manual Review
                          </span>

                          <span
                            className={`font-semibold ${
                              detection.manual_review
                                ? "text-red-600"
                                : "text-green-600"
                            }`}
                          >
                            {detection.manual_review
                              ? "Required"
                              : "Not Required"}
                          </span>

                        </div>
                      )}

                    </div>
                  );
                }
              )}

            </div>

          </div>
        )}

      </section>

    </div>
  );
}

export default Inspection;