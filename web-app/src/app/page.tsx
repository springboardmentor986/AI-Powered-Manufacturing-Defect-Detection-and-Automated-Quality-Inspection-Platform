"use client";

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import api from '@/lib/api';
import axios from 'axios';
import {
  XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  Area, AreaChart
} from 'recharts';
import {
  Activity, AlertTriangle, CheckCircle2, Package,
  Camera, UploadCloud, RefreshCw, Sliders, ShieldAlert,
  History, ArrowRight, Eye, ShieldCheck, Cpu, Sparkles, AlertCircle
} from 'lucide-react';

interface ValidationIssue {
  msg?: string;
}

interface TrendPoint {
  date: string;
  passed: number;
  failed: number;
}

interface DashboardStats {
  total_inspections?: number;
  passed?: number;
  failed?: number;
  pending?: number;
  defect_count?: number;
  defect_rate?: number;
  defect_distribution?: Record<string, number>;
}

interface InspectionItem {
  id: number;
  created_at?: string;
  status: string;
  defect_type?: string;
  severity_level?: string;
  confidence?: number;
  product_category?: string;
}

interface InspectionResult {
  status: string;
  defect_type?: string;
  classification_confidence?: number;
  severity_level?: string;
  severity_score?: number;
  recommendation?: string;
  defect_region?: {
    x?: number;
    y?: number;
    width?: number;
    height?: number;
  };
}

interface ProductCategory {
  name: string;
  display_name?: string;
}

interface SettingsSummary {
  blur_threshold?: number;
  anomaly_threshold?: number;
  classification_confidence_threshold?: number;
  critical_severity_cutoff?: number;
  high_severity_cutoff?: number;
  medium_severity_cutoff?: number;
}

const DEFAULT_CATEGORIES = [
  'bottle', 'cable', 'capsule', 'carpet', 'grid', 'hazelnut',
  'leather', 'metal_nut', 'pill', 'screw', 'tile', 'toothbrush',
  'transistor', 'wood', 'zipper'
];

