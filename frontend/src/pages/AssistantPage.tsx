import React, { useState } from 'react';
import { Product, AssistantAskResponse } from '../types';
import { askAssistant } from '../services/api';
import {
  MessageSquare,
  Send,
  Sparkles,
  ShieldAlert,
  Loader2,
  CheckCircle2,
  HelpCircle,
  Tag,
} from 'lucide-react';
import { ProductCard } from '../components/ProductCard';

interface AssistantPageProps {
  onSelectProduct: (product: Product) => void;
  savedProductIds: string[];
  onToggleSave: (product: Product) => void;
}

interface Message {
  sender: 'user' | 'assistant';
  content: string;
  responsePayload?: AssistantAskResponse;
  timestamp: string;
}

const SUGGESTED_QUESTIONS = [
  'Which desk is the narrowest and costs less than ₹15,000?',
  'What is the cheapest chair available?',
  'What are the dimensions and materials of FUR-DSK-001?',
  'Can you recommend a Scandi dining chair for a compact apartment?',
  'What are the specs for FUR-MIS-001?',
];

export const AssistantPage: React.FC<AssistantPageProps> = ({
  onSelectProduct,
  savedProductIds,
  onToggleSave,
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: 'assistant',
      content:
        'Hello! I am your FurniFind Shopping Assistant. I answer questions strictly grounded in our verified furniture catalogue—including exact dimensions, prices, and materials. How can I help you discover the right furniture today?',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async (questionText?: string) => {
    const q = questionText || input;
    if (!q.trim() || loading) return;

    const userMessage: Message = {
      sender: 'user',
      content: q,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const resp = await askAssistant(q);
      const assistantMessage: Message = {
        sender: 'assistant',
        content: resp.answer,
        responsePayload: resp,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      const errorMessage: Message = {
        sender: 'assistant',
        content: `Sorry, an error occurred while processing your query: ${err.message}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-brand-600 font-bold text-xs uppercase tracking-wider mb-1">
          <MessageSquare className="w-4 h-4" />
          <span>Grounded RAG Q&A Engine</span>
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          FurniFind AI Shopping Assistant
        </h1>
        <p className="mt-1 text-sm text-slate-600 max-w-2xl">
          Ask questions about product specifications, comparisons, prices, and dimensions. Answers are strictly backed by catalogue data without hallucinating unrecorded specs.
        </p>
      </div>

      {/* Suggested Prompts */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs">
        <span className="text-xs font-bold text-slate-700 block mb-2 flex items-center gap-1.5">
          <HelpCircle className="w-3.5 h-3.5 text-brand-600" />
          Click a verified query to test deterministic catalogue comparisons:
        </span>
        <div className="flex flex-wrap gap-2">
          {SUGGESTED_QUESTIONS.map((q) => (
            <button
              key={q}
              onClick={() => handleSend(q)}
              className="text-xs text-slate-700 bg-slate-50 hover:bg-brand-50 hover:text-brand-700 border border-slate-200 hover:border-brand-300 px-3 py-1.5 rounded-xl transition-all text-left"
            >
              "{q}"
            </button>
          ))}
        </div>
      </div>

      {/* Chat Messages Log */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-4 sm:p-6 min-h-[460px] flex flex-col justify-between">
        <div className="space-y-6 overflow-y-auto max-h-[550px] pr-2 custom-scrollbar">
          {messages.map((m, idx) => (
            <div
              key={idx}
              className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}
            >
              <div className="flex items-center gap-2 mb-1 text-[11px] text-slate-400">
                <span className="font-semibold text-slate-700">
                  {m.sender === 'user' ? 'You' : 'FurniFind Assistant'}
                </span>
                <span>• {m.timestamp}</span>
              </div>

              <div
                className={`max-w-3xl rounded-2xl p-4 text-sm leading-relaxed ${
                  m.sender === 'user'
                    ? 'bg-slate-900 text-white rounded-tr-xs'
                    : 'bg-slate-50 border border-slate-200/80 text-slate-800 rounded-tl-xs space-y-4'
                }`}
              >
                <div className="whitespace-pre-line">{m.content}</div>

                {/* Structured Evidence Badges */}
                {m.responsePayload && m.responsePayload.structured_evidence.length > 0 && (
                  <div className="pt-3 border-t border-slate-200/80 space-y-2">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
                      Verified Catalogue Evidence ({m.responsePayload.structured_evidence.length} facts)
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {m.responsePayload.structured_evidence.map((ev, eIdx) => (
                        <span
                          key={eIdx}
                          className="text-[11px] bg-white border border-slate-200 text-slate-700 px-2.5 py-1 rounded-lg flex items-center gap-1.5"
                        >
                          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                          <strong className="text-slate-900 capitalize">{ev.attribute}:</strong> {String(ev.value)}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Referenced Product Cards */}
                {m.responsePayload && m.responsePayload.referenced_products.length > 0 && (
                  <div className="pt-3 border-t border-slate-200/80 space-y-2">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
                      Referenced Product Records
                    </span>
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                      {m.responsePayload.referenced_products.map((p) => (
                        <ProductCard
                          key={p.product_id}
                          product={p}
                          isSaved={savedProductIds.includes(p.product_id)}
                          onToggleSave={onToggleSave}
                          onClick={onSelectProduct}
                        />
                      ))}
                    </div>
                  </div>
                )}

                {/* Missing Data Disclaimers */}
                {m.responsePayload && m.responsePayload.missing_data_notes && (
                  <div className="p-2.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-center gap-2">
                    <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0" />
                    <span>{m.responsePayload.missing_data_notes}</span>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-2 text-xs text-slate-500 bg-slate-50 p-3 rounded-xl border border-slate-200 w-fit">
              <Loader2 className="w-4 h-4 animate-spin text-brand-600" />
              <span>Querying verified catalogue facts and comparing dimensions...</span>
            </div>
          )}
        </div>

        {/* Input Form */}
        <div className="mt-4 pt-4 border-t border-slate-100 flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask anything about our furniture catalogue, dimensions, or budget comparisons..."
            className="flex-1 text-sm bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
          />
          <button
            onClick={() => handleSend()}
            disabled={loading || !input.trim()}
            className="p-3 bg-brand-600 hover:bg-brand-700 text-white rounded-xl shadow-xs disabled:opacity-50 transition-all"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
