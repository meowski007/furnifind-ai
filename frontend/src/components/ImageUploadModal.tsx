import React, { useState, useRef } from 'react';
import { ImageSearchResultItem } from '../types';
import { searchByImage, getProductImageUrl } from '../services/api';
import { Upload, X, Sparkles, AlertCircle, Loader2 } from 'lucide-react';

interface ImageUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectProduct: (product: any) => void;
}

export const ImageUploadModal: React.FC<ImageUploadModalProps> = ({
  isOpen,
  onClose,
  onSelectProduct,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<ImageSearchResultItem[]>([]);
  const [encoderUsed, setEncoderUsed] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileChange = (file: File) => {
    setError(null);
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      setError('Please upload a valid JPEG, PNG, or WEBP image.');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setError('Image exceeds 5MB size limit.');
      return;
    }
    setSelectedFile(file);
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    setResults([]);
  };

  const handleSearch = async () => {
    if (!selectedFile) return;
    setLoading(true);
    setError(null);
    try {
      const resp = await searchByImage(selectedFile);
      setResults(resp.results);
      setEncoderUsed(resp.encoder_used);
    } catch (err: any) {
      setError(err.message || 'Failed to search by image.');
    } finally {
      setLoading(false);
    }
  };

  const resetAll = () => {
    setSelectedFile(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setResults([]);
    setError(null);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div
        className="relative bg-white rounded-3xl max-w-3xl w-full max-h-[90vh] overflow-y-auto p-6 md:p-8 shadow-2xl border border-slate-200 custom-scrollbar animate-in fade-in zoom-in-95"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-brand-50 text-brand-600 border border-brand-100">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900">Multimodal Image Search</h3>
              <p className="text-xs text-slate-500">Find catalogue furniture visually matching your uploaded photo</p>
            </div>
          </div>
          <button
            onClick={() => {
              resetAll();
              onClose();
            }}
            className="p-2 rounded-full text-slate-400 hover:text-slate-900 hover:bg-slate-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Upload Dropzone */}
        {!previewUrl ? (
          <div
            onClick={() => fileInputRef.current?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              if (e.dataTransfer.files?.[0]) handleFileChange(e.dataTransfer.files[0]);
            }}
            className="border-2 border-dashed border-slate-300 hover:border-brand-500 rounded-2xl p-10 text-center cursor-pointer bg-slate-50 hover:bg-brand-50/20 transition-all group"
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={(e) => e.target.files?.[0] && handleFileChange(e.target.files[0])}
              accept="image/jpeg,image/png,image/webp"
              className="hidden"
            />
            <div className="mx-auto w-12 h-12 rounded-full bg-white shadow-xs flex items-center justify-center text-slate-400 group-hover:text-brand-600 mb-3 transition-colors">
              <Upload className="w-6 h-6" />
            </div>
            <p className="text-sm font-semibold text-slate-800">
              Click to browse or drag & drop furniture image
            </p>
            <p className="text-xs text-slate-400 mt-1">
              Supports JPEG, PNG, WEBP (Max: 5MB)
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row items-center gap-6 p-4 rounded-2xl bg-slate-50 border border-slate-200">
              <img
                src={previewUrl}
                alt="Upload preview"
                className="w-32 h-32 object-cover rounded-xl border border-slate-200 shadow-xs"
              />
              <div className="flex-1 space-y-2 text-center sm:text-left">
                <span className="text-xs font-semibold text-slate-700 block">
                  Reference Image: {selectedFile?.name}
                </span>
                <span className="text-xs text-slate-400 block font-mono">
                  {(selectedFile?.size || 0) / 1024 < 1024
                    ? `${((selectedFile?.size || 0) / 1024).toFixed(1)} KB`
                    : `${((selectedFile?.size || 0) / (1024 * 1024)).toFixed(2)} MB`}
                </span>
                <div className="flex gap-2 justify-center sm:justify-start">
                  <button
                    onClick={handleSearch}
                    disabled={loading}
                    className="py-2 px-5 bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold rounded-xl shadow-xs flex items-center gap-2 transition-all disabled:opacity-50"
                  >
                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                    <span>Run Visual Similarity Search</span>
                  </button>
                  <button
                    onClick={resetAll}
                    disabled={loading}
                    className="py-2 px-4 bg-white border border-slate-200 text-slate-600 hover:text-slate-900 text-xs font-semibold rounded-xl"
                  >
                    Change Image
                  </button>
                </div>
              </div>
            </div>

            {error && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Results Grid */}
            {results.length > 0 && (
              <div className="space-y-4 pt-4 border-t border-slate-100">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-bold text-slate-900">
                    Top Visually Similar Products ({results.length})
                  </h4>
                  <span className="text-[11px] font-mono text-slate-400">
                    Encoder: {encoderUsed}
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                  {results.map((res) => {
                    const prodImg = getProductImageUrl(res.product);
                    return (
                      <div
                        key={res.product.product_id}
                        onClick={() => {
                          onSelectProduct(res.product);
                          onClose();
                        }}
                        className="group border border-slate-200 rounded-xl p-3 bg-white hover:border-brand-500/50 hover:shadow-md transition-all cursor-pointer flex flex-col justify-between"
                      >
                        <div className="relative aspect-4/3 bg-slate-100 rounded-lg overflow-hidden mb-2">
                          <img
                            src={prodImg}
                            alt={res.product.title}
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                          />
                          <span className="absolute bottom-2 right-2 bg-slate-900/80 text-white text-[10px] font-bold px-1.5 py-0.5 rounded backdrop-blur-xs">
                            {(res.similarity_score * 100).toFixed(0)}% match
                          </span>
                        </div>
                        <div>
                          <h5 className="text-xs font-bold text-slate-900 line-clamp-1 group-hover:text-brand-600">
                            {res.product.title}
                          </h5>
                          <span className="text-xs font-black text-slate-900 block mt-1">
                            ₹{res.product.price.toLocaleString('en-IN')}
                          </span>
                          <p className="text-[10px] text-slate-500 mt-1 line-clamp-2">
                            {res.visual_match_explanation}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
