import React from 'react';
import { Product } from '../types';
import { getProductImageUrl } from '../services/api';
import { X, Bookmark, Ruler, CheckCircle2, XCircle, ShieldCheck, Tag } from 'lucide-react';

interface ProductModalProps {
  product: Product | null;
  explanation?: string;
  isSaved?: boolean;
  onClose: () => void;
  onToggleSave?: (product: Product) => void;
}

export const ProductModal: React.FC<ProductModalProps> = ({
  product,
  explanation,
  isSaved = false,
  onClose,
  onToggleSave,
}) => {
  if (!product) return null;

  const imageUrl = getProductImageUrl(product);

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div
        className="relative bg-white rounded-3xl max-w-2xl w-full overflow-hidden shadow-2xl border border-slate-200 animate-in fade-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-10 p-2 rounded-full bg-white/90 text-slate-500 hover:text-slate-900 shadow-md transition-all"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="grid grid-cols-1 md:grid-cols-2">
          {/* Image Side */}
          <div className="relative aspect-square md:aspect-auto bg-slate-100">
            <img
              src={imageUrl}
              alt={product.title}
              className="w-full h-full object-cover"
            />
            <div className="absolute bottom-4 left-4 flex gap-2">
              <span className="bg-slate-900/80 backdrop-blur-xs text-white text-xs font-semibold px-3 py-1 rounded-full uppercase">
                {product.category}
              </span>
              {product.style && (
                <span className="bg-white/90 backdrop-blur-xs text-slate-800 text-xs font-medium px-3 py-1 rounded-full capitalize">
                  {product.style}
                </span>
              )}
            </div>
          </div>

          {/* Details Side */}
          <div className="p-6 md:p-8 flex flex-col justify-between max-h-[85vh] overflow-y-auto custom-scrollbar">
            <div>
              <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-2">
                <span>ID: {product.product_id}</span>
                <span className="flex items-center gap-1 font-sans">
                  {product.availability ? (
                    <span className="text-emerald-600 font-semibold flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" /> In Stock
                    </span>
                  ) : (
                    <span className="text-rose-500 font-semibold flex items-center gap-1">
                      <XCircle className="w-3.5 h-3.5" /> Out of Stock
                    </span>
                  )}
                </span>
              </div>

              <h2 className="text-xl font-bold text-slate-900 leading-snug">
                {product.title}
              </h2>

              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-2xl font-black text-slate-900">
                  ₹{product.price.toLocaleString('en-IN')}
                </span>
                <span className="text-xs text-slate-500">{product.currency}</span>
              </div>

              <p className="mt-4 text-sm text-slate-600 leading-relaxed">
                {product.description}
              </p>

              {/* Verified Dimensions Specifications Table */}
              <div className="mt-6 border border-slate-200 rounded-xl p-4 bg-slate-50/50">
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                  <Ruler className="w-4 h-4 text-brand-600" />
                  Verified Catalogue Specifications
                </h4>

                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="bg-white p-2.5 rounded-lg border border-slate-200">
                    <span className="text-[10px] text-slate-400 uppercase font-semibold block">Width</span>
                    <span className="text-sm font-bold text-slate-800">
                      {product.width !== null && product.width !== undefined ? `${product.width} cm` : 'Not recorded'}
                    </span>
                  </div>
                  <div className="bg-white p-2.5 rounded-lg border border-slate-200">
                    <span className="text-[10px] text-slate-400 uppercase font-semibold block">Height</span>
                    <span className="text-sm font-bold text-slate-800">
                      {product.height !== null && product.height !== undefined ? `${product.height} cm` : 'Not recorded'}
                    </span>
                  </div>
                  <div className="bg-white p-2.5 rounded-lg border border-slate-200">
                    <span className="text-[10px] text-slate-400 uppercase font-semibold block">Depth</span>
                    <span className="text-sm font-bold text-slate-800">
                      {product.depth !== null && product.depth !== undefined ? `${product.depth} cm` : 'Not recorded'}
                    </span>
                  </div>
                </div>

                <div className="mt-3 pt-3 border-t border-slate-200 grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <span className="text-slate-400 block font-medium">Material:</span>
                    <span className="font-semibold text-slate-800 capitalize">
                      {product.material || 'Unspecified in catalogue'}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block font-medium">Colour:</span>
                    <span className="font-semibold text-slate-800 capitalize">
                      {product.colour || 'Unspecified in catalogue'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Match Explanation */}
              {explanation && (
                <div className="mt-4 p-3.5 bg-brand-50 border border-brand-200 rounded-xl text-xs">
                  <div className="flex items-center gap-1.5 font-bold text-brand-900 mb-1">
                    <ShieldCheck className="w-4 h-4 text-brand-600" />
                    Why this matches your criteria:
                  </div>
                  <p className="text-slate-700 leading-normal">{explanation}</p>
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="mt-6 pt-4 border-t border-slate-100 flex gap-3">
              <button
                type="button"
                onClick={() => onToggleSave && onToggleSave(product)}
                className={`flex-1 py-3 px-4 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition-all ${
                  isSaved
                    ? 'bg-amber-100 text-amber-900 border border-amber-300'
                    : 'bg-slate-900 hover:bg-slate-800 text-white shadow-md'
                }`}
              >
                <Bookmark className={`w-4 h-4 ${isSaved ? 'fill-amber-600 text-amber-600' : ''}`} />
                {isSaved ? 'Saved to Favorites' : 'Save to Favorites'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
