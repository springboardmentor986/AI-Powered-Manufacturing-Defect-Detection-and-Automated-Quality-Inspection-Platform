import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Clock, 
  Layers, 
  Scan, 
  TrendingUp, 
  Zap, 
  FolderArchive,
  RefreshCw,
  ArrowUpRight,
  ShieldCheck,
  ShieldAlert,
  Cpu,
  BarChart3,
  Sliders,
  FileCheck,
  Download,
  AlertOctagon,
  PieChart,
  DollarSign,
  FileText,
  Printer,
  X
} from 'lucide-react';
import { dashboardAPI } from '../api/client';
import { StatCard } from '../components/StatCard';
import { InspectionTable } from '../components/InspectionTable';
import { RoleHeaderBanner } from '../components/RoleHeaderBanner';
import { useAuth, ROLES } from '../context/AuthContext';

export const DashboardPage = ({ 
  onSelectRecord, 
  onOpenUpload, 
  onOpenSimulator, 
  onOpenDataset,
  setActiveTab 
}) => {
  const { user } = useAuth();
  const role = user?.role || ROLES.QUALITY_ENGINEER;

  const [stats, setStats] = useState(null);
  const [batches, setBatches] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [trends, setTrends] = useState(null);
  const [qualityReport, setQualityReport] = useState(null);
  const [showReportModal, setShowReportModal] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [statsRes, batchesRes, analyticsRes, trendsRes] = await Promise.all([
        dashboardAPI.getKPIStats(),
        dashboardAPI.getBatches(),
        dashboardAPI.getAnalytics(),
        dashboardAPI.getTrends()
      ]);
      setStats(statsRes.data);
      setBatches(batchesRes.data);
      setAnalytics(analyticsRes.data);
      setTrends(trendsRes.data);
    } catch (err) {
      console.error('Failed to fetch dashboard data', err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenReportModal = async () => {
    try {
      const res = await dashboardAPI.getQualityReport();
      setQualityReport(res.data);
      setShowReportModal(true);
    } catch (err) {
      console.error('Failed to generate production quality report', err);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  return (
    <div className="space-y-6 animate-enter">
      {/* 1. Dynamic Role Header Banner */}
      <RoleHeaderBanner
        onOpenUpload={onOpenUpload}
        onOpenSimulator={onOpenSimulator}
        onOpenDataset={onOpenDataset}
        setActiveTab={setActiveTab}
        stationSync={stats?.station_sync_percentage ?? 100}
      />

      {/* ========================================================================= */}
      {/* ROLE 1: QUALITY ENGINEER DASHBOARD VIEW */}
      {/* ========================================================================= */}
      {role === ROLES.QUALITY_ENGINEER && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title="Station Inspections"
              value={stats ? stats.total_inspections : '--'}
              icon={Scan}
              color="cyan"
              subtext="Total processed product images"
              badge="Live Line"
            />
            <StatCard
              title="Station Compliance Pass"
              value={stats ? `${stats.pass_rate_percentage}%` : '--'}
              icon={CheckCircle2}
              color="emerald"
              subtext={`${stats?.total_passed || 0} units approved`}
              badge="Target > 90%"
            />
            <StatCard
              title="Defects Flagged"
              value={stats ? stats.total_failed : '--'}
              icon={XCircle}
              color="rose"
              subtext={`${stats?.total_failed || 0} units rejected`}
              badge="Immediate Action"
            />
            <StatCard
              title="MVTec Explorer"
              value={stats ? `${stats.categories_covered}/15` : '--'}
              icon={Layers}
              color="cyan"
              subtext="Active category profiles"
              badge={stats?.total_dataset_samples ? `${stats.total_dataset_samples.toLocaleString()} Samples` : 'MVTec AD'}
            />
          </div>

          {/* Quick Actions & Pareto Root Causes */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-7 glass-panel p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
                <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-cyan-500" />
                  Top Defect Classes (Pareto 80/20)
                </h3>
                <span className="text-[11px] font-mono text-cyan-600 dark:text-cyan-400 font-semibold">
                  Optical Frequency
                </span>
              </div>

              <div className="space-y-3">
                {analytics?.pareto_defects && analytics.pareto_defects.length > 0 ? (
                  analytics.pareto_defects.slice(0, 5).map((p, idx) => (
                    <div key={idx} className="space-y-1">
                      <div className="flex justify-between text-xs font-mono">
                        <span className="font-semibold text-slate-800 dark:text-slate-200 capitalize">
                          {p.defect_type.replace('_', ' ')}
                        </span>
                        <span className="text-slate-500">
                          {p.count} units ({p.percentage}%) • Cumulative: {p.cumulative_percentage}%
                        </span>
                      </div>
                      <div className="w-full bg-slate-100 dark:bg-industrial-900 h-2 rounded-full overflow-hidden">
                        <div 
                          className="bg-gradient-to-r from-cyan-500 to-rose-500 h-full rounded-full transition-all duration-500"
                          style={{ width: `${Math.max(p.percentage, 8)}%` }}
                        />
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-6 text-slate-400 text-xs">No defects recorded yet.</div>
                )}
              </div>
            </div>

            <div className="lg:col-span-5 glass-panel p-6 space-y-4 flex flex-col justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2 border-b border-slate-100 dark:border-slate-800 pb-3">
                  <Zap className="w-4 h-4 text-amber-500" />
                  Live Line Controls
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-3 leading-relaxed">
                  Trigger high-speed optical inspection on simulated conveyor belt, acquisition feed, or import verified MVTec AD samples.
                </p>
              </div>

              <div className="space-y-2.5 pt-2">
                <button
                  onClick={onOpenSimulator}
                  className="w-full py-2.5 px-4 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs shadow-md shadow-cyan-600/20 transition-all flex items-center justify-center gap-2"
                >
                  <Scan className="w-4 h-4" /> Launch Live Conveyor Simulator
                </button>
                <button
                  onClick={onOpenUpload}
                  className="w-full py-2.5 px-4 rounded-xl bg-slate-100 dark:bg-industrial-900 hover:bg-slate-200 dark:hover:bg-industrial-800 text-slate-800 dark:text-slate-200 font-semibold text-xs border border-slate-200 dark:border-slate-700 transition-all flex items-center justify-center gap-2"
                >
                  <Layers className="w-4 h-4 text-cyan-500" /> Upload Inspection Batch
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* ROLE 2: FACTORY SUPERVISOR DASHBOARD VIEW */}
      {/* ========================================================================= */}
      {role === ROLES.FACTORY_SUPERVISOR && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title="Line Yield Efficiency"
              value={stats ? `${stats.pass_rate_percentage}%` : '--'}
              icon={TrendingUp}
              color="amber"
              subtext="First-pass manufacturing yield"
              badge="Shift Target 95%"
            />
            <StatCard
              title="Active Production Batches"
              value={stats?.active_batches ?? batches.length ?? 0}
              icon={Layers}
              color="amber"
              subtext="Conveyor lines monitored"
              badge="Operations"
            />
            <StatCard
              title="High Severity Alerts"
              value={stats?.high_severity_alerts ?? stats?.total_failed ?? 0}
              icon={AlertOctagon}
              color="rose"
              subtext="Requires supervisor review"
              badge="High Risk"
            />
            <StatCard
              title="Inspection Latency"
              value={stats?.average_inference_latency_ms ? `~${stats.average_inference_latency_ms} ms` : '~27 ms'}
              icon={Cpu}
              color="emerald"
              subtext="Optical inference throughput"
              badge="High Speed"
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-8 glass-panel p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <Layers className="w-4 h-4 text-amber-500" />
                    Production Batches & Line Status
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">Line batch throughput and yield stats.</p>
                </div>
                <button
                  onClick={onOpenUpload}
                  className="px-3 py-1.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold shadow-md shadow-amber-600/20 transition-all"
                >
                  + New Batch
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left data-table">
                  <thead className="text-[10px] text-slate-400 uppercase tracking-wider border-b border-slate-100 dark:border-slate-800">
                    <tr>
                      <th className="py-2.5 px-3">Batch Name</th>
                      <th className="py-2.5 px-3">Category</th>
                      <th className="py-2.5 px-3">Progress</th>
                      <th className="py-2.5 px-3">Yield Count</th>
                      <th className="py-2.5 px-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80 text-slate-700 dark:text-slate-300">
                    {batches.length > 0 ? (
                      batches.map(b => (
                        <tr key={b.id} className="hover:bg-slate-50 dark:hover:bg-industrial-900/50 transition-colors">
                          <td className="py-3 px-3 font-bold text-slate-900 dark:text-slate-100 font-mono text-xs">{b.batch_name}</td>
                          <td className="py-3 px-3 capitalize text-cyan-600 dark:text-cyan-400 font-semibold">{b.category || 'general'}</td>
                          <td className="py-3 px-3">
                            <div className="space-y-1">
                              <span className="text-[11px] font-mono text-slate-600 dark:text-slate-300">
                                {b.processed_images} / {b.total_images} items
                              </span>
                              <div className="w-28 bg-slate-100 dark:bg-industrial-900 h-1.5 rounded-full overflow-hidden">
                                <div 
                                  className="bg-amber-500 h-full rounded-full transition-all duration-500"
                                  style={{ width: `${b.total_images > 0 ? Math.round((b.processed_images / b.total_images) * 100) : 0}%` }}
                                />
                              </div>
                            </div>
                          </td>
                          <td className="py-3 px-3 text-xs font-mono">
                            <span className="text-emerald-600 dark:text-emerald-400 font-bold">{b.pass_count} Pass</span>
                            <span className="text-slate-400 mx-1.5">•</span>
                            <span className="text-rose-600 dark:text-rose-400 font-bold">{b.fail_count} Fail</span>
                          </td>
                          <td className="py-3 px-3">
                            <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                              b.status === 'COMPLETED'
                                ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30'
                                : b.status === 'PROCESSING'
                                ? 'bg-cyan-500/15 text-cyan-600 dark:text-cyan-400 border-cyan-500/30'
                                : 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30'
                            }`}>
                              {b.status}
                            </span>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={5} className="py-6 text-center text-slate-400 text-xs">No active batches recorded yet.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Severity Risk Tier Distribution */}
            <div className="lg:col-span-4 glass-panel p-6 space-y-4">
              <div className="border-b border-slate-100 dark:border-slate-800 pb-3">
                <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-amber-500" />
                  Severity Risk Tiers (Section 5)
                </h3>
              </div>

              <div className="space-y-2 text-xs font-mono">
                <div className="p-2.5 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex justify-between items-center">
                  <div>
                    <span className="text-emerald-600 dark:text-emerald-400 font-bold block">Low Severity (0-39)</span>
                    <span className="text-[10px] text-slate-400">PASS • Normal tolerance ({analytics?.severity_risk_distribution?.low?.percentage ?? 0}%)</span>
                  </div>
                  <span className="text-slate-900 dark:text-white font-black text-sm">
                    {analytics?.severity_risk_distribution?.low?.count ?? 0}
                  </span>
                </div>
                <div className="p-2.5 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex justify-between items-center">
                  <div>
                    <span className="text-amber-600 dark:text-amber-400 font-bold block">Medium Concern (40-59)</span>
                    <span className="text-[10px] text-slate-400">REVIEW • Supervisor sign-off ({analytics?.severity_risk_distribution?.medium?.percentage ?? 0}%)</span>
                  </div>
                  <span className="text-slate-900 dark:text-white font-black text-sm">
                    {analytics?.severity_risk_distribution?.medium?.count ?? 0}
                  </span>
                </div>
                <div className="p-2.5 rounded-2xl bg-orange-500/10 border border-orange-500/20 flex justify-between items-center">
                  <div>
                    <span className="text-orange-600 dark:text-orange-400 font-bold block">High Risk (60-79)</span>
                    <span className="text-[10px] text-slate-400">FAIL • Route to rework ({analytics?.severity_risk_distribution?.high?.percentage ?? 0}%)</span>
                  </div>
                  <span className="text-slate-900 dark:text-white font-black text-sm">
                    {analytics?.severity_risk_distribution?.high?.count ?? 0}
                  </span>
                </div>
                <div className="p-2.5 rounded-2xl bg-rose-500/10 border border-rose-500/20 flex justify-between items-center">
                  <div>
                    <span className="text-rose-600 dark:text-rose-400 font-bold block">Critical Defect (80-100)</span>
                    <span className="text-[10px] text-slate-400">FAIL & SCRAP • Immediate line scrap ({analytics?.severity_risk_distribution?.critical?.percentage ?? 0}%)</span>
                  </div>
                  <span className="text-slate-900 dark:text-white font-black text-sm">
                    {analytics?.severity_risk_distribution?.critical?.count ?? 0}
                  </span>
                </div>
              </div>

              <button
                onClick={handleOpenReportModal}
                className="w-full py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold shadow-md shadow-amber-600/20 transition-all flex items-center justify-center gap-2"
              >
                <FileText className="w-3.5 h-3.5" /> Generate Quality Audit Report
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* ROLE 3: PRODUCTION MANAGER DASHBOARD VIEW */}
      {/* ========================================================================= */}
      {role === ROLES.PRODUCTION_MANAGER && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title="Plant Quality Yield"
              value={stats ? `${stats.pass_rate_percentage}%` : '--'}
              icon={TrendingUp}
              color="purple"
              subtext="First-pass manufacturing yield"
              badge="Yield KPI"
            />
            <StatCard
              title="Critical Rejection Rate"
              value={stats ? `${stats.defect_rate_percentage}%` : '--'}
              icon={XCircle}
              color="rose"
              subtext="Scrap & containment volume"
              badge="Risk Matrix"
            />
            <StatCard
              title="Scrap Cost Impact"
              value={analytics?.financial_impact ? `$${analytics.financial_impact.total_quality_loss_usd}` : '$0.00'}
              icon={DollarSign}
              color="purple"
              subtext={`ROI Multiplier: ${analytics?.financial_impact?.roi_multiplier || 18}x`}
              badge="Financial KPI"
            />
            <StatCard
              title="Executive Compliance"
              value={stats?.executive_compliance_percentage ? `${stats.executive_compliance_percentage}%` : '100%'}
              icon={ShieldCheck}
              color="emerald"
              subtext="Tamper-evident audit logs"
              badge="Verified"
            />
          </div>

          {/* 15-Category Quality Performance Matrix */}
          <div className="glass-panel p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-purple-500" />
                  15-Category Industrial Quality Matrix (MVTec AD Benchmark)
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Cross-category quality pass rate, average severity score, and health rating.
                </p>
              </div>

              <button
                onClick={handleOpenReportModal}
                className="px-3.5 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs shadow-md shadow-purple-600/20 transition-all flex items-center gap-1.5"
              >
                <FileText className="w-3.5 h-3.5" /> Executive Quality Report
              </button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 font-mono text-xs">
              {analytics?.category_matrix && analytics.category_matrix.length > 0 ? (
                analytics.category_matrix.map(c => (
                  <div 
                    key={c.category}
                    className="p-3 rounded-2xl bg-white dark:bg-industrial-950 border border-slate-200 dark:border-slate-800 text-center shadow-xs hover:border-purple-500/50 transition-all hover:scale-[1.02] flex flex-col justify-between"
                  >
                    <div>
                      <span className="text-[11px] text-slate-700 dark:text-slate-300 uppercase font-black tracking-wider block truncate">
                        {c.category}
                      </span>
                      <span className="text-base font-black text-slate-900 dark:text-white mt-1 block">
                        {c.total_inspected > 0 ? `${c.pass_rate_percentage}% Yield` : 'Standby'}
                      </span>
                      <span className="text-[10px] text-slate-400 block mt-0.5">
                        {c.total_inspected > 0 
                          ? `${c.pass_count}P / ${c.fail_count}F (${c.total_inspected} total)`
                          : `${c.dataset_sample_size || 0} dataset refs`
                        }
                      </span>
                    </div>
                    <div className="mt-2">
                      <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full inline-block ${
                        c.health_status === 'EXCELLENT' ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20' :
                        c.health_status === 'ACCEPTABLE' ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20' :
                        c.health_status === 'STANDBY' ? 'bg-slate-500/10 text-slate-500 dark:text-slate-400 border border-slate-500/20' :
                        'bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20'
                      }`}>
                        {c.health_status}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="col-span-5 text-center py-6 text-slate-400">Loading benchmark matrix...</div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* RECENT INSPECTIONS TABLE */}
      <div className="space-y-3 pt-1">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900 dark:text-white tracking-tight flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-500" />
            Live Inspection Stream
          </h2>
          <span className="text-[11px] text-slate-400 dark:text-slate-500 font-mono">
            {stats?.recent_inspections?.length || 0} records
          </span>
        </div>

        <InspectionTable
          records={stats?.recent_inspections || []}
          onSelectRecord={onSelectRecord}
          onRefresh={fetchDashboardData}
        />
      </div>

      {/* ========================================================================= */}
      {/* MODAL: PRODUCTION QUALITY AUDIT REPORT (MILESTONE 3) */}
      {/* ========================================================================= */}
      {showReportModal && qualityReport && (
        <div className="fixed inset-0 z-50 bg-black/75 dark:bg-black/85 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-white dark:bg-industrial-950 w-full max-w-4xl max-h-[90vh] rounded-3xl border border-slate-200 dark:border-slate-800 shadow-2xl overflow-hidden flex flex-col">
            
            {/* Header */}
            <div className="p-5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-industrial-900/50">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-600 dark:text-purple-400">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                    Production Quality & Defect Intelligence Report
                  </h3>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">
                    Report ID: {qualityReport.report_id} • Location: {qualityReport.plant_location}
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => window.print()}
                  className="px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-industrial-800 hover:bg-slate-200 dark:hover:bg-industrial-700 text-xs font-semibold text-slate-700 dark:text-slate-200 transition-all flex items-center gap-1.5"
                >
                  <Printer className="w-3.5 h-3.5" /> Print / Save PDF
                </button>
                <button
                  onClick={() => setShowReportModal(false)}
                  className="p-1.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-6">
              
              {/* Executive Summary Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-center">
                <div className="p-3.5 rounded-2xl bg-slate-50 dark:bg-industrial-900/60 border border-slate-200 dark:border-slate-800">
                  <span className="text-[10px] text-slate-400 block">Total Inspected</span>
                  <span className="text-lg font-black text-slate-900 dark:text-white mt-1 block">
                    {qualityReport.executive_summary.total_inspected_units} units
                  </span>
                </div>
                <div className="p-3.5 rounded-2xl bg-slate-50 dark:bg-industrial-900/60 border border-slate-200 dark:border-slate-800">
                  <span className="text-[10px] text-slate-400 block">First-Pass Yield</span>
                  <span className="text-lg font-black text-emerald-600 dark:text-emerald-400 mt-1 block">
                    {qualityReport.executive_summary.first_pass_yield_percentage}%
                  </span>
                </div>
                <div className="p-3.5 rounded-2xl bg-slate-50 dark:bg-industrial-900/60 border border-slate-200 dark:border-slate-800">
                  <span className="text-[10px] text-slate-400 block">Defect Rate</span>
                  <span className="text-lg font-black text-rose-600 dark:text-rose-400 mt-1 block">
                    {qualityReport.executive_summary.defect_rate_percentage}%
                  </span>
                </div>
                <div className="p-3.5 rounded-2xl bg-slate-50 dark:bg-industrial-900/60 border border-slate-200 dark:border-slate-800">
                  <span className="text-[10px] text-slate-400 block">Compliance Status</span>
                  <span className="text-xs font-bold text-cyan-600 dark:text-cyan-400 mt-2 block">
                    {qualityReport.executive_summary.compliance_status}
                  </span>
                </div>
              </div>

              {/* Financial Scrap & Rework Loss */}
              <div className="p-4 rounded-2xl bg-purple-500/10 border border-purple-500/20 space-y-2">
                <span className="text-xs font-bold text-purple-600 dark:text-purple-400 flex items-center gap-1.5">
                  <DollarSign className="w-4 h-4" /> Financial Quality Loss & Prevention Analysis
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 font-mono text-xs">
                  <div>
                    <span className="text-[10px] text-slate-400 block">Critical Scrap Cost:</span>
                    <strong className="text-rose-600 dark:text-rose-400">${qualityReport.financial_impact.scrap_cost_usd}</strong>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 block">Rework Labor Cost:</span>
                    <strong className="text-amber-600 dark:text-amber-400">${qualityReport.financial_impact.rework_cost_usd}</strong>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 block">Total Quality Loss:</span>
                    <strong className="text-slate-900 dark:text-white">${qualityReport.financial_impact.total_quality_loss_usd}</strong>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 block">Prevented Field Recalls:</span>
                    <strong className="text-emerald-600 dark:text-emerald-400">${qualityReport.financial_impact.estimated_prevented_field_loss_usd}</strong>
                  </div>
                </div>
              </div>

              {/* Operational Recommendations */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 font-mono">
                  Automated Quality Recommendations (Section 6)
                </h4>
                <div className="space-y-1.5">
                  {qualityReport.recommendations.map((rec, i) => (
                    <div key={i} className="p-2.5 rounded-xl bg-slate-50 dark:bg-industrial-900 border border-slate-200 dark:border-slate-800 text-xs text-slate-700 dark:text-slate-300 flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                      <span>{rec}</span>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          </div>
        </div>
      )}
    </div>
  );
};
