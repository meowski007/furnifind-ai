import React from 'react';
import { Product } from '../types';
import { getProductImageUrl } from '../services/api';
import { Bookmark, Sparkles, Ruler, CheckCircle2, XCircle } from 'lucide-react';

interface ProductCardProps {
  product: Product;
  score?: number;
  explanation?: string;
  isSaved?: boolean;
  onToggleSave?: (product: Product) => void;
  onClick?: (product: Product) => void;
}

export const ProductCard: React.FC<ProductCardProps> = ({
  product,
  score,
  explanation,
  isSaved = false,
  onToggleSave,
  onClick,
}) => {
  const imageUrl = getProductImageUrl(product);

  return (
    <div
      onClick={() => onClick && onClick(product)}
      className="group relative bg-white rounded-2xl border border-slate-200/80 overflow-hidden shadow-xs hover:shadow-xl hover:border-brand-500/30 transition-all duration-300 flex flex-col cursor-pointer"
    >
      {/* Image container */}
      <div className="relative aspect-4/3 bg-slate-100 overflow-hidden">
        <img
          src={imageUrl}
          alt={product.title}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          loading="lazy"
        />

        {/* Category Pill */}
        <div className="absolute top-3 left-3 flex flex-wrap gap-1.5">
          <span className="bg-white/90 backdrop-blur-xs text-slate-800 text-xs font-semibold px-2.5 py-1 rounded-full shadow-xs capitalize">
            {product.category}
          </span>
          {product.style && (
            <span className="bg-slate-900/80 backdrop-blur-xs text-white text-[11px] font-medium px-2 py-0.5 rounded-full capitalize">
              {product.style}
            </span>
          )}
        </div>

        {/* Save/Favorite Button */}
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            if (onToggleSave) onToggleSave(product);
          }}
          className={`absolute top-3 right-3 p-2 rounded-full backdrop-blur-xs transition-all shadow-sm ${
            isSaved
              ? 'bg-amber-500 text-white'
              : 'bg-white/85 text-slate-600 hover:bg-white hover:text-slate-900'
          }`}
          title={isSaved ? 'Remove from saved' : 'Save product'}
        >
          <Bookmark className={`w-4 h-4 ${isSaved ? 'fill-white' : ''}`} />
        </button>

        {/* Match / Similarity Score Pill */}
        {score !== undefined && score > 0 && (
          <div className="absolute bottom-3 right-3 bg-brand-600/90 backdrop-blur-xs text-white text-[11px] font-bold px-2 py-1 rounded-lg flex items-center gap-1 shadow-xs">
            <Sparkles className="w-3 h-3 text-brand-200" />
            <span>{(score * 100).toFixed(0)}% match</span>
          </div>
        )}
      </div>

      {/* Card Content */}
      <div className="p-4 flex-1 flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between gap-2 mb-1">
            <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">
              {product.product_id}
            </span>
            <div className="flex items-center gap-1 text-[11px]">
              {product.availability ? (
                <span className="flex items-center gap-1 text-emerald-600 font-medium">
                  <CheckCircle2 className="w-3 h-3" /> In Stock
                </span>
              ) : (
                <span className="flex items-center gap-1 text-rose-500 font-medium">
                  <XCircle className="w-3 h-3" /> Out of Stock
                </span>
              )}
            </div>
          </div>

          <h3 className="font-semibold text-slate-900 text-sm line-clamp-1 group-hover:text-brand-600 transition-colors">
            {product.title}
          </h3>

          <p className="text-xs text-slate-500 mt-1 line-clamp-2">
            {product.description}
          </p>

          {/* Specifications Pills */}
          <div className="flex flex-wrap items-center gap-2 mt-3 pt-2 border-t border-slate-100">
            {product.material && (
              <span className="text-[11px] text-slate-600 bg-slate-100 px-2 py-0.5 rounded capitalize">
                {product.material}
              </span>
            )}
            {product.colour && (
              <span className="text-[11px] text-slate-600 bg-slate-100 px-2 py-0.5 rounded capitalize">
                {product.colour}
              </span>
            )}
            {product.width !== null && product.width !== undefined && (
              <span className="text-[11px] text-slate-600 bg-slate-100 px-2 py-0.5 rounded flex items-center gap-1">
                <Ruler className="w-3 h-3 text-slate-400" />
                {product.width} cm W
              </span>
            )}
          </div>
        </div>

        {/* Price & Explanation */}
        <div className="mt-4 pt-3 border-t border-slate-100">
          <div className="flex items-baseline justify-between">
            <span className="text-base font-bold text-slate-900">
              ₹{product.price.toLocaleString('en-IN')}
            </span>
            <span className="text-xs text-brand-600 font-medium group-hover:underline">
              Inspect Specs →
            </span>
          </div>

          {/* Grounded Match Explanation */}
          {explanation && (
            <div className="mt-2 text-[11px] text-slate-600 bg-brand-50/70 border border-brand-100 p-2 rounded-lg line-clamp-2">
              <span className="font-semibold text-brand-800">Why matched: </span>
              {explanation}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
