import React, { useState, useEffect } from 'react';
import { Product, RecommendationResponse, StatedPreferences } from '../types';
import { fetchRecommendations } from '../services/api';
import { ProductCard } from '../components/ProductCard';
import { Sparkles, Sliders, RefreshCw, Bookmark, Eye, AlertCircle, Loader2 } from 'lucide-react';

interface RecommendationsPageProps {
  savedProductIds: string[];
  viewedProductIds: string[];
  onToggleSave: (product: Product) => void;
  onSelectProduct: (product: Product) => void;
  onClearHistory: () => void;
}

const AVAILABLE_STYLES = [
  'scandinavian',
  'modern',
  'industrial',
  'mid-century',
  'minimalist',
  'boho',
  'rustic',
];

const AVAILABLE_MATERIALS = [
  'oak',
  'walnut',
  'pine',
  'leather',
  'velvet',
  'fabric',
  'glass',
  'marble',
  'rattan',
];

export const RecommendationsPage: React.FC<RecommendationsPageProps> = ({
  savedProductIds,
  viewedProductIds,
  onToggleSave,
  onSelectProduct,
  onClearHistory,
}) => {
  const [preferences, setPreferences] = useState<StatedPreferences>({
    category: null,
    budget_max: null,
    preferred_styles: [],
    preferred_materials: [],
    preferred_colours: [],
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recData, setRecData] = useState<RecommendationResponse | null>(null);

  useEffect(() => {
    loadRecommendations();
  }, [savedProductIds, viewedProductIds]);

  const loadRecommendations = async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetchRecommendations({
        user_id: 'portfolio_user',
        preferences: preferences,
        viewed_product_ids: viewedProductIds,
        saved_product_ids: savedProductIds,
        top_k: 8,
        include_diversity: true,
      });
      setRecData(resp);
    } catch (err: any) {
      setError(err.message || 'Failed to generate recommendations.');
    } finally {
      setLoading(false);
    }
  };

  const toggleStyle = (style: string) => {
    const current = preferences.preferred_styles;
    const next = current.includes(style)
      ? current.filter((s) => s !== style)
      : [...current, style];
    setPreferences({ ...preferences, preferred_styles: next });
  };

  const toggleMaterial = (mat: string) => {
    const current = preferences.preferred_materials;
    const next = current.includes(mat)
      ? current.filter((m) => m !== mat)
      : [...current, mat];
    setPreferences({ ...preferences, preferred_materials: next });
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Page Header */}
      <div>
        <div className="flex items-center gap-2 text-brand-600 font-bold text-xs uppercase tracking-wider mb-1">
          <Sparkles className="w-4 h-4" />
          <span>Explainable Recommendation Engine</span>
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          Personalized Furniture Suggestions
        </h1>
        <p className="mt-1 text-sm text-slate-600 max-w-2xl">
          Content-based recommendation algorithm scoring category affinity, style alignment, material preferences, and budget suitability.
        </p>
      </div>

      {/* Preferences & Signals Dashboard */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Preference Control Card */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Sliders className="w-4 h-4 text-brand-600" />
              <span>Explicit Customer Preferences</span>
            </h3>
            <button
              onClick={loadRecommendations}
              className="text-xs font-semibold text-brand-600 hover:text-brand-700 flex items-center gap-1.5 transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>Update Recommendations</span>
            </button>
          </div>

          {/* Budget Range */}
          <div>
            <label className="text-xs font-bold text-slate-700 uppercase tracking-wider block mb-2">
              Target Budget (Max ₹)
            </label>
            <div className="flex items-center gap-3">
              <input
                type="range"
                min="5000"
                max="80000"
                step="2500"
                value={preferences.budget_max || 80000}
                onChange={(e) =>
                  setPreferences({ ...preferences, budget_max: Number(e.target.value) })
                }
                className="w-full accent-brand-600 cursor-pointer"
              />
              <span className="text-xs font-mono font-bold text-slate-900 w-28 text-right">
                {preferences.budget_max ? `≤ ₹${preferences.budget_max.toLocaleString('en-IN')}` : 'Any Budget'}
              </span>
            </div>
          </div>

          {/* Style Preferences */}
          <div>
            <label className="text-xs font-bold text-slate-700 uppercase tracking-wider block mb-2">
              Preferred Aesthetics & Styles
            </label>
            <div className="flex flex-wrap gap-1.5">
              {AVAILABLE_STYLES.map((st) => {
                const active = preferences.preferred_styles.includes(st);
                return (
                  <button
                    key={st}
                    onClick={() => toggleStyle(st)}
                    className={`text-xs px-3 py-1 rounded-lg capitalize transition-all ${
                      active
                        ? 'bg-slate-900 text-white font-semibold shadow-xs'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {st}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Material Preferences */}
          <div>
            <label className="text-xs font-bold text-slate-700 uppercase tracking-wider block mb-2">
              Preferred Materials & Finishes
            </label>
            <div className="flex flex-wrap gap-1.5">
              {AVAILABLE_MATERIALS.map((mat) => {
                const active = preferences.preferred_materials.includes(mat);
                return (
                  <button
                    key={mat}
                    onClick={() => toggleMaterial(mat)}
                    className={`text-xs px-3 py-1 rounded-lg capitalize transition-all ${
                      active
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
        </div>

        {/* Interaction Signals Card */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 pb-3 border-b border-slate-100 mb-4">
              Interaction Signals
            </h3>

            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 rounded-xl bg-amber-50/60 border border-amber-200/50">
                <div className="flex items-center gap-2.5">
                  <Bookmark className="w-4 h-4 text-amber-600" />
                  <span className="text-xs font-medium text-slate-700">Saved Items (2.0x weight)</span>
                </div>
                <span className="text-sm font-bold text-slate-900">{savedProductIds.length}</span>
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200/60">
                <div className="flex items-center gap-2.5">
                  <Eye className="w-4 h-4 text-slate-500" />
                  <span className="text-xs font-medium text-slate-700">Viewed Items (1.0x weight)</span>
                </div>
                <span className="text-sm font-bold text-slate-900">{viewedProductIds.length}</span>
              </div>

              {recData && (
                <div className="p-3 rounded-xl bg-brand-50 border border-brand-100 text-xs text-brand-900 space-y-1">
                  <span className="font-bold block">Current Strategy:</span>
                  <p className="text-[11px] text-slate-700 leading-tight">
                    {recData.strategy_summary}
                  </p>
                </div>
              )}
            </div>
          </div>

          <button
            onClick={onClearHistory}
            className="w-full mt-6 py-2 px-3 border border-slate-200 hover:bg-slate-100 text-slate-600 rounded-xl text-xs font-semibold transition-colors"
          >
            Clear Interaction History (Reset to Cold Start)
          </button>
        </div>
      </div>

      {/* Recommendations Feed */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-slate-900">Recommended for You</h2>
            {recData?.is_cold_start && (
              <span className="bg-blue-100 text-blue-800 text-[11px] font-bold px-2.5 py-0.5 rounded-full border border-blue-200">
                Cold Start Discovery
              </span>
            )}
          </div>
          <span className="text-xs font-mono text-slate-500">
            {recData?.recommendations.length || 0} Products
          </span>
        </div>

        {loading && (
          <div className="py-20 flex flex-col items-center justify-center text-slate-400 gap-3">
            <Loader2 className="w-8 h-8 animate-spin text-brand-600" />
            <p className="text-sm font-medium">Computing content-based recommendations...</p>
          </div>
        )}

        {error && (
          <div className="p-4 bg-rose-50 border border-rose-200 rounded-2xl text-rose-700 text-sm flex items-center gap-2">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {!loading && !error && recData && recData.recommendations.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {recData.recommendations.map((item) => (
              <ProductCard
                key={item.product.product_id}
                product={item.product}
                score={item.recommendation_score}
                explanation={item.explanation}
                isSaved={savedProductIds.includes(item.product.product_id)}
                onToggleSave={onToggleSave}
                onClick={onSelectProduct}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
