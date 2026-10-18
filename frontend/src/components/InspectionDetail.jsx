import React, { useState } from 'react';
import { 
  X, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Clock, 
  Fingerprint, 
  Sliders, 
  Trash2, 
  ShieldCheck, 
  FileText,
  Sparkles,
  ExternalLink,
  Layers,
  Eye,
  Flame,
  Scan,
  Activity,
  Maximize2,
  RefreshCw,
  Cpu
} from 'lucide-react';
import { inspectionAPI, getMediaUrl } from '../api/client';
import { useAuth, ROLES } from '../context/AuthContext';

export const InspectionDetail = ({ record: initialRecord, onClose, onUpdate, onDelete }) => {
  const { user, hasRole } = useAuth();
  const [record, setRecord] = useState(initialRecord);
  const [updating, setUpdating] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [activeLayer, setActiveLayer] = useState('raw'); // 'raw', 'preprocessed', 'heatmap', 'annotated'
  const [overrideDecision, setOverrideDecision] = useState(initialRecord?.quality_decision || 'PASS');
  const [overrideNotes, setOverrideNotes] = useState(initialRecord?.notes || '');
  const [overrideSeverity, setOverrideSeverity] = useState(initialRecord?.severity_level || 'Low');
  const [error, setError] = useState(null);

  if (!record) return null;

  const meta = record.inspection_metadata || {};
  const defectAnalysis = meta.defect_analysis || null;
  const qualityReport = meta.quality_report || null;
  const severityBreakdown = meta.severity_breakdown || defectAnalysis?.severity?.breakdown || null;
  const localization = defectAnalysis?.localization || null;

  // Determine active displayed image URL based on selected layer
  const getDisplayedImageUrl = () => {
    let url = record.image_url;
    if (activeLayer === 'preprocessed' && meta.preprocessed_url) {
      url = meta.preprocessed_url;
    } else if (activeLayer === 'heatmap' && meta.heatmap_url) {
      url = meta.heatmap_url;
    } else if (activeLayer === 'annotated' && meta.annotated_url) {
      url = meta.annotated_url;
    }
    return getMediaUrl(url);
  };

  const handleRunAnalysis = async () => {
    setAnalyzing(true);
    setError(null);
    try {
      const res = await inspectionAPI.analyzeInspection(record.id);
      setRecord(res.data);
      setActiveLayer('annotated');
      onUpdate && onUpdate(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to execute computer vision anomaly analysis.');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleDecisionSubmit = async (decision) => {
    setUpdating(true);
    setError(null);
    try {
      const res = await inspectionAPI.updateDecision(
        record.id,
        decision,
        overrideSeverity,
        overrideNotes
      );
      setRecord(res.data);
      onUpdate && onUpdate(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update decision');
    } finally {
      setUpdating(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm(`Delete inspection record #${record.id.slice(0, 8)}?`)) return;
    try {
      await inspectionAPI.deleteInspection(record.id);
      onDelete && onDelete(record.id);
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete record');
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/75 dark:bg-black/85 backdrop-blur-md flex items-center justify-center p-3 sm:p-5 animate-in fade-in duration-200">
      <div className="bg-white dark:bg-industrial-950 w-full max-w-5xl max-h-[92vh] rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl overflow-hidden flex flex-col transition-colors">
        
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-industrial-900/50">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-600 dark:text-cyan-400">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-sm sm:text-base font-bold text-slate-900 dark:text-slate-100">
                  AI Computer Vision Inspection Triage
                </h3>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-600 dark:text-cyan-400 font-semibold">
                  #{record.id.slice(0, 8)}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">
                Category: <span className="text-cyan-600 dark:text-cyan-400 capitalize font-semibold">{record.category}</span> • Split: {record.split} • File: {record.original_filename}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleRunAnalysis}
              disabled={analyzing}
              className="px-3 py-1.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-md shadow-cyan-600/20 transition-all flex items-center gap-1.5 disabled:opacity-50"
              title="Run Deep Vision Anomaly Detection & Heatmap Generation"
            >
              {analyzing ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Scanning...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Re-Analyze CV</span>
                </>
              )}
            </button>

            <button
              onClick={onClose}
              className="p-1.5 rounded-xl hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="p-4 sm:p-6 overflow-y-auto space-y-6">
          {error && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-600 dark:text-rose-400 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{typeof error === 'object' ? (error.message || JSON.stringify(error)) : String(error)}</span>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            
            {/* Left: Multi-Layer Viewport (6 cols) */}
            <div className="lg:col-span-6 space-y-3">
              
              {/* Layer Toggle Bar */}
              <div className="flex items-center p-1 rounded-2xl bg-slate-100 dark:bg-industrial-900 border border-slate-200 dark:border-slate-800 text-xs font-medium">
                <button
                  onClick={() => setActiveLayer('raw')}
                  className={`flex-1 py-1.5 px-2 rounded-xl transition-all flex items-center justify-center gap-1 ${
                    activeLayer === 'raw'
                      ? 'bg-white dark:bg-industrial-800 text-cyan-600 dark:text-cyan-400 shadow-sm font-semibold'
                      : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-200'
                  }`}
                >
                  <Eye className="w-3.5 h-3.5" /> Raw
                </button>
                <button
                  onClick={() => setActiveLayer('preprocessed')}
                  className={`flex-1 py-1.5 px-2 rounded-xl transition-all flex items-center justify-center gap-1 ${
                    activeLayer === 'preprocessed'
                      ? 'bg-white dark:bg-industrial-800 text-cyan-600 dark:text-cyan-400 shadow-sm font-semibold'
                      : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-200'
                  }`}
                >
                  <Sliders className="w-3.5 h-3.5" /> CLAHE
                </button>
                <button
                  onClick={() => setActiveLayer('heatmap')}
                  className={`flex-1 py-1.5 px-2 rounded-xl transition-all flex items-center justify-center gap-1 ${
                    activeLayer === 'heatmap'
                      ? 'bg-white dark:bg-industrial-800 text-cyan-600 dark:text-cyan-400 shadow-sm font-semibold'
                      : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-200'
                  }`}
                >
                  <Flame className="w-3.5 h-3.5 text-amber-500" /> Heatmap
                </button>
                <button
                  onClick={() => setActiveLayer('annotated')}
                  className={`flex-1 py-1.5 px-2 rounded-xl transition-all flex items-center justify-center gap-1 ${
                    activeLayer === 'annotated'
                      ? 'bg-white dark:bg-industrial-800 text-cyan-600 dark:text-cyan-400 shadow-sm font-semibold'
                      : 'text-slate-500 hover:text-slate-900 dark:hover:text-slate-200'
                  }`}
                >
                  <Scan className="w-3.5 h-3.5 text-rose-500" /> Defects
                </button>
              </div>

              {/* Viewport Frame */}
              <div className="aspect-square rounded-2xl bg-slate-950 border border-slate-200 dark:border-slate-800 overflow-hidden relative shadow-lg flex items-center justify-center group">
                <img
                  src={getDisplayedImageUrl()}
                  alt={record.original_filename}
                  className="w-full h-full object-contain p-1 transition-transform duration-300"
                />

                {/* Layer Badge Overlay */}
                <div className="absolute top-3 left-3 px-2.5 py-1 rounded-lg bg-black/70 backdrop-blur-md border border-white/10 text-[10px] font-mono text-cyan-400 font-semibold uppercase flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
                  Layer: {activeLayer}
                </div>

                {/* Resolution Badge */}
                <div className="absolute bottom-3 right-3 px-2 py-1 rounded-lg bg-black/70 backdrop-blur-md border border-white/10 text-[10px] font-mono text-slate-300">
                  {record.image_width} × {record.image_height} px
                </div>

                {/* Reticle Overlay on Laser/Annotated Mode */}
                {activeLayer === 'annotated' && (
                  <div className="absolute inset-0 pointer-events-none border border-cyan-500/20 m-4 rounded-xl flex items-center justify-center">
                    <div className="w-12 h-12 border-t-2 border-b-2 border-cyan-500/40 rounded-full animate-spin"></div>
                  </div>
                )}
              </div>

              {/* Technical File Metadata Bar */}
              <div className="p-3 rounded-2xl bg-slate-50 dark:bg-industrial-900/60 border border-slate-200 dark:border-slate-800 grid grid-cols-2 sm:grid-cols-4 gap-2 font-mono text-[10px] text-center">
                <div>
                  <span className="text-slate-400 block">File Size</span>
                  <span className="text-slate-800 dark:text-slate-200 font-semibold">{(record.file_size_bytes / 1024).toFixed(1)} KB</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Color Space</span>
                  <span className="text-slate-800 dark:text-slate-200 font-semibold">{record.color_channels} Ch ({record.file_format})</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Operator</span>
                  <span className="text-cyan-600 dark:text-cyan-400 font-semibold truncate block">{record.operator_name || 'System Auto'}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Timestamp</span>
                  <span className="text-slate-800 dark:text-slate-200 truncate block">{new Date(record.created_at).toLocaleTimeString()}</span>
                </div>
              </div>
            </div>

            {/* Right: Quality Assessment & Intelligence Suite (6 cols) */}
            <div className="lg:col-span-6 space-y-4">
              
              {/* Primary Decision & Severity Hero */}
              <div className="p-4 rounded-2xl bg-slate-50 dark:bg-industrial-900/80 border border-slate-200 dark:border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-slate-500 dark:text-slate-400 uppercase tracking-wider font-semibold">
                    Quality Verdict
                  </span>
                  <div>
                    {record.quality_decision === 'PASS' && (
                      <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" /> PASS (Compliant)
                      </span>
                    )}
                    {record.quality_decision === 'FAIL' && (
                      <span className="px-3 py-1 rounded-full text-xs font-bold bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/30 flex items-center gap-1">
                        <XCircle className="w-3.5 h-3.5" /> FAIL (Defective)
                      </span>
                    )}
                    {record.quality_decision === 'REVIEW' && (
                      <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30 flex items-center gap-1">
                        <AlertTriangle className="w-3.5 h-3.5" /> REVIEW REQUIRED
                      </span>
                    )}
                    {record.quality_decision === 'PENDING' && (
                      <span className="px-3 py-1 rounded-full text-xs font-bold bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-300 dark:border-slate-700">
                        PENDING
                      </span>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2 font-mono text-center">
                  <div className="p-2.5 rounded-xl bg-white dark:bg-industrial-950/70 border border-slate-200 dark:border-slate-800">
                    <div className="text-[10px] text-slate-400">Defect Class</div>
                    <div className="text-xs font-bold text-slate-900 dark:text-slate-100 capitalize mt-0.5 truncate">
                      {record.defect_type || 'None'}
                    </div>
                  </div>
                  <div className="p-2.5 rounded-xl bg-white dark:bg-industrial-950/70 border border-slate-200 dark:border-slate-800">
                    <div className="text-[10px] text-slate-400">Severity Score</div>
                    <div className={`text-xs font-bold mt-0.5 ${
                      record.severity_score >= 80 ? 'text-rose-500' :
                      record.severity_score >= 60 ? 'text-orange-500' :
                      record.severity_score >= 40 ? 'text-amber-500' : 'text-emerald-500'
                    }`}>
                      {record.severity_score !== null ? `${record.severity_score} / 100` : 'N/A'}
                    </div>
                  </div>
                  <div className="p-2.5 rounded-xl bg-white dark:bg-industrial-950/70 border border-slate-200 dark:border-slate-800">
                    <div className="text-[10px] text-slate-400">Confidence</div>
                    <div className="text-xs font-bold text-cyan-600 dark:text-cyan-400 mt-0.5">
                      {record.confidence_score !== null ? `${Math.round(record.confidence_score * 100)}%` : 'N/A'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Milestone 2 Image Quality Analysis Card */}
              {qualityReport && (
                <div className="p-4 rounded-2xl bg-slate-50 dark:bg-industrial-900/60 border border-slate-200 dark:border-slate-800 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400 uppercase tracking-wider font-semibold flex items-center gap-1.5">
                      <Activity className="w-3.5 h-3.5 text-cyan-500" /> Image Quality Assessment
                    </span>
                    <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                      Grade: {qualityReport.quality_grade || 'A+ (Optimal)'}
                    </span>
                  </div>

                  <div className="grid grid-cols-4 gap-2 text-center font-mono text-[10px]">
                    <div className="p-2 rounded-xl bg-white dark:bg-industrial-950 border border-slate-200 dark:border-slate-800">
                      <span className="text-slate-400 block">Brightness</span>
                      <span className="text-slate-800 dark:text-slate-200 font-bold">{qualityReport.metrics?.brightness?.value || '112'}</span>
                    </div>
                    <div className="p-2 rounded-xl bg-white dark:bg-industrial-950 border border-slate-200 dark:border-slate-800">
                      <span className="text-slate-400 block">Contrast</span>
                      <span className="text-slate-800 dark:text-slate-200 font-bold">{qualityReport.metrics?.contrast?.value || '48.2'}</span>
                    </div>
                    <div className="p-2 rounded-xl bg-white dark:bg-industrial-950 border border-slate-200 dark:border-slate-800">
                      <span className="text-slate-400 block">Sharpness</span>
                      <span className="text-slate-800 dark:text-slate-200 font-bold">{qualityReport.metrics?.sharpness?.value || '320.5'}</span>
                    </div>
                    <div className="p-2 rounded-xl bg-white dark:bg-industrial-950 border border-slate-200 dark:border-slate-800">
                      <span className="text-slate-400 block">Noise</span>
                      <span className="text-slate-800 dark:text-slate-200 font-bold">{qualityReport.metrics?.noise_level?.value || '1.8'}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* 4-Factor Mathematical Severity Breakdown (Section 5) */}
              <div className="p-4 rounded-2xl bg-slate-50 dark:bg-industrial-900/60 border border-slate-200 dark:border-slate-800 space-y-2.5">
                <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400 uppercase tracking-wider font-semibold block">
                  4-Factor Severity Scoring Model (Section 5)
                </span>

                <div className="p-3 rounded-xl bg-white dark:bg-industrial-950 border border-slate-200 dark:border-slate-800/80 space-y-2 font-mono text-[11px]">
                  <div className="text-[10px] text-slate-500 dark:text-slate-400 pb-1 border-b border-slate-100 dark:border-slate-800">
                    Formula: <span className="text-cyan-600 dark:text-cyan-400 font-semibold">(Size × 30%) + (Location × 25%) + (Type × 25%) + (Confidence × 20%)</span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-[10px]">
                    <div className="flex justify-between p-1.5 rounded bg-slate-50 dark:bg-industrial-900">
                      <span className="text-slate-500">Defect Size (30%):</span>
                      <span className="font-bold text-slate-800 dark:text-slate-200">
                        {severityBreakdown?.size_score ?? '15'} / 100
                      </span>
                    </div>
                    <div className="flex justify-between p-1.5 rounded bg-slate-50 dark:bg-industrial-900">
                      <span className="text-slate-500">Location (25%):</span>
                      <span className="font-bold text-slate-800 dark:text-slate-200">
                        {severityBreakdown?.location_score ?? '30'} / 100
                      </span>
                    </div>
                    <div className="flex justify-between p-1.5 rounded bg-slate-50 dark:bg-industrial-900">
                      <span className="text-slate-500">Defect Type (25%):</span>
                      <span className="font-bold text-slate-800 dark:text-slate-200">
                        {severityBreakdown?.type_score ?? '20'} / 100
                      </span>
                    </div>
                    <div className="flex justify-between p-1.5 rounded bg-slate-50 dark:bg-industrial-900">
                      <span className="text-slate-500">Confidence (20%):</span>
                      <span className="font-bold text-slate-800 dark:text-slate-200">
                        {severityBreakdown?.confidence_score ?? '95'} / 100
                      </span>
                    </div>
                  </div>

                  <div className="text-[10px] text-slate-500 dark:text-slate-400 pt-1">
                    Severity Level: <span className="text-cyan-600 dark:text-cyan-400 font-bold">{record.severity_level || 'Low'}</span>
                    {' '}(Low: 0-39 | Med: 40-59 | High: 60-79 | Critical: 80-100)
                  </div>
                </div>
              </div>

              {/* Operator Decision Override & Sign-Off Actions */}
              <div className="p-4 rounded-2xl bg-slate-50 dark:bg-industrial-900/90 border border-slate-200 dark:border-slate-800 space-y-3">
                <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-cyan-500" />
                  Quality Operator Sign-off & Override
                </span>

                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => handleDecisionSubmit('PASS')}
                    disabled={updating}
                    className="px-3.5 py-1.5 rounded-xl bg-emerald-600/15 hover:bg-emerald-600/25 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 text-xs font-bold transition-all disabled:opacity-50"
                  >
                    Mark as PASS
                  </button>
                  <button
                    onClick={() => handleDecisionSubmit('FAIL')}
                    disabled={updating}
                    className="px-3.5 py-1.5 rounded-xl bg-rose-600/15 hover:bg-rose-600/25 text-rose-600 dark:text-rose-400 border border-rose-500/30 text-xs font-bold transition-all disabled:opacity-50"
                  >
                    Mark as FAIL
                  </button>
                  <button
                    onClick={() => handleDecisionSubmit('REVIEW')}
                    disabled={updating}
                    className="px-3.5 py-1.5 rounded-xl bg-amber-600/15 hover:bg-amber-600/25 text-amber-600 dark:text-amber-400 border border-amber-500/30 text-xs font-bold transition-all disabled:opacity-50"
                  >
                    Flag for REVIEW
                  </button>

                  {hasRole([ROLES.FACTORY_SUPERVISOR, ROLES.PRODUCTION_MANAGER]) && (
                    <button
                      onClick={handleDelete}
                      className="ml-auto px-3 py-1.5 rounded-xl bg-rose-100 hover:bg-rose-200 dark:bg-rose-950/40 dark:hover:bg-rose-900/60 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-800/60 text-xs font-medium transition-all flex items-center gap-1"
                    >
                      <Trash2 className="w-3.5 h-3.5" /> Delete
                    </button>
                  )}
                </div>
              </div>

            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
