import React, { useState, useRef } from 'react';
import { 
  X, 
  UploadCloud, 
  FileCheck, 
  AlertCircle, 
  CheckCircle2, 
  Layers, 
  Sparkles,
  Image as ImageIcon
} from 'lucide-react';
import { inspectionAPI } from '../api/client';

const MVTEC_CATEGORIES = [
  "bottle", "cable", "capsule", "carpet", "grid", 
  "hazelnut", "leather", "metal_nut", "pill", "screw", 
  "tile", "toothbrush", "transistor", "wood", "zipper"
];

export const UploadModal = ({ isOpen, onClose, onUploadSuccess }) => {
  const [activeMode, setActiveMode] = useState('single'); // 'single' or 'batch'
  const [selectedCategory, setSelectedCategory] = useState('capsule');
  const [defectType, setDefectType] = useState('unclassified');
  const [notes, setNotes] = useState('');
  const [batchName, setBatchName] = useState(`BATCH-${new Date().toISOString().slice(0, 10)}-01`);

  // Files & Preview
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [imageMeta, setImageMeta] = useState(null);

  // States
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const fileInputRef = useRef(null);

  if (!isOpen) return null;

  const handleFileChange = (e) => {
    setError(null);
    if (activeMode === 'single') {
      const file = e.target.files[0];
      if (file) {
        processSingleFile(file);
      }
    } else {
      const files = Array.from(e.target.files);
      if (files.length > 0) {
        setSelectedFiles(files);
      }
    }
  };

  const processSingleFile = (file) => {
    if (file.size > 25 * 1024 * 1024) {
      setError('File exceeds maximum size of 25MB.');
      return;
    }

    setSelectedFile(file);
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);

    const img = new Image();
    img.onload = () => {
      setImageMeta({
        width: img.naturalWidth,
        height: img.naturalHeight,
        size: (file.size / 1024).toFixed(1) + ' KB',
        type: file.type || 'image/png'
      });
    };
    img.src = url;
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setError(null);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      if (activeMode === 'single') {
        processSingleFile(e.dataTransfer.files[0]);
      } else {
        setSelectedFiles(Array.from(e.dataTransfer.files));
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (activeMode === 'single') {
        if (!selectedFile) {
          throw new Error('Please select an image file to upload.');
        }
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('category', selectedCategory);
        formData.append('split', 'upload');
        formData.append('defect_type', defectType);
        if (notes) formData.append('notes', notes);

        await inspectionAPI.uploadSingle(formData);
      } else {
        if (selectedFiles.length === 0) {
          throw new Error('Please select at least one file for the batch.');
        }
        const formData = new FormData();
        selectedFiles.forEach((f) => formData.append('files', f));
        formData.append('batch_name', batchName);
        formData.append('category', selectedCategory);
        if (notes) formData.append('description', notes);

        await inspectionAPI.uploadBatch(formData);
      }

      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
        onUploadSuccess && onUploadSuccess();
        onClose();
      }, 1000);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 dark:bg-black/80 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-200">
      <div className="bg-white dark:bg-industrial-950 w-full max-w-xl rounded-3xl border border-slate-200 dark:border-slate-700/80 shadow-2xl overflow-hidden flex flex-col transition-colors">
        {/* Header */}
        <div className="p-5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-600 dark:text-cyan-400">
              <UploadCloud className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">Image Acquisition & Upload</h3>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">Industry 4.0 Ingestion Pipeline</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Mode Toggle */}
        <div className="flex border-b border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-industrial-950/40 p-1.5 gap-2">
          <button
            type="button"
            onClick={() => { setActiveMode('single'); setSelectedFile(null); setPreviewUrl(null); }}
            className={`flex-1 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeMode === 'single'
                ? 'bg-cyan-500 text-white dark:bg-cyan-500/20 dark:text-cyan-300 shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            Single Product Inspection
          </button>
          <button
            type="button"
            onClick={() => { setActiveMode('batch'); setSelectedFiles([]); }}
            className={`flex-1 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeMode === 'batch'
                ? 'bg-cyan-500 text-white dark:bg-cyan-500/20 dark:text-cyan-300 shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            Batch Production Line Upload
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4 overflow-y-auto max-h-[75vh]">
          {error && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-600 dark:text-rose-400 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
              <span>Image uploaded and queued for inspection!</span>
            </div>
          )}

          {/* Dropzone */}
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-slate-300 dark:border-slate-700 hover:border-cyan-500 rounded-2xl p-6 text-center cursor-pointer transition-all bg-slate-50 dark:bg-industrial-900/40 hover:bg-slate-100 dark:hover:bg-industrial-900/80 group"
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              multiple={activeMode === 'batch'}
              accept=".png,.jpg,.jpeg,.bmp,.tiff"
              className="hidden"
            />

            {activeMode === 'single' ? (
              previewUrl ? (
                <div className="space-y-3">
                  <div className="w-32 h-32 mx-auto rounded-xl overflow-hidden border border-slate-300 dark:border-slate-700 bg-slate-100 dark:bg-industrial-950 relative shadow-md">
                    <img src={previewUrl} alt="Preview" className="w-full h-full object-cover" />
                  </div>
                  {imageMeta && (
                    <div className="flex items-center justify-center gap-3 font-mono text-[11px] text-cyan-600 dark:text-cyan-400 font-semibold">
                      <span>{imageMeta.width}x{imageMeta.height} px</span>
                      <span>•</span>
                      <span>{imageMeta.size}</span>
                      <span>•</span>
                      <span>{selectedFile.name}</span>
                    </div>
                  )}
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">Click or drop another file to replace</p>
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="w-12 h-12 rounded-xl bg-white dark:bg-industrial-800 border border-slate-200 dark:border-slate-700 flex items-center justify-center mx-auto text-slate-400 group-hover:text-cyan-500 transition-colors shadow-xs">
                    <UploadCloud className="w-6 h-6" />
                  </div>
                  <div className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                    Click to browse or drag & drop product image
                  </div>
                  <p className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">
                    PNG, JPG, BMP, TIFF up to 25MB
                  </p>
                </div>
              )
            ) : (
              <div className="space-y-2">
                <div className="w-12 h-12 rounded-xl bg-white dark:bg-industrial-800 border border-slate-200 dark:border-slate-700 flex items-center justify-center mx-auto text-slate-400 group-hover:text-cyan-500 transition-colors shadow-xs">
                  <Layers className="w-6 h-6" />
                </div>
                <div className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                  {selectedFiles.length > 0 
                    ? `${selectedFiles.length} files selected for batch ingestion`
                    : 'Click or drop multiple images for batch inspection'
                  }
                </div>
                <p className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">
                  Multi-file conveyor ingestion supported
                </p>
              </div>
            )}
          </div>

          {/* Category & Defect Options */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-mono text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-1.5 font-medium">
                MVTec AD Category
              </label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-industrial-900 border border-slate-300 dark:border-slate-700 text-slate-800 dark:text-slate-200 text-xs focus:outline-none focus:border-cyan-500 capitalize font-medium"
              >
                {MVTEC_CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>

            {activeMode === 'single' ? (
              <div>
                <label className="block text-[11px] font-mono text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-1.5 font-medium">
                  Initial Defect Label
                </label>
                <select
                  value={defectType}
                  onChange={(e) => setDefectType(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-industrial-900 border border-slate-300 dark:border-slate-700 text-slate-800 dark:text-slate-200 text-xs focus:outline-none focus:border-cyan-500 font-medium"
                >
                  <option value="unclassified">Unclassified (Auto-Inspect)</option>
                  <option value="good">Good (No Defect)</option>
                  <option value="scratch">Scratch</option>
                  <option value="crack">Crack / Fracture</option>
                  <option value="bent">Bent / Deformation</option>
                  <option value="broken_small">Broken Small</option>
                  <option value="color">Color Stain</option>
                  <option value="cut">Cut / Puncture</option>
                </select>
              </div>
            ) : (
              <div>
                <label className="block text-[11px] font-mono text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-1.5 font-medium">
                  Batch Identifier
                </label>
                <input
                  type="text"
                  value={batchName}
                  onChange={(e) => setBatchName(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-industrial-900 border border-slate-300 dark:border-slate-700 text-slate-800 dark:text-slate-200 text-xs focus:outline-none focus:border-cyan-500 font-mono"
                  placeholder="e.g. BATCH-2026-A1"
                />
              </div>
            )}
          </div>

          {/* Notes */}
          <div>
            <label className="block text-[11px] font-mono text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-1.5 font-medium">
              Operator Inspection Notes (Optional)
            </label>
            <input
              type="text"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Station Line A conveyor sample test"
              className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-industrial-900 border border-slate-300 dark:border-slate-700 text-slate-800 dark:text-slate-200 text-xs focus:outline-none focus:border-cyan-500 font-medium"
            />
          </div>

          {/* Footer Actions */}
          <div className="pt-2 flex items-center justify-end space-x-3 border-t border-slate-100 dark:border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-industrial-900 dark:hover:bg-industrial-800 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 text-xs font-semibold transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || (activeMode === 'single' ? !selectedFile : selectedFiles.length === 0)}
              className="px-5 py-2 rounded-xl bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 disabled:opacity-50 text-white text-xs font-bold shadow-lg shadow-cyan-600/20 transition-all flex items-center space-x-2"
            >
              {loading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <FileCheck className="w-3.5 h-3.5" />
                  <span>{activeMode === 'single' ? 'Submit for Inspection' : `Ingest ${selectedFiles.length} Images`}</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
