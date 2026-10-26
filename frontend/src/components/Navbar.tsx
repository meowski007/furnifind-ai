import React from 'react';
import { Compass, Sparkles, MessageSquare, BarChart3, Bookmark } from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  savedCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, savedCount }) => {
  const navItems = [
    { id: 'discover', label: 'Discover', icon: Compass },
    { id: 'recommendations', label: 'Recommendations', icon: Sparkles },
    { id: 'assistant', label: 'AI Assistant', icon: MessageSquare },
    { id: 'analytics', label: 'Search Analytics', icon: BarChart3 },
  ];

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => setActiveTab('discover')}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-700 to-brand-500 flex items-center justify-center text-white shadow-md shadow-brand-500/20">
              <span className="text-xl">🪑</span>
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-xl tracking-tight text-slate-900">FurniFind</span>
                <span className="bg-brand-100 text-brand-800 text-xs font-semibold px-2 py-0.5 rounded-full border border-brand-200">
                  AI Engine
                </span>
              </div>
              <p className="text-xs text-slate-500 hidden sm:block">Multimodal Furniture Discovery & RAG</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="flex items-center gap-1 sm:gap-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-slate-900 text-white shadow-xs'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="hidden md:inline">{item.label}</span>
                </button>
              );
            })}

            {/* Saved Items Count */}
            <div className="ml-2 pl-2 border-l border-slate-200 flex items-center">
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-amber-50 text-amber-900 border border-amber-200/80">
                <Bookmark className="w-3.5 h-3.5 fill-amber-500 text-amber-500" />
                <span>{savedCount}</span>
                <span className="hidden sm:inline">Saved</span>
              </span>
            </div>
          </nav>
        </div>
      </div>
    </header>
  );
};
