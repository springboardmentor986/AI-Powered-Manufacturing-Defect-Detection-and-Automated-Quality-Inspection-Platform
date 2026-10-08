import React from 'react';
import { 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Clock, 
  Eye, 
  Sparkles,
  Layers,
  ArrowUpRight
} from 'lucide-react';

export const InspectionTable = ({ records, onSelectRecord, onRefresh }) => {
  const getDecisionBadge = (decision) => {
    switch (decision?.toUpperCase()) {
      case 'PASS':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="w-3.5 h-3.5" /> PASS
          </span>
        );
      case 'FAIL':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/30">
            <XCircle className="w-3.5 h-3.5" /> FAIL
          </span>
        );
      case 'REVIEW':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30">
            <AlertTriangle className="w-3.5 h-3.5" /> REVIEW
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-300 dark:border-slate-700">
            <Clock className="w-3.5 h-3.5 animate-spin" /> PENDING
          </span>
        );
    }
  };

  const getSeverityBadge = (level, score) => {
    if (!level && score === undefined) return <span className="text-slate-400 text-xs font-mono">-</span>;
    const colors = {
      Low: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20',
      Medium: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20',
      High: 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20',
      Critical: 'bg-red-600/20 text-red-600 dark:text-red-300 border-red-500/40 animate-pulse',
    };
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono border ${colors[level] || 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-300 dark:border-slate-700'}`}>
        {level || 'Score'}: {score !== null && score !== undefined ? `${score}` : ''}
      </span>
    );
  };

  if (!records || records.length === 0) {
    return (
      <div className="glass-panel rounded-2xl p-12 text-center space-y-3">
        <div className="w-12 h-12 rounded-2xl bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 flex items-center justify-center mx-auto text-slate-400">
          <Layers className="w-6 h-6" />
        </div>
        <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">No inspection records found</h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto">
          Upload an image, run the conveyor camera simulator, or import samples from the MVTec AD dataset.
        </p>
      </div>
    );
  }

  return (
    <div className="glass-panel overflow-hidden border border-slate-200 dark:border-slate-800/80 transition-colors">
      <div className="overflow-x-auto">
        <table className="w-full text-left data-table">
          <thead className="bg-slate-50/90 dark:bg-industrial-900/60 border-b border-slate-200 dark:border-slate-800/60 text-slate-400 uppercase font-mono text-[10px] tracking-wider">
            <tr>
              <th className="py-3.5 px-4">Sample Image</th>
              <th className="py-3.5 px-4">Category / Split</th>
              <th className="py-3.5 px-4">Defect Classification</th>
              <th className="py-3.5 px-4">Quality Decision</th>
              <th className="py-3.5 px-4">Severity Assessment</th>
              <th className="py-3.5 px-4">Confidence</th>
              <th className="py-3.5 px-4">Timestamp</th>
              <th className="py-3.5 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 text-slate-700 dark:text-slate-300">
            {records.map((rec) => (
              <tr 
                key={rec.id} 
                className="hover:bg-slate-100/60 dark:hover:bg-industrial-900/50 transition-colors group cursor-pointer"
                onClick={() => onSelectRecord && onSelectRecord(rec)}
              >
                {/* Image Thumbnail */}
                <td className="py-3 px-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 rounded-xl bg-slate-100 dark:bg-industrial-950 border border-slate-200 dark:border-slate-800 overflow-hidden flex-shrink-0 relative group-hover:border-cyan-500/40 transition-colors">
                      <img
                        src={rec.thumbnail_url || rec.image_url}
                        alt={rec.original_filename}
                        className="w-full h-full object-cover"
                        loading="lazy"
                        onError={(e) => {
                          e.target.src = 'https://via.placeholder.com/100?text=IMG';
                        }}
                      />
                    </div>
                    <div className="truncate max-w-[140px]">
                      <div className="font-semibold text-slate-800 dark:text-slate-200 truncate font-mono text-[11px]" title={rec.original_filename}>
                        {rec.original_filename}
                      </div>
                      <div className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">
                        {rec.image_width}x{rec.image_height} • {rec.file_format}
                      </div>
                    </div>
                  </div>
                </td>

                {/* Category & Split */}
                <td className="py-3 px-4">
                  <div className="space-y-1">
                    <span className="inline-block font-mono text-[11px] font-semibold text-cyan-600 dark:text-cyan-400 bg-cyan-500/10 border border-cyan-500/20 px-2 py-0.5 rounded capitalize">
                      {rec.category}
                    </span>
                    <div className="text-[10px] text-slate-500 dark:text-slate-400 capitalize">
                      {rec.split}
                    </div>
                  </div>
                </td>

                {/* Defect Classification */}
                <td className="py-3 px-4">
                  <span className={`font-mono text-xs ${
                    rec.defect_type === 'good' 
                      ? 'text-emerald-600 dark:text-emerald-400 font-semibold' 
                      : rec.defect_type === 'unclassified' 
                        ? 'text-slate-500 dark:text-slate-400' 
                        : 'text-rose-600 dark:text-rose-400 font-semibold'
                  }`}>
                    {rec.defect_type}
                  </span>
                </td>

                {/* Quality Decision */}
                <td className="py-3 px-4">
                  {getDecisionBadge(rec.quality_decision)}
                </td>

                {/* Severity */}
                <td className="py-3 px-4">
                  {getSeverityBadge(rec.severity_level, rec.severity_score)}
                </td>

                {/* Confidence */}
                <td className="py-3 px-4 font-mono text-xs text-slate-700 dark:text-slate-300">
                  {rec.confidence_score !== null && rec.confidence_score !== undefined ? (
                    <div className="flex items-center space-x-1.5">
                      <div className="w-12 bg-slate-200 dark:bg-slate-800 rounded-full h-1.5 overflow-hidden">
                        <div 
                          className="bg-cyan-500 dark:bg-cyan-400 h-full rounded-full" 
                          style={{ width: `${Math.round(rec.confidence_score * 100)}%` }}
                        />
                      </div>
                      <span>{Math.round(rec.confidence_score * 100)}%</span>
                    </div>
                  ) : (
                    <span className="text-slate-400">-</span>
                  )}
                </td>

                {/* Timestamp */}
                <td className="py-3 px-4 font-mono text-[11px] text-slate-500 dark:text-slate-400">
                  {new Date(rec.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                </td>

                {/* Actions */}
                <td className="py-3 px-4 text-right">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectRecord && onSelectRecord(rec);
                    }}
                    className="p-1.5 rounded-lg bg-slate-100 hover:bg-cyan-500/20 dark:bg-industrial-800 dark:hover:bg-cyan-500/20 text-slate-700 dark:text-slate-300 hover:text-cyan-600 dark:hover:text-cyan-400 border border-slate-200 dark:border-slate-700 transition-colors inline-flex items-center gap-1 text-[11px] font-medium"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>Inspect</span>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
