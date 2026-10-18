import React, { useState, useEffect } from 'react';
import { 
  FolderArchive, 
  Layers, 
  ExternalLink, 
  Sparkles, 
  CheckCircle2, 
  AlertOctagon, 
  Eye, 
  ArrowRight,
  Database,
  RefreshCw,
  Zap,
  Cpu
} from 'lucide-react';
import { datasetAPI, inspectionAPI } from '../api/client';

export const DatasetBrowser = ({ onImportSuccess }) => {
  const [categories, setCategories] = useState([]);
  const [selectedType, setSelectedType] = useState('all');
  const [activeCategory, setActiveCategory] = useState(null);
  const [categoryDetails, setCategoryDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [importing, setImporting] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);
  const [modelsRegistry, setModelsRegistry] = useState({});
  const [trainingAll, setTrainingAll] = useState(false);

  useEffect(() => {
    fetchCategories();
    fetchModels();
  }, []);

  const fetchCategories = async () => {
    setLoading(true);
    try {
      const res = await datasetAPI.getCategories();
      setCategories(res.data);
      if (res.data.length > 0 && !activeCategory) {
        loadCategory(res.data[0].category);
      }
    } catch (err) {
      console.error('Failed to load MVTec AD categories', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchModels = async () => {
    try {
      const res = await datasetAPI.getTrainedModels();
      setModelsRegistry(res.data?.models || {});
    } catch (err) {
      console.error('Failed to load model registry', err);
    }
  };

  const handleTrainAll = async () => {
    setTrainingAll(true);
    try {
      const res = await datasetAPI.trainAllModels();
      setSuccessMsg(`Trained ${res.data?.categories_trained || 15} anomaly models on actual mv-dataset in ${res.data?.total_duration_seconds}s!`);
      setTimeout(() => setSuccessMsg(null), 5000);
      fetchModels();
    } catch (err) {
      console.error('Training failed', err);
    } finally {
      setTrainingAll(false);
    }
  };

  const loadCategory = async (catName) => {
    setActiveCategory(catName);
    setDetailsLoading(true);
    try {
      const res = await datasetAPI.getCategoryDetail(catName);
      setCategoryDetails(res.data);
    } catch (err) {
      console.error('Failed to load category details', err);
    } finally {
      setDetailsLoading(false);
    }
  };

  const handleImport = async (cat, split, defect, imageName) => {
    const key = `${cat}_${split}_${defect}_${imageName}`;
    setImporting(key);
    try {
      const res = await inspectionAPI.importMvtec(cat, split, defect, imageName);
      setSuccessMsg(`Imported ${cat} (${defect}) to live inspections!`);
      setTimeout(() => setSuccessMsg(null), 3000);
      onImportSuccess && onImportSuccess(res.data);
    } catch (err) {
      console.error('Import failed', err);
    } finally {
      setImporting(null);
    }
  };

  const filteredCategories = categories.filter((c) => {
    if (selectedType === 'all') return true;
    return c.type === selectedType;
  });

  const trainedCount = Object.keys(modelsRegistry).length;

  return (
    <div className="space-y-6 animate-enter">
      {/* Header Banner */}
      <div className="glass-panel p-5 sm:p-6 relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2.5">
              <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-600 dark:text-cyan-400">
                <Database className="w-5 h-5" />
              </div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                MVTec Anomaly Detection Benchmark (mv-dataset)
              </h2>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-2xl leading-relaxed">
              Real industrial benchmark dataset covering 15 manufacturing domains across textures & objects. Total 6,612 images connected.
            </p>
          </div>

          <div className="flex items-center flex-wrap gap-2">
            {/* Filter buttons */}
            <div className="flex items-center space-x-1.5 p-1 rounded-xl bg-slate-100 dark:bg-industrial-900 border border-slate-200 dark:border-slate-800">
              <button
                onClick={() => setSelectedType('all')}
                className={`px-3 py-1 rounded-lg text-xs font-mono font-semibold transition-all ${
                  selectedType === 'all'
                    ? 'bg-cyan-500 text-white shadow-sm'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
                }`}
              >
                All (15)
              </button>
              <button
                onClick={() => setSelectedType('object')}
                className={`px-3 py-1 rounded-lg text-xs font-mono font-semibold transition-all ${
                  selectedType === 'object'
                    ? 'bg-cyan-500 text-white shadow-sm'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
                }`}
              >
                Objects (10)
              </button>
              <button
                onClick={() => setSelectedType('texture')}
                className={`px-3 py-1 rounded-lg text-xs font-mono font-semibold transition-all ${
                  selectedType === 'texture'
                    ? 'bg-cyan-500 text-white shadow-sm'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
                }`}
              >
                Textures (5)
              </button>
            </div>

            {/* Train AI Models button */}
            <button
              onClick={handleTrainAll}
              disabled={trainingAll}
              className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-mono font-bold flex items-center gap-1.5 shadow-sm transition-all disabled:opacity-50"
            >
              {trainingAll ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Training 15 Models...</span>
                </>
              ) : (
                <>
                  <Cpu className="w-3.5 h-3.5" />
                  <span>AI Models: {trainedCount}/15 Trained</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {successMsg && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 text-xs font-mono flex items-center justify-between animate-in fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" />
            <span>{successMsg}</span>
          </div>
        </div>
      )}

      {/* Main 2-Col Layout: Categories list & Sample Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Category List Sidebar (4 cols) */}
        <div className="lg:col-span-4 space-y-2.5 max-h-[750px] overflow-y-auto pr-1">
          {loading ? (
            <div className="text-center py-12 text-slate-400 font-mono text-xs">
              <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-cyan-500" />
              Loading MVTec AD Structure...
            </div>
          ) : (
            filteredCategories.map((cat) => {
              const isSelected = activeCategory === cat.category;
              const modelMeta = modelsRegistry[cat.category];
              return (
                <div
                  key={cat.category}
                  onClick={() => loadCategory(cat.category)}
                  className={`p-3.5 rounded-2xl cursor-pointer transition-all border ${
                    isSelected
                      ? 'bg-cyan-50 dark:bg-industrial-900 border-cyan-500/50 shadow-md shadow-cyan-500/10'
                      : 'glass-panel hover:bg-slate-100/70 dark:hover:bg-industrial-900/60 border-slate-200 dark:border-slate-800/80'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-sm text-slate-900 dark:text-slate-200 capitalize font-mono">
                        {cat.category}
                      </span>
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded uppercase font-semibold ${
                        cat.type === 'object' ? 'bg-purple-500/15 text-purple-600 dark:text-purple-400 border border-purple-500/20' : 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/20'
                      }`}>
                        {cat.type}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5">
                      {modelMeta && (
                        <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                          <CheckCircle2 className="w-2.5 h-2.5" /> Trained
                        </span>
                      )}
                      <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
                        {cat.total_images} imgs
                      </span>
                    </div>
                  </div>

                  {/* Defect types pill tags */}
                  <div className="flex flex-wrap gap-1 mt-2">
                    {cat.defect_types && cat.defect_types.slice(0, 4).map((d) => (
                      <span key={d} className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
                        {d}
                      </span>
                    ))}
                    {cat.defect_types && cat.defect_types.length > 4 && (
                      <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500">
                        +{cat.defect_types.length - 4}
                      </span>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Selected Category Detail & Sample Viewer (8 cols) */}
        <div className="lg:col-span-8 glass-panel p-5 space-y-5">
          {detailsLoading ? (
            <div className="text-center py-20 text-slate-400 font-mono text-xs">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-cyan-500" />
              Loading {activeCategory} dataset samples...
            </div>
          ) : categoryDetails && categoryDetails.found ? (
            <div className="space-y-6">
              {/* Category Header */}
              <div className="flex items-center justify-between pb-4 border-b border-slate-200 dark:border-slate-800">
                <div>
                  <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 capitalize font-mono flex items-center gap-2">
                    <span>{categoryDetails.category}</span>
                    <span className="text-xs px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-500 font-mono">
                      Domain: {categories.find(c => c.category === categoryDetails.category)?.type || 'industrial'}
                    </span>
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 font-mono mt-0.5">
                    Click "Inspect" on any sample to run through the AI pipeline.
                  </p>
                </div>

                {modelsRegistry[categoryDetails.category] && (
                  <div className="text-right font-mono text-[11px] text-slate-500 dark:text-slate-400">
                    <span className="text-emerald-500 font-bold">● Model Active</span>
                    <div>Latency: {modelsRegistry[categoryDetails.category].mean_inference_latency_ms || 25}ms</div>
                  </div>
                )}
              </div>

              {/* 1. Train Good Reference Samples */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5" /> 1. Train Split (Flawless Reference Samples)
                  </span>
                  <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
                    {categoryDetails.splits.train?.good?.length || 0} preview images
                  </span>
                </div>

                <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-2.5">
                  {(categoryDetails.splits.train?.good || []).map((url, idx) => {
                    const imgName = url.split('/').pop();
                    const key = `${categoryDetails.category}_train_good_${imgName}`;
                    return (
                      <div key={idx} className="group relative rounded-xl bg-slate-100 dark:bg-industrial-900 border border-slate-200 dark:border-slate-800 overflow-hidden aspect-square">
                        <img src={url} alt="" className="w-full h-full object-cover" />
                        <div className="absolute inset-0 bg-black/70 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center p-1 gap-1">
                          <span className="text-[9px] font-mono text-white truncate w-full text-center">{imgName}</span>
                          <button
                            onClick={() => handleImport(categoryDetails.category, 'train', 'good', imgName)}
                            disabled={importing === key}
                            className="px-2 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-white text-[9px] font-mono flex items-center gap-1"
                          >
                            <Zap className="w-2.5 h-2.5" /> Inspect
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* 2. Test Defects & Ground Truth Masks */}
              <div className="space-y-4 pt-4 border-t border-slate-100 dark:border-slate-800">
                <span className="text-xs font-mono font-bold text-rose-600 dark:text-rose-400 uppercase tracking-wider flex items-center gap-1.5">
                  <AlertOctagon className="w-3.5 h-3.5" /> 2. Test Set (Defect Types & Ground Truth Pairs)
                </span>

                {Object.keys(categoryDetails.splits.test || {}).map((defect) => {
                  const testImages = categoryDetails.splits.test[defect] || [];
                  const gtImages = categoryDetails.splits.ground_truth[defect] || [];

                  return (
                    <div key={defect} className="p-3.5 rounded-xl bg-slate-50 dark:bg-industrial-900/60 border border-slate-200 dark:border-slate-800 space-y-2.5">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-mono font-bold text-slate-800 dark:text-slate-200 capitalize">
                          Defect Mode: <span className={defect === 'good' ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'}>{defect}</span>
                        </span>
                        <span className="text-[10px] font-mono text-slate-500 dark:text-slate-400">
                          {testImages.length} test images
                        </span>
                      </div>

                      <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-2">
                        {testImages.map((testUrl, idx) => {
                          const imgName = testUrl.split('/').pop();
                          const gtUrl = gtImages[idx];
                          const key = `${categoryDetails.category}_test_${defect}_${imgName}`;

                          return (
                            <div key={idx} className="space-y-1">
                              <div className="group relative rounded-xl bg-slate-100 dark:bg-industrial-950 border border-slate-200 dark:border-slate-800 overflow-hidden aspect-square">
                                <img src={testUrl} alt="" className="w-full h-full object-cover" />
                                <div className="absolute inset-0 bg-black/70 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center p-1 gap-1">
                                  <span className="text-[9px] font-mono text-white truncate w-full text-center">{imgName}</span>
                                  <button
                                    onClick={() => handleImport(categoryDetails.category, 'test', defect, imgName)}
                                    disabled={importing === key}
                                    className="px-2 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-white text-[9px] font-mono flex items-center gap-1"
                                  >
                                    <Zap className="w-2.5 h-2.5" /> Inspect
                                  </button>
                                </div>
                              </div>
                              {gtUrl && (
                                <div className="text-[9px] font-mono text-slate-400 text-center truncate">
                                  Mask available
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="text-center py-20 text-slate-400 font-mono text-xs">
              Select a category to view dataset images and splits.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
