import React, { useState, useEffect } from 'react';
import { Product, SearchResponse, ActiveFilters } from '../types';
import { searchProducts, fetchProducts } from '../services/api';
import { ProductCard } from '../components/ProductCard';
import { FilterSidebar } from '../components/FilterSidebar';
import { ImageUploadModal } from '../components/ImageUploadModal';
import {
  Search,
  Camera,
  Sparkles,
  SlidersHorizontal,
  Loader2,
  AlertCircle,
  HelpCircle,
  Layers,
} from 'lucide-react';

interface DiscoverPageProps {
  savedProductIds: string[];
  onToggleSave: (product: Product) => void;
  onSelectProduct: (product: Product) => void;
}

const EXAMPLE_QUERIES = [
  'Scandinavian light oak study desk with drawers',
  'industrial desk under 15000',
  'emerald green velvet seating',
  'round wooden dining table width under 120 cm',
  'luxury leather couch for living room',
  'open ladder bookshelf in light wood',
];

export const DiscoverPage: React.FC<DiscoverPageProps> = ({
  savedProductIds,
  onToggleSave,
  onSelectProduct,
}) => {
  const [query, setQuery] = useState('');
  const [searchMode, setSearchMode] = useState<'hybrid' | 'semantic' | 'keyword'>('hybrid');
  const [filters, setFilters] = useState<ActiveFilters>({});
  const [sortBy, setSortBy] = useState('newest');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);
  const [catalogProducts, setCatalogProducts] = useState<Product[]>([]);
  const [isImageModalOpen, setIsImageModalOpen] = useState(false);

  // Load default catalogue on mount or when browsing without query
  useEffect(() => {
    if (!query.trim()) {
      loadCatalog();
    }
  }, [filters, sortBy]);

  const loadCatalog = async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetchProducts({
        category: filters.category,
        min_price: filters.min_price,
        max_price: filters.max_price,
        material: filters.material,
        colour: filters.colour,
        style: filters.style,
        availability: filters.availability,
        sort_by: sortBy,
        page_size: 24,
      });
      setCatalogProducts(resp.items);
      setSearchResults(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load catalogue.');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (overrideQuery?: string) => {
    const q = overrideQuery !== undefined ? overrideQuery : query;
    if (!q.trim()) {
      loadCatalog();
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const resp = await searchProducts({
        query: q,
        search_mode: searchMode,
        filters: filters,
        top_k: 24,
        alpha: 0.5,
      });
      setSearchResults(resp);
    } catch (err: any) {
      setError(err.message || 'Search execution failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Hero Search Section */}
      <div className="mb-8 text-center sm:text-left">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
          Find Furniture in Ordinary Language
        </h1>
        <p className="mt-2 text-slate-600 text-sm sm:text-base max-w-2xl">
          Powered by hybrid BM25 lexical keyword matching, pretrained sentence embeddings, and visual similarity.
        </p>

        {/* Search Bar Container */}
        <div className="mt-6 bg-white p-2 rounded-2xl shadow-lg border border-slate-200/80 max-w-3xl">
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
            <div className="flex-1 flex items-center gap-3 px-3">
              <Search className="w-5 h-5 text-slate-400 shrink-0" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="e.g. Modern Scandinavian desk with drawers, width below 120cm, under ₹15000"
                className="w-full text-sm text-slate-900 placeholder-slate-400 focus:outline-none py-2"
              />
            </div>

            <div className="flex items-center gap-2 px-2 pb-2 sm:pb-0 justify-end border-t sm:border-t-0 sm:border-l border-slate-100 pt-2 sm:pt-0">
              {/* Search Mode Selector */}
              <div className="flex items-center bg-slate-100 p-1 rounded-xl text-xs">
                {(['hybrid', 'semantic', 'keyword'] as const).map((mode) => (
                  <button
                    key={mode}
                    onClick={() => setSearchMode(mode)}
                    className={`px-2.5 py-1 rounded-lg capitalize font-medium transition-all ${
                      searchMode === mode
                        ? 'bg-white text-slate-900 shadow-xs font-semibold'
                        : 'text-slate-500 hover:text-slate-900'
                    }`}
                  >
                    {mode}
                  </button>
                ))}
              </div>

              {/* Multimodal Image Search Button */}
              <button
                type="button"
                onClick={() => setIsImageModalOpen(true)}
                className="p-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl transition-colors shrink-0"
                title="Search using photo"
              >
                <Camera className="w-4 h-4" />
              </button>

              {/* Submit Search */}
              <button
                type="button"
                onClick={() => handleSearch()}
                disabled={loading}
                className="px-5 py-2.5 bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs rounded-xl shadow-md transition-all flex items-center gap-1.5 shrink-0"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                <span>Search</span>
              </button>
            </div>
          </div>
        </div>

        {/* Example Query Pills */}
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold text-slate-400 flex items-center gap-1">
            <HelpCircle className="w-3.5 h-3.5" /> Try asking:
          </span>
          {EXAMPLE_QUERIES.map((ex) => (
            <button
              key={ex}
              onClick={() => {
                setQuery(ex);
                handleSearch(ex);
              }}
              className="text-xs text-slate-600 bg-white border border-slate-200 hover:border-brand-500 hover:text-brand-600 px-3 py-1 rounded-full shadow-2xs transition-all"
            >
              "{ex}"
            </button>
          ))}
        </div>
      </div>

      {/* Main Layout: Filters + Results */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Left Column: Filter Sidebar */}
        <div className="lg:col-span-1">
          <FilterSidebar
            filters={filters}
            onChange={(newFilters) => {
              setFilters(newFilters);
              if (query.trim()) {
                handleSearch();
              }
            }}
            onReset={() => {
              setFilters({});
              if (query.trim()) {
                handleSearch();
              }
            }}
          />
        </div>

        {/* Right Column: Results Grid */}
        <div className="lg:col-span-3 space-y-6">
          {/* AI Extracted Filters Banner */}
          {searchResults && (
            <div className="bg-slate-900 text-white rounded-2xl p-4 sm:p-5 shadow-md">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <Layers className="w-4 h-4 text-brand-400" />
                  <span className="text-sm font-bold">Query Understanding & Extracted Constraints</span>
                </div>
                <div className="flex items-center gap-3 text-xs text-slate-400">
                  <span>Latency: <strong className="text-slate-200">{searchResults.latency_ms} ms</strong></span>
                  <span>Matches: <strong className="text-brand-400">{searchResults.total_matches}</strong></span>
                  <span className="capitalize font-mono bg-slate-800 px-2 py-0.5 rounded text-slate-300">
                    Mode: {searchResults.search_mode}
                  </span>
                </div>
              </div>

              {/* Extracted Tokens */}
              <div className="mt-3 flex flex-wrap gap-2 text-xs">
                {searchResults.extracted_filters.category && (
                  <span className="bg-slate-800 text-slate-200 px-2.5 py-1 rounded-lg border border-slate-700">
                    Category: <strong className="text-white capitalize">{searchResults.extracted_filters.category}</strong>
                  </span>
                )}
                {searchResults.extracted_filters.max_price && (
                  <span className="bg-slate-800 text-slate-200 px-2.5 py-1 rounded-lg border border-slate-700">
                    Max Budget: <strong className="text-white">₹{searchResults.extracted_filters.max_price.toLocaleString('en-IN')}</strong>
                  </span>
                )}
                {searchResults.extracted_filters.max_width_cm && (
                  <span className="bg-slate-800 text-slate-200 px-2.5 py-1 rounded-lg border border-slate-700">
                    Max Width: <strong className="text-white">{searchResults.extracted_filters.max_width_cm} cm</strong>
                  </span>
                )}
                {searchResults.extracted_filters.style && (
                  <span className="bg-slate-800 text-slate-200 px-2.5 py-1 rounded-lg border border-slate-700">
                    Style: <strong className="text-white capitalize">{searchResults.extracted_filters.style}</strong>
                  </span>
                )}
                {searchResults.extracted_filters.material && (
                  <span className="bg-slate-800 text-slate-200 px-2.5 py-1 rounded-lg border border-slate-700">
                    Material: <strong className="text-white capitalize">{searchResults.extracted_filters.material}</strong>
                  </span>
                )}
                {searchResults.extracted_filters.colour && (
                  <span className="bg-slate-800 text-slate-200 px-2.5 py-1 rounded-lg border border-slate-700">
                    Colour: <strong className="text-white capitalize">{searchResults.extracted_filters.colour}</strong>
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Sorting and Results Header */}
          <div className="flex items-center justify-between pb-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              {searchResults ? `${searchResults.results.length} Ranked Results` : `${catalogProducts.length} Catalogue Items`}
            </span>
            {!searchResults && (
              <div className="flex items-center gap-2">
                <SlidersHorizontal className="w-3.5 h-3.5 text-slate-400" />
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="text-xs bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-700 focus:outline-none focus:ring-1 focus:ring-brand-500"
                >
                  <option value="newest">Newest Arrivals</option>
                  <option value="price_asc">Price: Low to High</option>
                  <option value="price_desc">Price: High to Low</option>
                  <option value="title_asc">Alphabetical</option>
                </select>
              </div>
            )}
          </div>

          {/* Loading State */}
          {loading && (
            <div className="py-20 flex flex-col items-center justify-center text-slate-400 gap-3">
              <Loader2 className="w-8 h-8 animate-spin text-brand-600" />
              <p className="text-sm font-medium">Retrieving and ranking catalogue furniture...</p>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-2xl text-rose-700 text-sm flex items-center gap-2">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Empty Results State */}
          {!loading && !error && searchResults && searchResults.results.length === 0 && (
            <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-4">
              <div className="w-14 h-14 bg-amber-50 text-amber-600 rounded-full flex items-center justify-center mx-auto text-2xl">
                🔍
              </div>
              <h3 className="text-base font-bold text-slate-900">
                No matching furniture found for "{searchResults.query}"
              </h3>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                No items in our verified catalogue met all of your hard constraints.
              </p>
              {searchResults.suggestions.length > 0 && (
                <div className="mt-4 p-4 bg-slate-50 border border-slate-200/80 rounded-xl text-left max-w-md mx-auto">
                  <span className="text-xs font-bold text-slate-800 block mb-2">Helpful suggestions:</span>
                  <ul className="text-xs text-slate-600 space-y-1 list-disc list-inside">
                    {searchResults.suggestions.map((s, idx) => (
                      <li key={idx}>{s}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Product Grid */}
          {!loading && !error && (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
              {searchResults
                ? searchResults.results.map((item) => (
                    <ProductCard
                      key={item.product.product_id}
                      product={item.product}
                      score={item.score}
                      explanation={item.match_explanation}
                      isSaved={savedProductIds.includes(item.product.product_id)}
                      onToggleSave={onToggleSave}
                      onClick={onSelectProduct}
                    />
                  ))
                : catalogProducts.map((prod) => (
                    <ProductCard
                      key={prod.product_id}
                      product={prod}
                      isSaved={savedProductIds.includes(prod.product_id)}
                      onToggleSave={onToggleSave}
                      onClick={onSelectProduct}
                    />
                  ))}
            </div>
          )}
        </div>
      </div>

      {/* Image Search Modal */}
      <ImageUploadModal
        isOpen={isImageModalOpen}
        onClose={() => setIsImageModalOpen(false)}
        onSelectProduct={onSelectProduct}
      />
    </div>
  );
};