export default function DashboardPage() {
  const router = useRouter();

  // Auth & Role state
  const [role, setRole] = useState<string>('inspector');
  const [username, setUsername] = useState<string>('');
  const [loading, setLoading] = useState(true);

  // Inspector Section - Live Inspection state
  const [categories, setCategories] = useState<string[]>(DEFAULT_CATEGORIES);
  const [selectedCategory, setSelectedCategory] = useState<string>('bottle');
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [inspecting, setInspecting] = useState(false);
  const [inspectResult, setInspectResult] = useState<InspectionResult | null>(null);
  const [inspectError, setInspectError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Supervisor Section - Analytics & Trends state
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [recentHistory, setRecentHistory] = useState<InspectionItem[]>([]);
  const [analyticsError, setAnalyticsError] = useState<string | null>(null);

  // Admin Section - Settings & System state
  const [systemSettings, setSystemSettings] = useState<SettingsSummary | null>(null);

  useEffect(() => {
    const getStoredRole = () =>
      (localStorage.getItem('userRole') || localStorage.getItem('role') || 'inspector').toLowerCase();
    const token = localStorage.getItem('token') || localStorage.getItem('access_token');
    
    if (!token) {
      router.push('/login');
      return;
    }

    const currentRole = getStoredRole();
    const currentUsername = localStorage.getItem('username') || 'User';
    setRole(currentRole);
    setUsername(currentUsername);

    const initData = async () => {
      setLoading(true);
      try {
        // Fetch categories for inspection
        const catRes = await api.get('/inspections/categories').catch(() => null);
        if (catRes?.data?.categories && Array.isArray(catRes.data.categories)) {
          setCategories(catRes.data.categories.map((c: ProductCategory) => c.name));
        }

        // If Supervisor or Admin, load Analytics and History
        if (currentRole === 'supervisor' || currentRole === 'admin') {
          const [analyticsRes, trendsRes, historyRes] = await Promise.allSettled([
            api.get('/inspections/analytics'),
            api.get('/inspections/trends'),
            api.get('/inspections/history?limit=5')
          ]);

          if (analyticsRes.status === 'fulfilled') {
            setStats(analyticsRes.value.data);
          }
          if (trendsRes.status === 'fulfilled') {
            const raw = trendsRes.value.data as { trends?: unknown } | unknown[] | undefined;
            const t: TrendPoint[] = Array.isArray(raw)
              ? (raw as TrendPoint[])
              : Array.isArray((raw as { trends?: unknown } | undefined)?.trends)
                ? ((raw as { trends: TrendPoint[] }).trends)
                : [];
            setTrends(t);
          }
          if (historyRes.status === 'fulfilled') {
            setRecentHistory(Array.isArray(historyRes.value.data) ? historyRes.value.data : []);
          }
        }

        // If Admin, load Settings & System metrics
        if (currentRole === 'admin') {
          const settingsRes = await api.get('/inspections/config/settings').catch(() => null);
          if (settingsRes?.data?.settings) {
            setSystemSettings(settingsRes.data.settings);
          }
        }
      } catch (err) {
        console.error('Failed to load dashboard data', err);
        setAnalyticsError('Could not load all dashboard components.');
      } finally {
        setLoading(false);
      }
    };

    initData();

    const syncRole = () => {
      setRole(getStoredRole());
    };
    window.addEventListener('storage', syncRole);
    return () => window.removeEventListener('storage', syncRole);
  }, [router]);

  // Live Inspection Handlers
  const handleFileSelect = (selected: File | null) => {
    if (!selected) return;
    if (selected.size > 10 * 1024 * 1024) {
      setInspectError('Image exceeds 10MB size limit.');
      return;
    }
    setFile(selected);
    setInspectResult(null);
    setInspectError(null);
    const reader = new FileReader();
    reader.onload = () => setPreview(reader.result as string);
    reader.readAsDataURL(selected);
  };

  const handleRunInspection = async () => {
    if (!file) {
      setInspectError('Please select or upload an inspection image.');
      return;
    }
    setInspecting(true);
    setInspectError(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('category', selectedCategory);
      const res = await api.post(`/inspections/upload?category=${encodeURIComponent(selectedCategory)}`, formData);
      setInspectResult(res.data as InspectionResult);
      
      // Refresh analytics if Supervisor/Admin
      if (role === 'supervisor' || role === 'admin') {
        const [aRes, hRes] = await Promise.allSettled([
          api.get('/inspections/analytics'),
          api.get('/inspections/history?limit=5')
        ]);
        if (aRes.status === 'fulfilled') setStats(aRes.value.data);
        if (hRes.status === 'fulfilled' && Array.isArray(hRes.value.data)) setRecentHistory(hRes.value.data);
      }
    } catch (err: unknown) {
      const detail = axios.isAxiosError(err)
        ? (err.response?.data as { detail?: unknown } | undefined)?.detail
        : undefined;
      const msg = Array.isArray(detail)
        ? detail.map((d) => (typeof d === 'object' && d !== null && 'msg' in d ? String((d as ValidationIssue).msg) : '')).filter(Boolean).join(', ')
        : typeof detail === 'string'
          ? detail
          : 'Inspection failed. Please try again.';
      setInspectError(msg);
    } finally {
      setInspecting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-[70vh] items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-slate-400 text-sm">Loading RBAC Dashboard workspace...</p>
        </div>
      </div>
    );
  }

  const isInspector = role === 'inspector';
  const isSupervisor = role === 'supervisor';
  const isAdmin = role === 'admin';

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Top Welcome / Role Banner */}
      <div className="glass-card p-6 md:p-8 rounded-3xl border border-slate-700/60 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none"></div>
        <div className="relative z-10 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
                Welcome back, {username}
              </h1>
              <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
                isAdmin
                  ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40'
                  : isSupervisor
                    ? 'bg-blue-500/20 text-blue-300 border border-blue-500/40'
                    : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
              }`}>
                {role} Mode
              </span>
            </div>
            <p className="text-slate-400 text-sm">
              {isInspector && 'Active Role: Inspector — Focused Live Defect Inspection & Image Verification.'}
              {isSupervisor && 'Active Role: Supervisor — Real-Time Live Inspection, Trend Analytics & Quality Audit History.'}
              {isAdmin && 'Active Role: Administrator — Full Quality Control Suite, Analytics, Thresholds & System Management.'}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/inspect"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold rounded-xl transition flex items-center gap-2 shadow-[0_0_15px_rgba(37,99,235,0.4)]"
            >
              <Camera size={16} /> Full Inspection Suite
            </Link>
            {(isSupervisor || isAdmin) && (
              <Link
                href="/history"
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-semibold rounded-xl transition border border-slate-700 flex items-center gap-2"
              >
                <History size={16} /> History Log
              </Link>
            )}
            {isAdmin && (
              <Link
                href="/settings"
                className="px-4 py-2 bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/30 text-sm font-semibold rounded-xl transition flex items-center gap-2"
              >
                <Sliders size={16} /> Settings
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 1. CORE LIVE INSPECTION / IMAGE UPLOAD (Inspector, Supervisor, Admin)      */}
      {/* ========================================================================= */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-white flex items-center gap-2.5">
            <Camera className="text-blue-400" size={22} />
            Live Defect Inspection &amp; Image Upload
          </h2>
          <span className="text-xs text-slate-400 font-mono bg-slate-800/80 px-3 py-1 rounded-lg border border-slate-700">
            Target Category: <span className="text-blue-400 font-bold capitalize">{selectedCategory.replaceAll('_', ' ')}</span>
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Upload & Category Controls */}
          <div className="lg:col-span-6 glass-card p-6 rounded-2xl border border-slate-800 space-y-5">
            <div>
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-2">
                Select Manufactured Product Category
              </label>
              <select
                aria-label="Select Manufactured Product Category"
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full bg-slate-900/80 border border-slate-700 text-white rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-blue-500 capitalize"
              >
                {categories.map((c) => (
                  <option key={c} value={c}>
                    {c.replaceAll('_', ' ')}
                  </option>
                ))}
              </select>
            </div>

            {/* Drag & Drop / Upload Zone */}
            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-slate-700 hover:border-blue-500/70 bg-slate-900/40 hover:bg-slate-900/70 rounded-2xl p-6 text-center cursor-pointer transition flex flex-col items-center justify-center min-h-[200px]"
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(e) => handleFileSelect(e.target.files?.[0] || null)}
              />
              <UploadCloud className="text-blue-400 mb-2 animate-pulse" size={36} />
              <p className="text-sm font-semibold text-slate-200">
                {file ? file.name : 'Click or Drag & Drop manufacturing part image'}
              </p>
              <p className="text-xs text-slate-400 mt-1">PNG, JPG, WEBP up to 10MB</p>
            </div>

            {inspectError && (
              <div className="p-3 bg-red-500/10 border border-red-500/30 text-red-400 text-xs rounded-xl flex items-center gap-2">
                <AlertCircle size={16} />
                <span>{inspectError}</span>
              </div>
            )}

            <div className="flex gap-3">
              <button
                type="button"
                onClick={handleRunInspection}
                disabled={!file || inspecting}
                className="flex-1 py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-xl transition shadow-[0_0_20px_rgba(37,99,235,0.3)] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-sm"
              >
                {inspecting ? (
                  <>
                    <RefreshCw size={16} className="animate-spin" /> Analyzing Defect Anomaly...
                  </>
                ) : (
                  <>
                    <Sparkles size={16} /> Run Automated Inspection
                  </>
                )}
              </button>
              {file && (
                <button
                  type="button"
                  onClick={() => { setFile(null); setPreview(null); setInspectResult(null); }}
                  className="px-4 py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl transition text-sm"
                >
                  Clear
                </button>
              )}
            </div>
          </div>

          {/* Live Preview & Result Display */}
          <div className="lg:col-span-6 glass-card p-6 rounded-2xl border border-slate-800 flex flex-col justify-between">
            <div>
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
                  Live Visual Inspection &amp; Decision
                </h3>
                {inspectResult && (
                  <span className={`px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1.5 ${
                    inspectResult.status === 'PASS'
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                      : 'bg-red-500/20 text-red-400 border border-red-500/40'
                  }`}>
                    {inspectResult.status === 'PASS' ? <CheckCircle2 size={14} /> : <AlertTriangle size={14} />}
                    {inspectResult.status}
                  </span>
                )}
              </div>

              {preview ? (
                <div className="relative rounded-xl overflow-hidden bg-black/40 border border-slate-800 aspect-video flex items-center justify-center">
                  <img
                    src={preview}
                    alt="Inspection target preview"
                    className="max-h-full max-w-full object-contain"
                  />
                  {inspectResult?.defect_region && (
                    <div
                      className="absolute border-2 border-red-500 bg-red-500/20 shadow-[0_0_15px_rgba(239,68,68,0.5)] rounded pointer-events-none"
                      style={{
                        left: `${inspectResult.defect_region.x || 0}%`,
                        top: `${inspectResult.defect_region.y || 0}%`,
                        width: `${inspectResult.defect_region.width || 0}%`,
                        height: `${inspectResult.defect_region.height || 0}%`,
                      }}
                    />
                  )}
                </div>
              ) : (
                <div className="rounded-xl border border-slate-800/80 bg-slate-900/30 aspect-video flex flex-col items-center justify-center text-slate-500">
                  <Eye size={36} className="mb-2 opacity-50" />
                  <p className="text-sm">No image uploaded for preview yet</p>
                </div>
              )}
            </div>

            {inspectResult ? (
              <div className="mt-4 pt-4 border-t border-slate-800 space-y-2.5">
                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="p-2.5 rounded-xl bg-slate-900/70 border border-slate-800">
                    <span className="text-slate-400 block mb-0.5">Classification</span>
                    <span className="font-bold text-white capitalize">{inspectResult.defect_type || 'Good'}</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-slate-900/70 border border-slate-800">
                    <span className="text-slate-400 block mb-0.5">Confidence</span>
                    <span className="font-mono font-bold text-blue-400">
                      {typeof inspectResult.classification_confidence === 'number'
                        ? `${(inspectResult.classification_confidence * 100).toFixed(1)}%`
                        : '-'}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-slate-900/70 border border-slate-800">
                    <span className="text-slate-400 block mb-0.5">Severity</span>
                    <span className={`font-bold ${
                      inspectResult.severity_level === 'Critical' ? 'text-red-400' :
                      inspectResult.severity_level === 'High' ? 'text-amber-400' :
                      inspectResult.severity_level === 'Medium' ? 'text-blue-400' : 'text-slate-300'
                    }`}>
                      {inspectResult.severity_level || 'Low'}
                    </span>
                  </div>
                </div>

                {inspectResult.recommendation && (
                  <p className="text-xs text-slate-300 bg-slate-900/50 p-2.5 rounded-xl border border-slate-800">
                    <span className="font-semibold text-amber-400">Recommendation:</span> {inspectResult.recommendation}
                  </p>
                )}
              </div>
            ) : (
              <div className="mt-4 text-xs text-slate-500 text-center py-2">
                Select an image and click &quot;Run Automated Inspection&quot; to view AI classification.
              </div>
            )}
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 2. SUPERVISOR & ADMIN SECTION: ANALYTICS, TRENDS & HISTORY               */}
      {/* ========================================================================= */}
      {(isSupervisor || isAdmin) && (
        <section className="space-y-6 pt-4 border-t border-slate-800/80">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-white flex items-center gap-2.5">
              <Activity className="text-emerald-400" size={22} />
              Analytics &amp; Inspection Trends (Supervisor &amp; Admin)
            </h2>
            <Link
              href="/history"
              className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 font-semibold"
            >
              View Full History Log <ArrowRight size={14} />
            </Link>
          </div>

          {analyticsError && (
            <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400 text-sm">
              {analyticsError}
            </div>
          )}

          {/* KPI Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="glass-card p-5 rounded-2xl border border-slate-800 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center text-blue-400">
                <Package size={24} />
              </div>
              <div>
                <p className="text-xs text-slate-400 font-medium">Total Inspections</p>
                <h3 className="text-2xl font-bold text-white mt-0.5">{stats?.total_inspections ?? 0}</h3>
              </div>
            </div>

            <div className="glass-card p-5 rounded-2xl border border-slate-800 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center text-emerald-400">
                <CheckCircle2 size={24} />
              </div>
              <div>
                <p className="text-xs text-slate-400 font-medium">Passed Parts</p>
                <h3 className="text-2xl font-bold text-white mt-0.5">{stats?.passed ?? 0}</h3>
              </div>
            </div>

            <div className="glass-card p-5 rounded-2xl border border-slate-800 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-red-500/20 flex items-center justify-center text-red-400">
                <AlertTriangle size={24} />
              </div>
              <div>
                <p className="text-xs text-slate-400 font-medium">Failed Parts</p>
                <h3 className="text-2xl font-bold text-white mt-0.5">{stats?.failed ?? 0}</h3>
              </div>
            </div>

            <div className="glass-card p-5 rounded-2xl border border-slate-800 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-amber-500/20 flex items-center justify-center text-amber-400">
                <Activity size={24} />
              </div>
              <div>
                <p className="text-xs text-slate-400 font-medium">Defect Rate</p>
                <h3 className="text-2xl font-bold text-white mt-0.5">
                  {typeof stats?.defect_rate === 'number' ? stats.defect_rate.toFixed(2) : '0.00'}%
                </h3>
              </div>
            </div>
          </div>

          {/* Charts & Distribution */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="glass-card p-6 rounded-2xl border border-slate-800 lg:col-span-2">
              <h3 className="text-base font-bold text-white mb-4">Inspection Volume &amp; Yield Trends</h3>
              <div className="h-64">
                {trends.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={trends}>
                      <defs>
                        <linearGradient id="colorPass" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                        </linearGradient>
                        <linearGradient id="colorFail" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
                      <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                      <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                      <RechartsTooltip 
                        contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.95)', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff' }}
                      />
                      <Area type="monotone" dataKey="passed" stroke="#10b981" strokeWidth={2.5} fillOpacity={1} fill="url(#colorPass)" name="Passed" />
                      <Area type="monotone" dataKey="failed" stroke="#ef4444" strokeWidth={2.5} fillOpacity={1} fill="url(#colorFail)" name="Failed" />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex items-center justify-center h-full text-slate-500 text-sm">
                    No trend history available yet.
                  </div>
                )}
              </div>
            </div>

            <div className="glass-card p-6 rounded-2xl border border-slate-800">
              <h3 className="text-base font-bold text-white mb-4">Defect Type Distribution</h3>
              <div className="space-y-3.5 max-h-64 overflow-y-auto pr-1">
                {stats?.defect_distribution && Object.entries(stats.defect_distribution).map(([type, count]) => {
                  const numCount = Number(count) || 0;
                  const defectTotal = Number(stats.defect_count) || numCount || 1;
                  const percentage = Math.min(100, Math.max(0, Math.round((numCount / defectTotal) * 100)));
                  return (
                    <div key={type}>
                      <div className="flex justify-between text-xs mb-1 text-slate-300">
                        <span className="capitalize">{type.replaceAll('_', ' ')}</span>
                        <span className="font-bold">{numCount} ({percentage}%)</span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full"
                          style={{ width: `${percentage}%` }}
                        ></div>
                      </div>
                    </div>
                  );
                })}
                {(!stats?.defect_distribution || Object.keys(stats.defect_distribution).length === 0) && (
                  <div className="text-center text-slate-500 py-10 text-xs">No defect records logged yet.</div>
                )}
              </div>
            </div>
          </div>

          {/* Recent History Table Preview */}
          <div className="glass-card p-6 rounded-2xl border border-slate-800">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-base font-bold text-white">Recent Audit History Preview</h3>
              <Link href="/history" className="text-xs text-blue-400 hover:underline flex items-center gap-1">
                Open audit log <ArrowRight size={12} />
              </Link>
            </div>

            {recentHistory.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400">
                      <th className="py-2.5 px-3">ID</th>
                      <th className="py-2.5 px-3">Product</th>
                      <th className="py-2.5 px-3">Status</th>
                      <th className="py-2.5 px-3">Defect Type</th>
                      <th className="py-2.5 px-3">Severity</th>
                      <th className="py-2.5 px-3 text-right">Confidence</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {recentHistory.map((item) => (
                      <tr key={item.id} className="hover:bg-slate-800/30">
                        <td className="py-2.5 px-3 font-mono text-slate-300">#{item.id}</td>
                        <td className="py-2.5 px-3 text-white capitalize">{item.product_category || 'bottle'}</td>
                        <td className="py-2.5 px-3">
                          <span className={`px-2 py-0.5 rounded-full font-bold text-[10px] ${
                            item.status === 'PASS' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                          }`}>
                            {item.status}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-300 capitalize">
                          {item.defect_type === 'good' ? '-' : (item.defect_type ?? '').replaceAll('_', ' ')}
                        </td>
                        <td className="py-2.5 px-3 text-slate-300">{item.severity_level || '-'}</td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-300">
                          {typeof item.confidence === 'number' ? `${(item.confidence * 100).toFixed(1)}%` : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-xs text-slate-500 text-center py-4">No recent inspections logged.</p>
            )}
          </div>
        </section>
      )}

      {/* ========================================================================= */}
      {/* 3. ADMIN SECTION: SYSTEM SETTINGS & USER / MODEL MANAGEMENT               */}
      {/* ========================================================================= */}
      {isAdmin && (
        <section className="space-y-6 pt-4 border-t border-purple-500/30">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2.5">
                <Sliders className="text-purple-400" size={22} />
                System Settings &amp; AI Calibration (Administrator Only)
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Manage global anomaly thresholds, pre-inference blur gates, and multi-model pipeline configuration.
              </p>
            </div>
            <Link
              href="/settings"
              className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white font-semibold rounded-xl text-xs transition shadow-[0_0_15px_rgba(168,85,247,0.4)] flex items-center gap-1.5"
            >
              Configure Thresholds <ArrowRight size={14} />
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Quality Gate</span>
                <ShieldCheck size={16} className="text-blue-400" />
              </div>
              <p className="text-sm font-bold text-white">Pre-Inference Blur Check</p>
              <div className="flex justify-between items-center text-xs text-slate-300 pt-2 border-t border-slate-800">
                <span>Blur Threshold:</span>
                <span className="font-mono text-blue-400 font-bold">{systemSettings?.blur_threshold ?? 20}</span>
              </div>
            </div>

            <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">AI Sensitivity</span>
                <ShieldAlert size={16} className="text-amber-400" />
              </div>
              <p className="text-sm font-bold text-white">Anomaly Sensitivity</p>
              <div className="flex justify-between items-center text-xs text-slate-300 pt-2 border-t border-slate-800">
                <span>Anomaly Threshold:</span>
                <span className="font-mono text-amber-400 font-bold">{systemSettings?.anomaly_threshold ?? 90}</span>
              </div>
            </div>

            <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Pipeline Status</span>
                <Cpu size={16} className="text-emerald-400" />
              </div>
              <p className="text-sm font-bold text-white">Category AI Models</p>
              <div className="flex justify-between items-center text-xs text-slate-300 pt-2 border-t border-slate-800">
                <span>Active Categories:</span>
                <span className="font-mono text-emerald-400 font-bold">15 / 15 Online</span>
              </div>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
