import React, { useState, useEffect, useRef } from 'react';
import { 
  Video, 
  Play, 
  Pause, 
  Camera, 
  Activity, 
  Sliders, 
  CheckCircle2, 
  AlertTriangle,
  RotateCcw,
  Zap
} from 'lucide-react';
import { inspectionAPI, datasetAPI } from '../api/client';

const CATEGORIES = [
  "bottle", "cable", "capsule", "carpet", "grid", "hazelnut", "leather", "metal_nut", "pill", "screw", "tile", "toothbrush", "transistor", "wood", "zipper"
];

export const CameraSimulator = ({ onNewInspection }) => {
  const [isRunning, setIsRunning] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('capsule');
  const [intervalSec, setIntervalSec] = useState(3);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [categorySamples, setCategorySamples] = useState([]);
  const [latestResult, setLatestResult] = useState(null);
  const [ingestedLog, setIngestedLog] = useState([]);
  const [loading, setLoading] = useState(false);

  const timerRef = useRef(null);

  useEffect(() => {
    fetchSamples(selectedCategory);
  }, [selectedCategory]);

  const fetchSamples = async (cat) => {
    try {
      const res = await datasetAPI.getCategoryDetail(cat);
      if (res.data && res.data.splits) {
        const samples = [];
        if (res.data.splits.test?.good) {
          res.data.splits.test.good.forEach(img => {
            samples.push({ category: cat, split: 'test', defect: 'good', url: img, name: img.split('/').pop() });
          });
        }
        Object.keys(res.data.splits.test || {}).forEach(defect => {
          if (defect !== 'good') {
            res.data.splits.test[defect].forEach(img => {
              samples.push({ category: cat, split: 'test', defect: defect, url: img, name: img.split('/').pop() });
            });
          }
        });
        setCategorySamples(samples);
        setCurrentImageIndex(0);
      }
    } catch (err) {
      console.warn('Failed to load category samples for simulator', err);
    }
  };

  useEffect(() => {
    if (isRunning) {
      timerRef.current = setInterval(() => {
        triggerCapture();
      }, intervalSec * 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isRunning, intervalSec, categorySamples, currentImageIndex]);

  const triggerCapture = async () => {
    if (categorySamples.length === 0) return;
    const sample = categorySamples[currentImageIndex % categorySamples.length];
    setCurrentImageIndex(prev => prev + 1);

    try {
      setLoading(true);
      const res = await inspectionAPI.importMvtec(
        sample.category,
        sample.split,
        sample.defect,
        sample.name
      );
      setLatestResult(res.data);
      setIngestedLog(prev => [res.data, ...prev.slice(0, 7)]);
      onNewInspection && onNewInspection(res.data);
    } catch (err) {
      console.error('Camera capture simulation error', err);
    } finally {
      setLoading(false);
    }
  };

  const currentSample = categorySamples[currentImageIndex % Math.max(categorySamples.length, 1)];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-enter">
      {/* Viewfinder Viewport (2 cols) */}
      <div className="lg:col-span-2 glass-panel rounded-2xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border border-cyan-500/20">
              <Camera className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">Live Conveyor Camera Viewfinder</h3>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">Camera ID: CAM-LINEA-04 • Optical 512x512</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono bg-slate-100 dark:bg-industrial-900 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300">
              FPS: {isRunning ? '59.8' : '0.0'}
            </span>
            <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-mono font-bold ${
              isRunning 
                ? 'bg-rose-500/20 text-rose-600 dark:text-rose-400 border border-rose-500/40 animate-pulse' 
                : 'bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-300 dark:border-slate-700'
            }`}>
              <div className={`w-1.5 h-1.5 rounded-full ${isRunning ? 'bg-rose-500' : 'bg-slate-400'}`} />
              {isRunning ? 'REC LIVE' : 'STANDBY'}
            </span>
          </div>
        </div>

        {/* Viewport Frame */}
        <div className="relative aspect-video rounded-xl bg-industrial-950 border-2 border-slate-800 overflow-hidden flex items-center justify-center group shadow-xl">
          {currentSample ? (
            <img
              src={currentSample.url}
              alt="Live Conveyor Stream"
              className="w-full h-full object-contain p-4 transition-transform duration-300 group-hover:scale-105"
            />
          ) : (
            <div className="text-slate-500 font-mono text-xs flex flex-col items-center gap-2">
              <Camera className="w-8 h-8 opacity-40 animate-pulse" />
              <span>Awaiting Camera Stream Sync...</span>
            </div>
          )}

          {/* Laser Scanline Overlay */}
          {isRunning && (
            <div className="absolute inset-x-0 h-1 bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_12px_rgba(6,182,212,0.9)] animate-scan pointer-events-none" />
          )}

          {/* Viewport HUD Crosshairs & Grid */}
          <div className="absolute inset-0 border border-cyan-500/10 pointer-events-none flex flex-col justify-between p-4 font-mono text-[10px] text-cyan-400">
            <div className="flex justify-between items-start">
              <div className="space-y-0.5 bg-black/50 px-2 py-1 rounded backdrop-blur-sm">
                <div>EXPOSURE: 1/250s</div>
                <div>ISO: 100</div>
                <div>FOCUS: AUTO (99.4%)</div>
              </div>
              <div className="bg-black/50 px-2 py-1 rounded backdrop-blur-sm">
                UTC: {new Date().toLocaleTimeString()}
              </div>
            </div>

            {/* Target Reticle in Center */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="w-24 h-24 border border-cyan-400/40 rounded-lg relative flex items-center justify-center">
                <div className="w-2 h-2 border border-cyan-400 rounded-full" />
                <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-2 text-[8px] bg-black/60 px-1 rounded">
                  ROI 1
                </div>
              </div>
            </div>

            {/* Bottom HUD */}
            <div className="flex justify-between items-end">
              <div className="bg-black/50 px-2 py-1 rounded backdrop-blur-sm">
                PRODUCT: <span className="uppercase text-white font-bold">{selectedCategory}</span>
              </div>
              <div className="bg-black/50 px-2 py-1 rounded backdrop-blur-sm">
                STATUS: {loading ? 'INGESTING...' : (isRunning ? 'SCANNING' : 'IDLE')}
              </div>
            </div>
          </div>
        </div>

        {/* Control Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsRunning(!isRunning)}
              className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center space-x-2 shadow-lg transition-all ${
                isRunning
                  ? 'bg-amber-600 hover:bg-amber-500 text-white shadow-amber-600/20'
                  : 'bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 text-white shadow-cyan-600/20'
              }`}
            >
              {isRunning ? (
                <>
                  <Pause className="w-3.5 h-3.5" />
                  <span>Pause Conveyor</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5" />
                  <span>Start Automated Conveyor</span>
                </>
              )}
            </button>

            <button
              onClick={triggerCapture}
              disabled={loading}
              className="px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-industrial-800 dark:hover:bg-industrial-700 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-700 text-xs font-semibold transition-colors flex items-center space-x-1.5"
            >
              <Zap className="w-3.5 h-3.5 text-cyan-500" />
              <span>Snap & Inspect</span>
            </button>
          </div>

          {/* Speed & Category controls */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-1.5">
              <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400">Interval:</span>
              <select
                value={intervalSec}
                onChange={(e) => setIntervalSec(Number(e.target.value))}
                className="px-2.5 py-1.5 rounded-lg bg-slate-50 dark:bg-industrial-900 border border-slate-300 dark:border-slate-700 text-slate-800 dark:text-slate-200 text-xs font-mono"
              >
                <option value={1.5}>1.5s (High Speed)</option>
                <option value={3}>3.0s (Normal)</option>
                <option value={5}>5.0s (Demo)</option>
              </select>
            </div>

            <div className="flex items-center space-x-1.5">
              <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400">Category:</span>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="px-2.5 py-1.5 rounded-lg bg-slate-50 dark:bg-industrial-900 border border-slate-300 dark:border-slate-700 text-slate-800 dark:text-slate-200 text-xs font-mono capitalize font-medium"
              >
                {CATEGORIES.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Real-time Ingestion Stream Log (1 col) */}
      <div className="glass-panel rounded-2xl p-5 space-y-4 flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <Activity className="w-4 h-4 text-cyan-500" />
              <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">Live Ingestion Stream</h3>
            </div>
            <span className="text-[10px] font-mono text-slate-500 dark:text-slate-400">
              {ingestedLog.length} captured
            </span>
          </div>

          <div className="space-y-2 mt-3 overflow-y-auto max-h-[420px] pr-1">
            {ingestedLog.length === 0 ? (
              <div className="text-center py-12 text-slate-400 text-xs font-mono space-y-2">
                <Sliders className="w-6 h-6 mx-auto opacity-30 animate-pulse" />
                <p>No captures in current session.<br />Click 'Start Conveyor' or 'Snap & Inspect'.</p>
              </div>
            ) : (
              ingestedLog.map((rec) => (
                <div
                  key={rec.id}
                  className="p-2.5 rounded-xl bg-slate-50 dark:bg-industrial-900/80 border border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs hover:border-cyan-500/40 transition-all"
                >
                  <div className="flex items-center space-x-2.5">
                    <div className="w-9 h-9 rounded-lg bg-white dark:bg-industrial-950 border border-slate-200 dark:border-slate-800 overflow-hidden flex-shrink-0">
                      <img src={rec.thumbnail_url || rec.image_url} alt="" className="w-full h-full object-cover" />
                    </div>
                    <div>
                      <div className="font-semibold text-slate-800 dark:text-slate-200 capitalize font-mono text-[11px]">
                        {rec.category} • {rec.defect_type}
                      </div>
                      <div className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">
                        {rec.image_width}x{rec.image_height} • {rec.file_format}
                      </div>
                    </div>
                  </div>

                  <div>
                    {rec.quality_decision === 'PASS' ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 font-mono">
                        PASS
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/30 font-mono">
                        FAIL ({rec.severity_score})
                      </span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {latestResult && (
          <div className="pt-3 border-t border-slate-100 dark:border-slate-800 text-[11px] font-mono text-slate-500 dark:text-slate-400 flex items-center justify-between">
            <span>Last ID: #{latestResult.id.slice(0, 8)}</span>
            <span className="text-cyan-600 dark:text-cyan-400 font-semibold">{Math.round((latestResult.confidence_score || 0.95) * 100)}% Conf</span>
          </div>
        )}
      </div>
    </div>
  );
};
