import React, { useState, useEffect } from 'react';
import { 
  Scan, 
  Search, 
  Filter, 
  RefreshCw, 
  Download, 
  Zap, 
  Video,
  Layers
} from 'lucide-react';
import { inspectionAPI } from '../api/client';
import { InspectionTable } from '../components/InspectionTable';

const MVTEC_CATEGORIES = [
  "all", "bottle", "cable", "capsule", "carpet", "grid", 
  "hazelnut", "leather", "metal_nut", "pill", "screw", 
  "tile", "toothbrush", "transistor", "wood", "zipper"
];

export const InspectionsPage = ({ onSelectRecord, onOpenUpload, onOpenSimulator }) => {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedDecision, setSelectedDecision] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');

  const fetchRecords = async () => {
    setLoading(true);
    try {
      const params = {
        category: selectedCategory,
        decision: selectedDecision,
        status: selectedStatus,
        search: search || undefined,
        limit: 100
      };
      const res = await inspectionAPI.getInspections(params);
      setRecords(res.data);
    } catch (err) {
      console.error('Failed to fetch inspections', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecords();
  }, [selectedCategory, selectedDecision, selectedStatus]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchRecords();
  };

  return (
    <div className="space-y-6 animate-enter">
      {/* Page Header */}
      <div className="glass-panel p-5 sm:p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100 tracking-tight flex items-center gap-2">
            <Scan className="w-5 h-5 text-cyan-500 dark:text-cyan-400" />
            Inspection Records Database
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Browse, filter, and inspect raw product images, technical quality metrics, and severity evaluations.
          </p>
        </div>

        <div className="flex items-center space-x-2.5">
          <button
            onClick={fetchRecords}
            className="p-2 rounded-xl bg-slate-100 dark:bg-industrial-900 hover:bg-slate-200 dark:hover:bg-industrial-800 border border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-cyan-500' : ''}`} />
          </button>
          <button
            onClick={onOpenUpload}
            className="px-3.5 py-2 rounded-xl bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 text-white text-xs font-semibold shadow-lg shadow-cyan-500/20 transition-all flex items-center space-x-2"
          >
            <Zap className="w-3.5 h-3.5" />
            <span>Upload Image</span>
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="glass-panel rounded-2xl p-4 border border-slate-200 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3">
        {/* Search */}
        <form onSubmit={handleSearchSubmit} className="flex-1 min-w-[240px] relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by filename, category, or defect type..."
            className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-50 dark:bg-industrial-900 border border-slate-300 dark:border-slate-700 text-slate-800 dark:text-slate-200 text-xs focus:outline-none focus:border-cyan-500"
          />
        </form>

        {/* Dropdowns */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Category */}
          <div className="flex items-center space-x-1.5 text-xs font-mono">
            <span className="text-slate-500 dark:text-slate-400 text-[11px]">Category:</span>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg bg-slate-50 dark:bg-industrial-900 border border-slate-300 dark:border-slate-700 text-slate-800 dark:text-slate-200 text-xs capitalize font-medium"
            >
              {MVTEC_CATEGORIES.map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          {/* Decision */}
          <div className="flex items-center space-x-1.5 text-xs font-mono">
            <span className="text-slate-500 dark:text-slate-400 text-[11px]">Decision:</span>
            <select
              value={selectedDecision}
              onChange={(e) => setSelectedDecision(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg bg-slate-50 dark:bg-industrial-900 border border-slate-300 dark:border-slate-700 text-slate-800 dark:text-slate-200 text-xs font-medium"
            >
              <option value="all">All Decisions</option>
              <option value="PASS">PASS (Compliant)</option>
              <option value="FAIL">FAIL (Defective)</option>
              <option value="REVIEW">REVIEW</option>
              <option value="PENDING">PENDING</option>
            </select>
          </div>

          {/* Status */}
          <div className="flex items-center space-x-1.5 text-xs font-mono">
            <span className="text-slate-500 dark:text-slate-400 text-[11px]">Status:</span>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg bg-slate-50 dark:bg-industrial-900 border border-slate-300 dark:border-slate-700 text-slate-800 dark:text-slate-200 text-xs font-medium"
            >
              <option value="all">All Statuses</option>
              <option value="INSPECTED">INSPECTED</option>
              <option value="PENDING">PENDING</option>
              <option value="PROCESSING">PROCESSING</option>
              <option value="FAILED">FAILED</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <InspectionTable
        records={records}
        onSelectRecord={onSelectRecord}
        onRefresh={fetchRecords}
      />
    </div>
  );
};
