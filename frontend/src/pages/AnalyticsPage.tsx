import React, { useState, useEffect } from 'react';
import { EvaluationResponse } from '../types';
import { fetchEvaluationAnalytics } from '../services/api';
import { BarChart3, CheckCircle2, AlertCircle, Loader2, ArrowUpRight, FileText } from 'lucide-react';

export const AnalyticsPage: React.FC = () => {
  const [data, setData] = useState<EvaluationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetchEvaluationAnalytics();
      setData(resp);
    } catch (err: any) {
      setError(err.message || 'Failed to load evaluation metrics.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Page Header */}
      <div>
        <div className="flex items-center gap-2 text-brand-600 font-bold text-xs uppercase tracking-wider mb-1">
          <BarChart3 className="w-4 h-4" />
          <span>Reproducible Search Evaluation Pipeline</span>
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          Retrieval Benchmark & Experiment Results
        </h1>
        <p className="mt-1 text-sm text-slate-600 max-w-2xl">
          Offline evaluation comparing Keyword (BM25), Semantic (Sentence Transformers), and Hybrid Retrieval over a curated test collection with labelled ground-truth relevance.
        </p>
      </div>

      {loading && (
        <div className="py-20 flex flex-col items-center justify-center text-slate-400 gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-brand-600" />
          <p className="text-sm font-medium">Running retrieval benchmark pipeline across test collection...</p>
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-2xl text-rose-700 text-sm flex items-center gap-2">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {!loading && data && (
        <div className="space-y-8">
          {/* Summary Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                Evaluated Test Queries
              </span>
              <span className="text-2xl font-black text-slate-900 mt-1 block">
                {data.total_queries}
              </span>
              <span className="text-[11px] text-slate-400 mt-1 block">
                Covers synonyms, styles, dimensions
              </span>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                BM25 Keyword NDCG@5
              </span>
              <span className="text-2xl font-black text-slate-700 mt-1 block">
                {(data.comparison.keyword.ndcg_at_5 * 100).toFixed(1)}%
              </span>
              <span className="text-[11px] text-slate-400 mt-1 block">
                Strong on exact token matches
              </span>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                Semantic Recall@5
              </span>
              <span className="text-2xl font-black text-blue-600 mt-1 block">
                {(data.comparison.semantic.recall_at_5 * 100).toFixed(1)}%
              </span>
              <span className="text-[11px] text-slate-400 mt-1 block">
                Dense sentence embeddings
              </span>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                Hybrid NDCG@5
              </span>
              <span className="text-2xl font-black text-brand-600 mt-1 block">
                {(data.comparison.hybrid.ndcg_at_5 * 100).toFixed(1)}%
              </span>
              <span className="text-[11px] text-slate-400 mt-1 block">
                Hard constraint filtering + soft blend
              </span>
            </div>
          </div>

          {/* Comparative Benchmark Table */}
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
            <div className="p-5 border-b border-slate-100 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900">
                  Search Methodology Comparison Matrix
                </h3>
                <p className="text-xs text-slate-500">
                  Evaluated at rank cutoff K = 5
                </p>
              </div>
              <span className="text-xs font-mono text-slate-400">
                Evaluation timestamp: {new Date(data.timestamp).toLocaleString()}
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 uppercase tracking-wider text-[11px] border-b border-slate-200">
                  <tr>
                    <th className="py-3.5 px-6 font-bold">Retrieval Method</th>
                    <th className="py-3.5 px-6 font-bold">Precision@5</th>
                    <th className="py-3.5 px-6 font-bold">Recall@5</th>
                    <th className="py-3.5 px-6 font-bold">NDCG@5</th>
                    <th className="py-3.5 px-6 font-bold">MRR (Mean Reciprocal Rank)</th>
                    <th className="py-3.5 px-6 font-bold">Empty Result Rate</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  <tr className="hover:bg-slate-50/50">
                    <td className="py-4 px-6 font-bold text-slate-900">Keyword (BM25 Baseline)</td>
                    <td className="py-4 px-6 font-mono">{(data.comparison.keyword.precision_at_5 * 100).toFixed(2)}%</td>
                    <td className="py-4 px-6 font-mono">{(data.comparison.keyword.recall_at_5 * 100).toFixed(2)}%</td>
                    <td className="py-4 px-6 font-mono">{(data.comparison.keyword.ndcg_at_5 * 100).toFixed(2)}%</td>
                    <td className="py-4 px-6 font-mono">{data.comparison.keyword.mrr.toFixed(4)}</td>
                    <td className="py-4 px-6 font-mono text-slate-500">{(data.comparison.keyword.empty_result_rate * 100).toFixed(1)}%</td>
                  </tr>
                  <tr className="hover:bg-slate-50/50">
                    <td className="py-4 px-6 font-bold text-slate-900">Semantic (Dense MiniLM-L6)</td>
                    <td className="py-4 px-6 font-mono">{(data.comparison.semantic.precision_at_5 * 100).toFixed(2)}%</td>
                    <td className="py-4 px-6 font-mono">{(data.comparison.semantic.recall_at_5 * 100).toFixed(2)}%</td>
                    <td className="py-4 px-6 font-mono">{(data.comparison.semantic.ndcg_at_5 * 100).toFixed(2)}%</td>
                    <td className="py-4 px-6 font-mono">{data.comparison.semantic.mrr.toFixed(4)}</td>
                    <td className="py-4 px-6 font-mono text-slate-500">{(data.comparison.semantic.empty_result_rate * 100).toFixed(1)}%</td>
                  </tr>
                  <tr className="bg-brand-50/40 hover:bg-brand-50/70 font-semibold text-slate-900">
                    <td className="py-4 px-6 font-bold text-brand-800 flex items-center gap-1.5">
                      <span>Hybrid (BM25 + Dense + Hard Filters)</span>
                      <span className="text-[10px] bg-brand-200 text-brand-900 px-1.5 py-0.5 rounded">Production</span>
                    </td>
                    <td className="py-4 px-6 font-mono font-bold text-brand-900">{(data.comparison.hybrid.precision_at_5 * 100).toFixed(2)}%</td>
                    <td className="py-4 px-6 font-mono font-bold text-brand-900">{(data.comparison.hybrid.recall_at_5 * 100).toFixed(2)}%</td>
                    <td className="py-4 px-6 font-mono font-bold text-brand-900">{(data.comparison.hybrid.ndcg_at_5 * 100).toFixed(2)}%</td>
                    <td className="py-4 px-6 font-mono font-bold text-brand-900">{data.comparison.hybrid.mrr.toFixed(4)}</td>
                    <td className="py-4 px-6 font-mono text-slate-500">{(data.comparison.hybrid.empty_result_rate * 100).toFixed(1)}%</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Technical Analysis Notes */}
          <div className="bg-slate-900 text-white rounded-2xl p-6 shadow-md space-y-3">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-brand-400" />
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Information Retrieval Evaluation Findings
              </h3>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              {data.analysis_notes}
            </p>
          </div>

          {/* Detailed Per-Query Breakdown */}
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
            <div className="p-5 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-900">
                Per-Query Benchmark Breakdown
              </h3>
              <p className="text-xs text-slate-500">
                Evaluation results on individual queries under Hybrid Retrieval
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 uppercase tracking-wider text-[10px] border-b border-slate-200">
                  <tr>
                    <th className="py-3 px-4 font-bold">Query ID</th>
                    <th className="py-3 px-4 font-bold">Natural Language Query</th>
                    <th className="py-3 px-4 font-bold">Query Type</th>
                    <th className="py-3 px-4 font-bold">Ground Truth</th>
                    <th className="py-3 px-4 font-bold">Retrieved</th>
                    <th className="py-3 px-4 font-bold">P@5</th>
                    <th className="py-3 px-4 font-bold">R@5</th>
                    <th className="py-3 px-4 font-bold">NDCG@5</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {data.query_details.map((q) => (
                    <tr key={q.query_id} className="hover:bg-slate-50/50">
                      <td className="py-3 px-4 font-mono font-bold text-slate-900">{q.query_id}</td>
                      <td className="py-3 px-4 font-medium text-slate-800">"{q.query}"</td>
                      <td className="py-3 px-4">
                        <span className="bg-slate-100 text-slate-600 px-2 py-0.5 rounded text-[10px] font-mono capitalize">
                          {q.query_type.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono">{q.ground_truth_count}</td>
                      <td className="py-3 px-4 font-mono">{q.retrieved_count}</td>
                      <td className="py-3 px-4 font-mono">{(q.precision_at_5 * 100).toFixed(0)}%</td>
                      <td className="py-3 px-4 font-mono">{(q.recall_at_5 * 100).toFixed(0)}%</td>
                      <td className="py-3 px-4 font-mono font-bold text-slate-900">{(q.ndcg_at_5 * 100).toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
