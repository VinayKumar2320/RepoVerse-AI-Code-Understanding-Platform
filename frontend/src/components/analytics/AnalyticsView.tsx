'use client';

import React, { useState, useEffect } from 'react';
import { useRepoStore } from '../../store/useRepoStore';
import { api } from '../../services/api';
import { ArchitectureAnalytics } from '../../types';
import { BarChart3, AlertCircle, Layers, CheckCircle2, TrendingUp, Info } from 'lucide-react';

export const AnalyticsView: React.FC = () => {
  const { currentRepo } = useRepoStore();
  const [analytics, setAnalytics] = useState<ArchitectureAnalytics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      if (!currentRepo) return;
      setLoading(true);
      try {
        const data = await api.getArchitectureAnalytics(currentRepo.id);
        setAnalytics(data);
      } catch (e) {
        console.error('Failed to load architecture analytics:', e);
      } finally {
        setLoading(false);
      }
    };
    fetchMetrics();
  }, [currentRepo]);

  if (loading) {
    return (
      <div className="text-center p-12 text-slate-400">
        Calculating graph centrality, coupling metrics, and Tarjan SCC components...
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="text-center p-12 text-slate-500">
        Analytics could not be loaded.
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6 py-2">
      {/* Overview Stat Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <span className="text-xs text-slate-500 uppercase font-semibold">Total Modules</span>
          <span className="text-2xl font-bold text-white block mt-1">{analytics.total_modules}</span>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <span className="text-xs text-slate-500 uppercase font-semibold">Dependencies</span>
          <span className="text-2xl font-bold text-white block mt-1">{analytics.total_dependencies}</span>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <span className="text-xs text-slate-500 uppercase font-semibold">Dependency Cycles</span>
          <span className={`text-2xl font-bold block mt-1 ${analytics.dependency_cycles.length > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
            {analytics.dependency_cycles.length}
          </span>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <span className="text-xs text-slate-500 uppercase font-semibold">Cyclic Clusters</span>
          <span className="text-2xl font-bold text-slate-300 block mt-1">
            {analytics.strongly_connected_components.length}
          </span>
        </div>
      </div>

      {/* Summary Verdict */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex items-start space-x-3">
        <Info className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
        <div>
          <h4 className="text-xs font-bold text-indigo-300 uppercase tracking-wider mb-1">
            Architectural Health Verdict
          </h4>
          <p className="text-xs text-slate-300 leading-relaxed">
            {analytics.summary_verdict}
          </p>
        </div>
      </div>

      {/* Centrality & Instability Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <h3 className="text-sm font-bold text-white mb-3">Top Central Modules (PageRank Centrality)</h3>
        <div className="space-y-2">
          {analytics.top_central_modules.map((m, i) => (
            <div
              key={i}
              className="flex items-center justify-between p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs"
            >
              <div className="flex items-center space-x-3">
                <span className="font-mono text-indigo-400 font-semibold">{m.label}</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                  {m.entity_type}
                </span>
              </div>
              <div className="text-right">
                <span className="text-xs font-mono text-emerald-400 font-bold">
                  Score: {m.centrality_score}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
