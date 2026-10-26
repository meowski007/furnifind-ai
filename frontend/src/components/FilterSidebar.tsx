import React from 'react';
import { ActiveFilters } from '../types';
import { Filter, RotateCcw } from 'lucide-react';

interface FilterSidebarProps {
  filters: ActiveFilters;
  onChange: (filters: ActiveFilters) => void;
  onReset: () => void;
}

const CATEGORIES = [
  'desks',
  'chairs',
  'sofas',
  'tables',
  'beds',
  'bookcases',
  'storage',
  'lighting',
];

const STYLES = [
  'scandinavian',
  'modern',
  'industrial',
  'mid-century',
  'minimalist',
  'boho',
  'rustic',
];

const MATERIALS = [
  'oak',
  'walnut',
  'pine',
  'metal',
  'leather',
  'velvet',
  'fabric',
  'glass',
  'marble',
  'rattan',
];

export const FilterSidebar: React.FC<FilterSidebarProps> = ({
  filters,
  onChange,
  onReset,
}) => {
  const handleCategoryClick = (cat: string) => {
    if (filters.category === cat) {
      const next = { ...filters };
      delete next.category;
      onChange(next);
    } else {
      onChange({ ...filters, category: cat });
    }
  };

  const handleStyleClick = (style: string) => {
    if (filters.style === style) {
      const next = { ...filters };
      delete next.style;
      onChange(next);
    } else {
      onChange({ ...filters, style: style });
    }
  };

  const handleMaterialClick = (mat: string) => {
    if (filters.material === mat) {
      const next = { ...filters };
      delete next.material;
      onChange(next);
    } else {
      onChange({ ...filters, material: mat });
    }
  };

  return (
    <aside className="w-full lg:w-64 bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2 font-bold text-sm text-slate-900">
          <Filter className="w-4 h-4 text-brand-600" />
          <span>Filters</span>
        </div>
        <button
          onClick={onReset}
          className="text-xs text-slate-500 hover:text-brand-600 flex items-center gap-1 transition-colors"
        >
          <RotateCcw className="w-3 h-3" />
          <span>Reset</span>
        </button>
      </div>

      {/* Category Filter */}
      <div>
        <label className="text-xs font-bold text-slate-900 uppercase tracking-wider block mb-2.5">
          Category
        </label>
        <div className="flex flex-wrap gap-1.5">
          {CATEGORIES.map((cat) => {
            const isSelected = filters.category === cat;
            return (
              <button
                key={cat}
                onClick={() => handleCategoryClick(cat)}
                className={`text-xs px-2.5 py-1 rounded-lg capitalize transition-all ${
                  isSelected
                    ? 'bg-slate-900 text-white font-semibold shadow-xs'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {cat}
              </button>
            );
          })}
        </div>
      </div>

      {/* Price Range */}
      <div>
        <label className="text-xs font-bold text-slate-900 uppercase tracking-wider block mb-2">
          Max Price (₹)
        </label>
        <div className="space-y-2">
          <input
            type="range"
            min="3000"
            max="80000"
            step="1000"
            value={filters.max_price || 80000}
            onChange={(e) =>
              onChange({ ...filters, max_price: Number(e.target.value) })
            }
            className="w-full accent-brand-600 cursor-pointer"
          />
          <div className="flex justify-between text-xs text-slate-500 font-mono">
            <span>₹3,000</span>
            <span className="font-bold text-slate-900">
              {filters.max_price ? `≤ ₹${filters.max_price.toLocaleString('en-IN')}` : 'Any'}
            </span>
            <span>₹80,000</span>
          </div>
        </div>
      </div>

      {/* Dimension Max Width */}
      <div>
        <label className="text-xs font-bold text-slate-900 uppercase tracking-wider block mb-2">
          Max Width (cm)
        </label>
        <div className="flex items-center gap-2">
          <input
            type="number"
            min="30"
            max="300"
            placeholder="e.g. 120"
            value={filters.max_width || ''}
            onChange={(e) =>
              onChange({
                ...filters,
                max_width: e.target.value ? Number(e.target.value) : undefined,
              })
            }
            className="w-full text-xs px-3 py-2 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
          />
          <span className="text-xs text-slate-400 font-medium">cm</span>
        </div>
      </div>

      {/* Style Filter */}
      <div>
        <label className="text-xs font-bold text-slate-900 uppercase tracking-wider block mb-2.5">
          Style
        </label>
        <div className="flex flex-wrap gap-1.5">
          {STYLES.map((style) => {
            const isSelected = filters.style === style;
            return (
              <button
                key={style}
                onClick={() => handleStyleClick(style)}
                className={`text-xs px-2.5 py-1 rounded-lg capitalize transition-all ${
                  isSelected
                    ? 'bg-brand-600 text-white font-semibold shadow-xs'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {style}
              </button>
            );
          })}
        </div>
      </div>

      {/* Material Filter */}
      <div>
        <label className="text-xs font-bold text-slate-900 uppercase tracking-wider block mb-2.5">
          Material
        </label>
        <div className="flex flex-wrap gap-1.5">
          {MATERIALS.map((mat) => {
            const isSelected = filters.material === mat;
            return (
              <button
                key={mat}
                onClick={() => handleMaterialClick(mat)}
                className={`text-xs px-2.5 py-1 rounded-lg capitalize transition-all ${
                  isSelected
                    ? 'bg-amber-800 text-white font-semibold shadow-xs'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {mat}
              </button>
            );
          })}
        </div>
      </div>

      {/* In Stock Only Switch */}
      <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
        <span className="text-xs font-medium text-slate-700">In Stock Only</span>
        <input
          type="checkbox"
          checked={filters.availability || false}
          onChange={(e) =>
            onChange({
              ...filters,
              availability: e.target.checked ? true : undefined,
            })
          }
          className="w-4 h-4 rounded text-brand-600 accent-brand-600 cursor-pointer"
        />
      </div>
    </aside>
  );
};
