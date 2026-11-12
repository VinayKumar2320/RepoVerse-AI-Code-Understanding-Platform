'use client';

import React, { useState, useEffect } from 'react';
import { useRepoStore } from '../../store/useRepoStore';
import { api } from '../../services/api';
import { CommitSummary, ArchitectureDiff } from '../../types';
import { History, GitCommit, GitCompare, Plus, Minus, RefreshCw, ArrowRight } from 'lucide-react';

export const GitTimeMachine: React.FC = () => {
  const { currentRepo } = useRepoStore();
  const [commits, setCommits] = useState<CommitSummary[]>([]);
  const [baseCommit, setBaseCommit] = useState<string>('');
  const [targetCommit, setTargetCommit] = useState<string>('');
  const [diff, setDiff] = useState<ArchitectureDiff | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    const fetchHistory = async () => {
      if (!currentRepo) return;
      try {
        const data = await api.getRepositoryHistory(currentRepo.id);
        setCommits(data.commits);
        if (data.commits.length >= 2) {
          setBaseCommit(data.commits[1].sha);
          setTargetCommit(data.commits[0].sha);
        } else if (data.commits.length === 1) {
          setBaseCommit(data.commits[0].sha);
          setTargetCommit(data.commits[0].sha);
        }
      } catch (e) {
        console.error('Failed to load git history:', e);
      }
    };
    fetchHistory();
  }, [currentRepo]);

  const handleCompare = async () => {
    if (!currentRepo || !baseCommit || !targetCommit) return;
    setLoading(true);
    try {
      const data = await api.getArchitectureDiff(currentRepo.id, baseCommit, targetCommit);
      setDiff(data);
    } catch (e) {
      console.error('Failed to compute architecture diff:', e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 py-2">
      {/* Time Machine Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center space-x-2">
              <History className="w-5 h-5 text-indigo-400" />
              <span>Git Time Machine & Architecture Evolution</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Select two commits in Git history to inspect architectural deltas, structural churn, and coupling changes.
            </p>
          </div>

          {/* Commit Selectors */}
          <div className="flex items-center space-x-2">
            <select
              value={baseCommit}
              onChange={(e) => setBaseCommit(e.target.value)}
              className="bg-slate-950 border border-slate-800 text-xs text-slate-300 rounded-lg px-2.5 py-1.5 font-mono focus:outline-none focus:border-brand-500"
            >
              {commits.map((c) => (
                <option key={c.sha} value={c.sha}>Base: {c.short_sha} - {c.message.slice(0, 25)}</option>
              ))}
            </select>

            <span className="text-slate-500">→</span>

            <select
              value={targetCommit}
              onChange={(e) => setTargetCommit(e.target.value)}
              className="bg-slate-950 border border-slate-800 text-xs text-slate-300 rounded-lg px-2.5 py-1.5 font-mono focus:outline-none focus:border-brand-500"
            >
              {commits.map((c) => (
                <option key={c.sha} value={c.sha}>Target: {c.short_sha} - {c.message.slice(0, 25)}</option>
              ))}
            </select>

            <button
              onClick={handleCompare}
              disabled={loading}
              className="px-3 py-1.5 bg-brand-600 hover:bg-brand-500 text-white rounded-lg text-xs font-semibold flex items-center space-x-1 transition shadow"
            >
              <GitCompare className="w-3.5 h-3.5" />
              <span>Compare</span>
            </button>
          </div>
        </div>
      </div>

      {/* Diff Results */}
      {diff && (
        <div className="space-y-4">
          {/* Summary Box */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <h3 className="text-sm font-bold text-white mb-2">Structural Evolution Summary</h3>
            <p className="text-xs text-slate-300 font-mono bg-slate-950 p-3 rounded-lg border border-slate-800">
              {diff.structural_summary}
            </p>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 pt-3 border-t border-slate-800">
              <div>
                <span className="text-[10px] text-slate-500 uppercase font-semibold">Added Nodes</span>
                <span className="text-base font-bold text-emerald-400 block">+{diff.added_nodes.length}</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 uppercase font-semibold">Removed Nodes</span>
                <span className="text-base font-bold text-rose-400 block">-{diff.removed_nodes.length}</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 uppercase font-semibold">Cycles Delta</span>
                <span className={`text-base font-bold block ${diff.cycle_delta > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                  {diff.cycle_delta >= 0 ? `+${diff.cycle_delta}` : diff.cycle_delta}
                </span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 uppercase font-semibold">Coupling Delta</span>
                <span className="text-base font-bold text-slate-200 block">{diff.coupling_delta}</span>
              </div>
            </div>
          </div>

          {/* Added & Removed Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-3 flex items-center space-x-1.5">
                <Plus className="w-3.5 h-3.5" />
                <span>Added Structural Nodes ({diff.added_nodes.length})</span>
              </h4>
              <div className="space-y-1.5 max-h-48 overflow-y-auto">
                {diff.added_nodes.length === 0 ? (
                  <span className="text-xs text-slate-500">No nodes added</span>
                ) : (
                  diff.added_nodes.map((n, i) => (
                    <div key={i} className="text-xs font-mono text-emerald-300 bg-slate-950 p-2 rounded border border-slate-800/80">
                      + {n.label} ({n.type})
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <h4 className="text-xs font-bold text-rose-400 uppercase tracking-wider mb-3 flex items-center space-x-1.5">
                <Minus className="w-3.5 h-3.5" />
                <span>Removed Structural Nodes ({diff.removed_nodes.length})</span>
              </h4>
              <div className="space-y-1.5 max-h-48 overflow-y-auto">
                {diff.removed_nodes.length === 0 ? (
                  <span className="text-xs text-slate-500">No nodes removed</span>
                ) : (
                  diff.removed_nodes.map((n, i) => (
                    <div key={i} className="text-xs font-mono text-rose-300 bg-slate-950 p-2 rounded border border-slate-800/80">
                      - {n.label} ({n.type})
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Historical Commits List */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <h3 className="text-sm font-bold text-white mb-3">Commit History</h3>
        <div className="space-y-2">
          {commits.map((c) => (
            <div
              key={c.sha}
              className="flex items-center justify-between p-3 bg-slate-950 rounded-lg border border-slate-800/60 text-xs"
            >
              <div className="flex items-center space-x-3">
                <span className="font-mono text-indigo-400 font-semibold">{c.short_sha}</span>
                <span className="text-slate-200">{c.message}</span>
              </div>
              <div className="flex items-center space-x-3 text-slate-500 text-[11px]">
                <span>{c.author}</span>
                <span>{c.date.slice(0, 10)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
