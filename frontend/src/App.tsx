import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { DiscoverPage } from './pages/DiscoverPage';
import { RecommendationsPage } from './pages/RecommendationsPage';
import { AssistantPage } from './pages/AssistantPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { ProductModal } from './components/ProductModal';
import { Product } from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('discover');
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

  // LocalStorage persistence for user interaction history
  const [savedProductIds, setSavedProductIds] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem('furnifind_saved');
      return saved ? JSON.parse(saved) : ['FUR-DSK-001'];
    } catch {
      return ['FUR-DSK-001'];
    }
  });

  const [viewedProductIds, setViewedProductIds] = useState<string[]>(() => {
    try {
      const viewed = localStorage.getItem('furnifind_viewed');
      return viewed ? JSON.parse(viewed) : ['FUR-CHR-002', 'FUR-SOF-001'];
    } catch {
      return ['FUR-CHR-002', 'FUR-SOF-001'];
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem('furnifind_saved', JSON.stringify(savedProductIds));
    } catch (e) {
      console.warn('Could not save to localStorage', e);
    }
  }, [savedProductIds]);

  useEffect(() => {
    try {
      localStorage.setItem('furnifind_viewed', JSON.stringify(viewedProductIds));
    } catch (e) {
      console.warn('Could not save to localStorage', e);
    }
  }, [viewedProductIds]);

  const handleToggleSave = (product: Product) => {
    setSavedProductIds((prev) =>
      prev.includes(product.product_id)
        ? prev.filter((id) => id !== product.product_id)
        : [...prev, product.product_id]
    );
  };

  const handleSelectProduct = (product: Product) => {
    setSelectedProduct(product);
    setViewedProductIds((prev) =>
      prev.includes(product.product_id) ? prev : [...prev, product.product_id]
    );
  };

  const handleClearHistory = () => {
    setSavedProductIds([]);
    setViewedProductIds([]);
    try {
      localStorage.removeItem('furnifind_saved');
      localStorage.removeItem('furnifind_viewed');
    } catch (e) {
      console.warn('Could not clear localStorage', e);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-between selection:bg-brand-500 selection:text-white">
      <div>
        <Navbar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          savedCount={savedProductIds.length}
        />

        <main>
          {activeTab === 'discover' && (
            <DiscoverPage
              savedProductIds={savedProductIds}
              onToggleSave={handleToggleSave}
              onSelectProduct={handleSelectProduct}
            />
          )}

          {activeTab === 'recommendations' && (
            <RecommendationsPage
              savedProductIds={savedProductIds}
              viewedProductIds={viewedProductIds}
              onToggleSave={handleToggleSave}
              onSelectProduct={handleSelectProduct}
              onClearHistory={handleClearHistory}
            />
          )}

          {activeTab === 'assistant' && (
            <AssistantPage
              onSelectProduct={handleSelectProduct}
              savedProductIds={savedProductIds}
              onToggleSave={handleToggleSave}
            />
          )}

          {activeTab === 'analytics' && <AnalyticsPage />}
        </main>
      </div>

      {/* Product Details Modal */}
      <ProductModal
        product={selectedProduct}
        isSaved={selectedProduct ? savedProductIds.includes(selectedProduct.product_id) : false}
        onClose={() => setSelectedProduct(null)}
        onToggleSave={handleToggleSave}
      />

      {/* Global Footer */}
      <footer className="mt-16 bg-white border-t border-slate-200 py-8 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="font-bold text-slate-800">FurniFind AI</span>
            <span>• Multimodal E-Commerce Information Retrieval & Discovery</span>
          </div>

          <div className="flex items-center gap-4 text-slate-600">
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="hover:text-brand-600 transition-colors font-semibold"
            >
              OpenAPI Swagger Docs
            </a>
            <span className="text-slate-300">|</span>
            <span>FastAPI + PyTorch + Sentence Transformers + React + Vite</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
