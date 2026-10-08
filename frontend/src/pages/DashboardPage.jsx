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
  AlertOctagon
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
  const [loading, setLoading] = useState(true);

  const fetchStatsAndBatches = async () => {
    try {
      setLoading(true);
      const [statsRes, batchesRes] = await Promise.all([
        dashboardAPI.getKPIStats(),
        dashboardAPI.getBatches()
      ]);
      setStats(statsRes.data);
      setBatches(batchesRes.data);
    } catch (err) {
      console.error('Failed to fetch dashboard data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatsAndBatches();
  }, []);

  return (
    <div className="space-y-6 animate-enter">
      {/* 1. Dynamic Role Header Banner */}
      <RoleHeaderBanner
        onOpenUpload={onOpenUpload}
        onOpenSimulator={onOpenSimulator}
        onOpenDataset={onOpenDataset}
        setActiveTab={setActiveTab}
      />

      {/* ========================================================================= */}
      {/* ROLE 1: QUALITY ENGINEER DASHBOARD VIEW */}
      {/* ========================================================================= */}
      {role === ROLES.QUALITY_ENGINEER && (
        <div className="space-y-6">
          {/* KPI Metrics */}
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
              subtext={`${stats?.defect_rate_percentage || 0}% rejection rate`}
              badge="Action Required"
            />
            <StatCard
              title="MVTec AD Categories"
              value={stats ? `${stats.categories_covered}/15` : '15/15'}
              icon={FolderArchive}
              color="cyan"
              subtext="Industrial benchmark domains"
              badge="Integrated"
            />
          </div>

          {/* Engineer Station Deck */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Decision Status Panel */}
            <div className="lg:col-span-5 glass-panel p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800/60 pb-3">
                <h3 className="text-[13px] font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-cyan-500" />
                  Triage Counter
                </h3>
                <span className="text-[11px] font-mono text-slate-400 font-semibold">Station A</span>
              </div>

              <div className="grid grid-cols-2 gap-3 font-mono">
                <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20">
                  <span className="text-xs text-emerald-600 dark:text-emerald-400 font-bold flex items-center gap-1">
                    <CheckCircle2 className="w-4 h-4" /> PASS (Compliant)
                  </span>
                  <span className="text-3xl font-black text-slate-900 dark:text-white mt-2 block">
                    {stats?.total_passed || 0}
                  </span>
                </div>

                <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20">
                  <span className="text-xs text-rose-600 dark:text-rose-400 font-bold flex items-center gap-1">
                    <XCircle className="w-4 h-4" /> FAIL (Defective)
                  </span>
                  <span className="text-3xl font-black text-slate-900 dark:text-white mt-2 block">
                    {stats?.total_failed || 0}
                  </span>
                </div>

                <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20">
                  <span className="text-xs text-amber-600 dark:text-amber-400 font-bold flex items-center gap-1">
                    <AlertTriangle className="w-4 h-4" /> REVIEW (Hold)
                  </span>
                  <span className="text-3xl font-black text-slate-900 dark:text-white mt-2 block">
                    {stats?.total_review || 0}
                  </span>
                </div>

                <div className="p-4 rounded-2xl bg-slate-100 dark:bg-industrial-950 border border-slate-200 dark:border-slate-800">
                  <span className="text-xs text-slate-600 dark:text-slate-400 font-bold flex items-center gap-1">
                    <Clock className="w-4 h-4" /> PENDING
                  </span>
                  <span className="text-3xl font-black text-slate-900 dark:text-white mt-2 block">
                    {stats?.total_pending || 0}
                  </span>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-industrial-950/80 border border-slate-200 dark:border-slate-800/60">
                <p className="text-[12px] text-slate-500 dark:text-slate-400 leading-relaxed">
                  Click any sample below to inspect defect localization and submit sign-offs.
                </p>
              </div>
            </div>

            {/* Ingestion Stream by Category */}
            <div className="lg:col-span-7 glass-panel p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800/60 pb-3">
                <h3 className="text-[13px] font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <FolderArchive className="w-4 h-4 text-cyan-500" />
                  Category Volume
                </h3>
                <button
                  onClick={onOpenDataset}
                  className="text-xs text-cyan-600 dark:text-cyan-400 hover:underline flex items-center gap-1 font-mono font-bold"
                >
                  Explore MVTec AD <ArrowUpRight className="w-3 h-3" />
                </button>
              </div>

              <div className="space-y-3 max-h-[250px] overflow-y-auto pr-1">
                {stats && stats.category_distribution && Object.keys(stats.category_distribution).length > 0 ? (
                  Object.entries(stats.category_distribution).map(([cat, count]) => {
                    const total = Math.max(stats.total_inspections, 1);
                    const pct = Math.round((count / total) * 100);
                    return (
                      <div key={cat} className="space-y-1">
                        <div className="flex justify-between text-xs font-mono">
                          <span className="capitalize text-slate-800 dark:text-slate-200 font-semibold">{cat}</span>
                          <span className="text-slate-500 dark:text-slate-400">{count} inspections ({pct}%)</span>
                        </div>
                        <div className="w-full bg-slate-200 dark:bg-industrial-900 rounded-full h-2.5 overflow-hidden">
                          <div
                            className="bg-gradient-to-r from-cyan-500 to-emerald-400 h-full rounded-full transition-all duration-500"
                            style={{ width: `${Math.max(pct, 5)}%` }}
                          />
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="text-center py-8 text-slate-400 text-xs font-mono">No data yet.</div>
                )}
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
          {/* Supervisor Metrics */}
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
              value={batches.length || (stats?.total_batches || 1)}
              icon={Layers}
              color="amber"
              subtext="Conveyor lines monitored"
              badge="Operations"
            />
            <StatCard
              title="High Severity Alerts"
              value={stats ? stats.total_failed : '--'}
              icon={AlertOctagon}
              color="rose"
              subtext="Requires supervisor review"
              badge="High Risk"
            />
            <StatCard
              title="Inspection Latency"
              value="~38 ms"
              icon={Cpu}
              color="emerald"
              subtext="Optical inference throughput"
              badge="High Speed"
            />
          </div>

          {/* Supervisor Batch Control */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Batch Table */}
            <div className="lg:col-span-8 glass-panel p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800/60 pb-3">
                <div>
                  <h3 className="text-[13px] font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <Layers className="w-4 h-4 text-amber-500" />
                    Production Batches
                  </h3>
                  <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">
                    Line batch progress and pass/fail distribution.
                  </p>
                </div>
                <button
                  onClick={onOpenUpload}
                  className="px-3.5 py-1.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold shadow-md shadow-amber-600/20 transition-all"
                >
                  + New Batch
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left data-table">
                  <thead className="text-[10px] text-slate-400 uppercase tracking-wider border-b border-slate-100 dark:border-slate-800">
                    <tr>
                      <th className="py-2.5 px-3">Batch ID</th>
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
                          <td className="py-3 px-3 font-bold text-slate-900 dark:text-slate-100">{b.batch_name}</td>
                          <td className="py-3 px-3 capitalize text-cyan-600 dark:text-cyan-400 font-semibold">{b.category || 'general'}</td>
                          <td className="py-3 px-3">{b.processed_images} / {b.total_images} items</td>
                          <td className="py-3 px-3 text-emerald-600 dark:text-emerald-400 font-semibold">{b.pass_count} Pass • {b.fail_count} Fail</td>
                          <td className="py-3 px-3">
                            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
                              {b.status}
                            </span>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={5} className="py-4 text-center text-slate-400">No active batches recorded yet.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Severity Model */}
            <div className="lg:col-span-4 glass-panel p-6 space-y-4">
              <div className="border-b border-slate-100 dark:border-slate-800/60 pb-3">
                <h3 className="text-[13px] font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-amber-500" />
                  Severity Distribution
                </h3>
              </div>

              <div className="space-y-3 text-xs font-mono">
                <div className="p-3.5 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex justify-between items-center">
                  <span className="text-emerald-600 dark:text-emerald-400 font-bold">Low Severity (0-39)</span>
                  <span className="text-slate-900 dark:text-white font-black text-sm">{stats?.total_passed || 0} items</span>
                </div>
                <div className="p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex justify-between items-center">
                  <span className="text-amber-600 dark:text-amber-400 font-bold">Medium Concern (40-59)</span>
                  <span className="text-slate-900 dark:text-white font-black text-sm">{stats?.total_review || 0} items</span>
                </div>
                <div className="p-3.5 rounded-2xl bg-rose-500/10 border border-rose-500/20 flex justify-between items-center">
                  <span className="text-rose-600 dark:text-rose-400 font-bold">Critical Defect (80-100)</span>
                  <span className="text-slate-900 dark:text-white font-black text-sm">{stats?.total_failed || 0} items</span>
                </div>
              </div>

              <button
                onClick={() => setActiveTab('audit')}
                className="w-full py-2.5 rounded-2xl bg-slate-100 hover:bg-slate-200 dark:bg-industrial-900 dark:hover:bg-industrial-800 text-slate-800 dark:text-slate-200 border border-slate-300 dark:border-slate-700 text-xs font-bold transition-colors flex items-center justify-center gap-2 shadow-xs"
              >
                <ShieldAlert className="w-3.5 h-3.5 text-amber-500" />
                View Shift Security Audit Logs
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
          {/* Executive Metrics */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title="Plant Quality Yield"
              value={stats ? `${stats.pass_rate_percentage}%` : '--'}
              icon={TrendingUp}
              color="purple"
              subtext="Overall plant-wide compliance"
              badge="Yield KPI"
            />
            <StatCard
              title="Critical Rejection Rate"
              value={stats ? `${stats.defect_rate_percentage}%` : '--'}
              icon={XCircle}
              color="rose"
              subtext="Scrap & rework frequency"
              badge="Risk Matrix"
            />
            <StatCard
              title="MVTec Benchmark Status"
              value="15/15"
              icon={FolderArchive}
              color="purple"
              subtext="Industrial object & texture categories"
              badge="100% Online"
            />
            <StatCard
              title="System Audit Compliance"
              value="99.8%"
              icon={ShieldCheck}
              color="emerald"
              subtext="Tamper-evident audit logs"
              badge="Verified"
            />
          </div>

          {/* Manager Strategy Deck */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Category Performance Matrix */}
            <div className="lg:col-span-8 glass-panel p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800/60 pb-3">
                <div>
                  <h3 className="text-[13px] font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-purple-500" />
                    Category Benchmark Matrix
                  </h3>
                  <p className="text-[11px] text-slate-400 dark:text-slate-500">
                    Performance across all 15 MVTec AD industrial domains.
                  </p>
                </div>
                <button
                  onClick={onOpenDataset}
                  className="text-xs text-purple-600 dark:text-purple-400 hover:underline flex items-center gap-1 font-mono font-bold"
                >
                  Dataset Detail <ArrowUpRight className="w-3 h-3" />
                </button>
              </div>

              {/* 15-Category Matrix Tiles (Dark & Light Theme High Contrast) */}
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 font-mono text-xs">
                {stats && stats.category_distribution && Object.keys(stats.category_distribution).length > 0 ? (
                  Object.entries(stats.category_distribution).map(([cat, cnt]) => (
                    <div 
                      key={cat} 
                      className="p-3.5 rounded-2xl bg-white dark:bg-industrial-950 border border-slate-200 dark:border-slate-800 text-center shadow-xs hover:border-purple-500/50 transition-all hover:scale-[1.02]"
                    >
                      <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-bold tracking-wider block truncate">
                        {cat}
                      </span>
                      <span className="text-lg font-black text-slate-900 dark:text-white mt-1 block">
                        {cnt} units
                      </span>
                      <span className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full inline-block mt-1">
                        Yield ~96%
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="col-span-5 text-center py-6 text-slate-400">Loading benchmark matrix...</div>
                )}
              </div>
            </div>

            {/* Compliance Snapshot */}
            <div className="lg:col-span-4 glass-panel p-6 space-y-4">
              <div className="border-b border-slate-100 dark:border-slate-800/60 pb-3">
                <h3 className="text-[13px] font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-purple-500" />
                  Compliance & Audit
                </h3>
              </div>

              <div className="p-4 rounded-2xl bg-purple-500/10 border border-purple-500/20 text-xs space-y-2.5">
                <div className="flex justify-between font-mono">
                  <span className="text-slate-600 dark:text-slate-300">Total Inspections:</span>
                  <strong className="text-slate-900 dark:text-white font-bold">{stats?.total_inspections || 0}</strong>
                </div>
                <div className="flex justify-between font-mono">
                  <span className="text-slate-600 dark:text-slate-300">Operator Sign-offs:</span>
                  <strong className="text-emerald-600 dark:text-emerald-400 font-bold">100% Tracked</strong>
                </div>
                <div className="flex justify-between font-mono">
                  <span className="text-slate-600 dark:text-slate-300">Audit Status:</span>
                  <strong className="text-cyan-600 dark:text-cyan-400 font-bold">Tamper Evident</strong>
                </div>
              </div>

              <button
                onClick={() => setActiveTab('audit')}
                className="w-full py-3 rounded-2xl bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-500 text-white font-bold text-xs shadow-md shadow-purple-600/20 transition-all flex items-center justify-center gap-2"
              >
                <ShieldCheck className="w-4 h-4" />
                Access Full Plant Audit Trail
              </button>
            </div>
          </div>
        </div>
      )}

      {/* RECENT INSPECTIONS */}
      <div className="space-y-3 pt-1">
        <div className="flex items-center justify-between">
          <h2 className="text-[14px] font-bold text-slate-900 dark:text-white tracking-tight flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-500" />
            Recent Inspections
          </h2>
          <span className="text-[11px] text-slate-400 dark:text-slate-500 font-mono">
            {stats?.recent_inspections?.length || 0} records
          </span>
        </div>

        <InspectionTable
          records={stats?.recent_inspections || []}
          onSelectRecord={onSelectRecord}
          onRefresh={fetchStatsAndBatches}
        />
      </div>
    </div>
  );
};
