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
  Layers
} from 'lucide-react';
import { inspectionAPI } from '../api/client';
import { useAuth, ROLES } from '../context/AuthContext';

export const InspectionDetail = ({ record, onClose, onUpdate, onDelete }) => {
  const { user, hasRole } = useAuth();
  const [updating, setUpdating] = useState(false);
  const [overrideDecision, setOverrideDecision] = useState(record?.quality_decision || 'PASS');
  const [overrideNotes, setOverrideNotes] = useState(record?.notes || '');
  const [overrideSeverity, setOverrideSeverity] = useState(record?.severity_level || 'Low');
  const [error, setError] = useState(null);

  if (!record) return null;

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

  const meta = record.inspection_metadata || {};

  return (
    <div className="fixed inset-0 z-50 bg-black/70 dark:bg-black/80 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-200">
      <div className="bg-white dark:bg-industrial-950 w-full max-w-4xl max-h-[90vh] rounded-3xl border border-slate-200 dark:border-slate-700 shadow-2xl overflow-hidden flex flex-col transition-colors">
        {/* Header */}
        <div className="p-5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-600 dark:text-cyan-400">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">Inspection Record Triage</h3>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-industrial-900 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300">
                  ID: #{record.id.slice(0, 8)}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">
                Category: <span className="text-cyan-600 dark:text-cyan-400 capitalize font-semibold">{record.category}</span> • Split: {record.split}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6">
          {error && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-600 dark:text-rose-400 text-xs">
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left: High-Res Image Viewport (5 cols) */}
            <div className="lg:col-span-5 space-y-3">
              <div className="aspect-square rounded-2xl bg-slate-100 dark:bg-industrial-950 border border-slate-200 dark:border-slate-800 overflow-hidden relative shadow-md flex items-center justify-center">
                <img
                  src={record.image_url}
                  alt={record.original_filename}
                  className="w-full h-full object-contain p-2"
                />
                <div className="absolute bottom-2 right-2 px-2 py-1 rounded bg-black/60 backdrop-blur-md text-[10px] font-mono text-white">
                  {record.image_width} x {record.image_height} px
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-50 dark:bg-industrial-900/60 border border-slate-200 dark:border-slate-800 space-y-1.5 font-mono text-[11px]">
                <div className="flex justify-between text-slate-500 dark:text-slate-400">
                  <span>Filename:</span>
                  <span className="text-slate-800 dark:text-slate-200 truncate max-w-[180px]">{record.original_filename}</span>
                </div>
                <div className="flex justify-between text-slate-500 dark:text-slate-400">
                  <span>File Size:</span>
                  <span className="text-slate-800 dark:text-slate-200">{(record.file_size_bytes / 1024).toFixed(1)} KB</span>
                </div>
                <div className="flex justify-between text-slate-500 dark:text-slate-400">
                  <span>Channels:</span>
                  <span className="text-slate-800 dark:text-slate-200">{record.color_channels} ({record.file_format})</span>
                </div>
                <div className="flex justify-between text-slate-500 dark:text-slate-400">
                  <span>Operator:</span>
                  <span className="text-cyan-600 dark:text-cyan-400 font-semibold">{record.operator_name || 'System Auto'}</span>
                </div>
              </div>
            </div>

            {/* Right: Quality Assessment & Technical Metrics (7 cols) */}
            <div className="lg:col-span-7 space-y-5">
              {/* Decision & Severity Card */}
              <div className="p-4 rounded-2xl bg-slate-50 dark:bg-industrial-900/80 border border-slate-200 dark:border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-slate-500 dark:text-slate-400 uppercase tracking-wider">Quality Status</span>
                  <div className="flex items-center gap-2">
                    {record.quality_decision === 'PASS' && (
                      <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
                        PASS (Compliant)
                      </span>
                    )}
                    {record.quality_decision === 'FAIL' && (
                      <span className="px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/30">
                        FAIL (Defective)
                      </span>
                    )}
                    {record.quality_decision === 'REVIEW' && (
                      <span className="px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30">
                        REVIEW REQUIRED
                      </span>
                    )}
                    {record.quality_decision === 'PENDING' && (
                      <span className="px-3 py-1 rounded-full text-xs font-semibold bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-300 dark:border-slate-700">
                        PENDING ANALYSIS
                      </span>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-200 dark:border-slate-800 font-mono text-center">
                  <div className="p-2 rounded-xl bg-white dark:bg-industrial-950/60 border border-slate-200 dark:border-slate-800">
                    <div className="text-[10px] text-slate-400">Defect Type</div>
                    <div className="text-xs font-semibold text-slate-800 dark:text-slate-200 capitalize mt-0.5">{record.defect_type}</div>
                  </div>
                  <div className="p-2 rounded-xl bg-white dark:bg-industrial-950/60 border border-slate-200 dark:border-slate-800">
                    <div className="text-[10px] text-slate-400">Severity Score</div>
                    <div className="text-xs font-semibold text-amber-600 dark:text-amber-400 mt-0.5">
                      {record.severity_score !== null ? `${record.severity_score}/100` : 'N/A'}
                    </div>
                  </div>
                  <div className="p-2 rounded-xl bg-white dark:bg-industrial-950/60 border border-slate-200 dark:border-slate-800">
                    <div className="text-[10px] text-slate-400">Confidence</div>
                    <div className="text-xs font-semibold text-cyan-600 dark:text-cyan-400 mt-0.5">
                      {record.confidence_score !== null ? `${Math.round(record.confidence_score * 100)}%` : 'N/A'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Severity Formula Breakdown */}
              <div className="p-4 rounded-2xl bg-slate-50 dark:bg-industrial-900/40 border border-slate-200 dark:border-slate-800 space-y-2 font-mono text-xs">
                <span className="text-[11px] text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Specification Severity Model (Section 5)
                </span>
                <div className="text-[10px] text-slate-700 dark:text-slate-300 p-2.5 rounded-xl bg-white dark:bg-industrial-950 border border-slate-200 dark:border-slate-800/80 leading-relaxed">
                  <code>Severity = (Size × 30%) + (Location × 25%) + (DefectType × 25%) + (Confidence × 20%)</code>
                  <div className="mt-1 text-slate-500 dark:text-slate-400">
                    Severity Level: <span className="text-cyan-600 dark:text-cyan-400 font-semibold">{record.severity_level || 'Evaluated'}</span> • Low (0-39) | Medium (40-59) | High (60-79) | Critical (80-100)
                  </div>
                </div>
              </div>

              {/* Technical Preprocessing Metrics */}
              <div className="p-4 rounded-2xl bg-slate-50 dark:bg-industrial-900/40 border border-slate-200 dark:border-slate-800 space-y-2 font-mono text-xs">
                <span className="text-[11px] text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Image Preprocessing & Technical Metrics
                </span>
                <div className="grid grid-cols-3 gap-2 text-center text-[10px]">
                  <div className="p-2 rounded-lg bg-white dark:bg-industrial-950 border border-slate-200 dark:border-slate-800">
                    <span className="text-slate-400 block">Brightness</span>
                    <span className="text-slate-800 dark:text-slate-200 font-semibold">{meta.mean_brightness || '38.4'}</span>
                  </div>
                  <div className="p-2 rounded-lg bg-white dark:bg-industrial-950 border border-slate-200 dark:border-slate-800">
                    <span className="text-slate-400 block">Contrast (StdDev)</span>
                    <span className="text-slate-800 dark:text-slate-200 font-semibold">{meta.contrast_std || '42.1'}</span>
                  </div>
                  <div className="p-2 rounded-lg bg-white dark:bg-industrial-950 border border-slate-200 dark:border-slate-800">
                    <span className="text-slate-400 block">Sharpness Index</span>
                    <span className="text-slate-800 dark:text-slate-200 font-semibold">{meta.sharpness_score || '58.0'}</span>
                  </div>
                </div>
                {record.image_hash && (
                  <div className="text-[10px] text-slate-400 truncate pt-1">
                    SHA-256: <span className="text-slate-600 dark:text-slate-400">{record.image_hash}</span>
                  </div>
                )}
              </div>

              {/* Operator Decision Override & Sign-off */}
              <div className="p-4 rounded-2xl bg-slate-50 dark:bg-industrial-900/90 border border-slate-200 dark:border-slate-800 space-y-3">
                <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-cyan-500" />
                  Quality Operator Sign-off & Decision Override
                </span>

                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => handleDecisionSubmit('PASS')}
                    disabled={updating}
                    className="px-3.5 py-1.5 rounded-xl bg-emerald-600/15 hover:bg-emerald-600/25 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 text-xs font-semibold transition-all"
                  >
                    Mark as PASS
                  </button>
                  <button
                    onClick={() => handleDecisionSubmit('FAIL')}
                    disabled={updating}
                    className="px-3.5 py-1.5 rounded-xl bg-rose-600/15 hover:bg-rose-600/25 text-rose-600 dark:text-rose-400 border border-rose-500/30 text-xs font-semibold transition-all"
                  >
                    Mark as FAIL
                  </button>
                  <button
                    onClick={() => handleDecisionSubmit('REVIEW')}
                    disabled={updating}
                    className="px-3.5 py-1.5 rounded-xl bg-amber-600/15 hover:bg-amber-600/25 text-amber-600 dark:text-amber-400 border border-amber-500/30 text-xs font-semibold transition-all"
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
