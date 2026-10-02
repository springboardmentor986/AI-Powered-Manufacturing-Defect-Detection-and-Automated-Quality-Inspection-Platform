import { useEffect, useMemo, useRef, useState } from "react";
import api from "../services/api";
import Sidebar from "../components/Sidebar";

const CATEGORIES = [
  "bottle", "cable", "capsule", "carpet", "grid", "hazelnut", "leather",
  "metal_nut", "pill", "screw", "tile", "toothbrush", "transistor", "wood", "zipper",
];

const title = (value) => value.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());

function CameraBatch() {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const [category, setCategory] = useState("bottle");
  const [cameraOn, setCameraOn] = useState(false);
  const [cameraError, setCameraError] = useState("");
  const [capturing, setCapturing] = useState(false);
  const [batchFiles, setBatchFiles] = useState([]);
  const [batchRunning, setBatchRunning] = useState(false);
  const [batchResult, setBatchResult] = useState(null);
  const [frameResult, setFrameResult] = useState(null);
  const [cameraInspectionIds, setCameraInspectionIds] = useState([]);
  const [clearingCameraHistory, setClearingCameraHistory] = useState(false);

  useEffect(() => () => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
  }, []);

  const startCamera = async () => {
    setCameraError("");
    if (!navigator.mediaDevices?.getUserMedia) {
      setCameraError(
        "Camera access is not supported in this browser or page context. Use batch image processing instead."
      );
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      streamRef.current = stream;
      setCameraOn(true);
      requestAnimationFrame(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      });
    } catch (error) {
      const messages = {
        NotAllowedError:
          "Camera permission was denied. Allow camera access for localhost and try again.",
        NotFoundError:
          "No camera was found on this device. You can still use batch image processing.",
        NotReadableError:
          "The camera is already being used by another application. Close it and try again.",
        SecurityError:
          "Camera access was blocked by browser security settings. Use localhost and allow camera access.",
      };
      setCameraError(
        messages[error.name] ||
          "Camera could not be started. You can still use batch image processing."
      );
    }
  };

  const stopCamera = () => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setCameraOn(false);
    void clearCameraHistory();
  };

  const clearCameraHistory = async () => {
    if (!cameraInspectionIds.length) {
      setFrameResult(null);
      return;
    }

    setClearingCameraHistory(true);
    try {
      await Promise.all(
        cameraInspectionIds.map((id) => api.delete(`/inspections/${id}`))
      );
      setCameraInspectionIds([]);
      setFrameResult(null);
      setCameraError("");
    } catch (error) {
      setCameraError(
        error.response?.data?.detail ||
          "Some camera inspections could not be deleted."
      );
    } finally {
      setClearingCameraHistory(false);
    }
  };

  const captureFrame = async () => {
    if (!videoRef.current?.videoWidth) return;
    setCapturing(true);
    try {
      const canvas = document.createElement("canvas");
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      canvas.getContext("2d").drawImage(videoRef.current, 0, 0);
      const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.92));
      const formData = new FormData();
      formData.append("file", blob, `camera-${Date.now()}.jpg`);
      const response = await api.post(
        `/inspections/upload?category=${encodeURIComponent(category)}`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } },
      );
      setFrameResult(response.data);
      setCameraInspectionIds((ids) => [
        ...ids,
        response.data.inspection_id,
      ]);
    } catch (error) {
      setCameraError(error.response?.data?.detail || "Camera frame inspection failed.");
    } finally {
      setCapturing(false);
    }
  };

  const processBatch = async () => {
    if (!batchFiles.length) return;
    setBatchRunning(true);
    setBatchResult(null);
    try {
      const formData = new FormData();
      batchFiles.forEach((file) => formData.append("files", file));
      const response = await api.post(
        `/inspections/batch-upload?category=${encodeURIComponent(category)}`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } },
      );
      setBatchResult(response.data);
    } catch (error) {
      setBatchResult({ error: error.response?.data?.detail || "Batch processing failed." });
    } finally {
      setBatchRunning(false);
    }
  };

  return (
    <div className="dashboard-layout">
      <Sidebar />
      <main className="dashboard-main camera-batch-main">
        <header className="dashboard-header"><div><span className="eyebrow">AUTOMATION WORKSPACE</span><h1>Camera &amp; Batch Processing</h1><p>Simulate a production camera or inspect a group of images in one run.</p></div></header>
        <div className="camera-batch-toolbar">
          <label>Product category<select value={category} onChange={(event) => setCategory(event.target.value)}>{CATEGORIES.map((item) => <option key={item} value={item}>{title(item)}</option>)}</select></label>
        </div>
        <div className="camera-batch-grid">
          <section className="camera-card">
            <div className="card-heading"><span className="eyebrow">📷 CAMERA INTEGRATION SIMULATION</span><h2>Live inspection station</h2><p>Use your webcam as a simulated production camera. Captured frames use the same AI pipeline as normal uploads.</p></div>
            <div className="camera-preview">
              <video
                ref={videoRef}
                autoPlay
                muted
                playsInline
                style={{ display: cameraOn ? "block" : "none" }}
              />
              {!cameraOn && <div className="camera-placeholder">Camera feed is stopped</div>}
            </div>
            {cameraError && <div className="camera-error">{cameraError}</div>}
            <div className="camera-actions">
              {!cameraOn ? <button onClick={startCamera}>Start camera</button> : <button onClick={stopCamera}>Stop camera</button>}
              <button onClick={captureFrame} disabled={!cameraOn || capturing}>{capturing ? "Inspecting frame..." : "Capture & inspect"}</button>
              <button className="camera-clear-button" onClick={clearCameraHistory} disabled={!cameraInspectionIds.length || clearingCameraHistory}>
                {clearingCameraHistory ? "Clearing..." : "Clear camera history"}
              </button>
            </div>
            {cameraInspectionIds.length > 0 && <div className="camera-session-note">This session has {cameraInspectionIds.length} saved frame inspection(s). Clear camera history removes only these records.</div>}
            {frameResult && <div className={`camera-result ${frameResult.result?.status === "DEFECT" ? "defect" : "good"}`}><strong>{frameResult.result?.status || "COMPLETED"}</strong><span>{frameResult.result?.defects?.length || 0} localized defects</span></div>}
          </section>
          <section className="camera-card">
            <div className="card-heading"><span className="eyebrow">📦 BATCH IMAGE PROCESSING</span><h2>Inspect multiple images</h2><p>Select up to 50 JPG, PNG, or WEBP images. Each image gets its own inspection record and result.</p></div>
            <input className="batch-file-input" type="file" accept="image/jpeg,image/png,image/webp" multiple onChange={(event) => { setBatchFiles(Array.from(event.target.files || [])); setBatchResult(null); }} />
            <div className="batch-count">{batchFiles.length ? `${batchFiles.length} image(s) selected` : "No images selected"}</div>
            <button onClick={processBatch} disabled={!batchFiles.length || batchRunning}>{batchRunning ? "Processing batch..." : "Start batch inspection"}</button>
            {batchResult?.error && <div className="camera-error"><strong>Batch processing failed</strong><span>{batchResult.error}</span></div>}
            {batchResult?.results && (
              <div className="batch-output">
                <div className="batch-summary">
                  <strong>{batchResult.completed} completed / {batchResult.failed} failed</strong>
                  <span className="batch-output-hint">All uploaded images and YOLO localization results</span>
                </div>
                <div className="batch-results-grid">
                  {batchResult.results.map((item) => (
                    <BatchResultCard
                      item={item}
                      file={batchFiles.find((candidate) => candidate.name === item.filename)}
                      key={`${item.inspection_id || item.filename}-${item.status}`}
                    />
                  ))}
                </div>
              </div>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}

function BatchResultCard({ item, file }) {
  const imageUrl = useMemo(
    () => (file ? URL.createObjectURL(file) : null),
    [file]
  );
  const [imageSize, setImageSize] = useState(null);
  const defects = Array.isArray(item.result?.defects) ? item.result.defects : [];

  useEffect(() => {
    return () => {
      if (imageUrl) URL.revokeObjectURL(imageUrl);
    };
  }, [imageUrl]);

  if (!file || !imageUrl) {
    return <div className="batch-image-missing">Original image is unavailable for preview.</div>;
  }

  return (
    <article className="batch-result-card">
      <div className="batch-viewer-heading">
        <strong>{item.filename}</strong>
        <span className={item.result?.status === "DEFECT" ? "text-defect" : "text-good"}>
          {item.result?.status || item.status}
        </span>
      </div>
      <div className="batch-image-stage">
        <img
          src={imageUrl}
          alt={`Batch result ${item.filename}`}
          onLoad={(event) => setImageSize({
            width: event.currentTarget.naturalWidth,
            height: event.currentTarget.naturalHeight,
          })}
        />
        {defects.map((defect, index) => {
          const box = defect.bbox;
          if (!box || !imageSize) return null;
          const x1 = Math.max(0, Number(box.x1) || 0);
          const y1 = Math.max(0, Number(box.y1) || 0);
          const x2 = Math.max(x1, Number(box.x2) || 0);
          const y2 = Math.max(y1, Number(box.y2) || 0);
          return (
            <div
              className="batch-image-box"
              key={`${item.inspection_id}-${index}`}
              style={{
                left: `${(x1 / imageSize.width) * 100}%`,
                top: `${(y1 / imageSize.height) * 100}%`,
                width: `${((x2 - x1) / imageSize.width) * 100}%`,
                height: `${((y2 - y1) / imageSize.height) * 100}%`,
              }}
            >
              <span>{defect.defect_type || "DEFECT"} {defect.confidence !== undefined ? `${(defect.confidence * 100).toFixed(1)}%` : ""}</span>
            </div>
          );
        })}
      </div>
      <div className="batch-card-footer">
        <span>{defects.length} YOLO box{defects.length === 1 ? "" : "es"}</span>
        {item.result?.quality_assessment?.severity?.level && (
          <span>{item.result.quality_assessment.severity.level} severity</span>
        )}
      </div>
      {item.result?.status === "DEFECT" && defects.length === 0 && (
        <div className="batch-image-missing">Autoencoder detected a defect, but YOLO returned no localization.</div>
      )}
    </article>
  );
}

export default CameraBatch;
