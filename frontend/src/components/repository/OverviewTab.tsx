'use client';

import React from 'react';
import { useRepoStore } from '../../store/useRepoStore';
import {
  FolderGit2,
  Terminal,
  Layers,
  FileCode2,
  CheckCircle2,
  Play,
  FlaskConical,
  ArrowRight,
  Boxes
} from 'lucide-react';

export const OverviewTab: React.FC = () => {
  const { overview, setActiveTab, setSelectedFile } = useRepoStore();

  if (!overview) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-slate-400">
        <Layers className="w-10 h-10 mb-3 animate-pulse text-slate-500" />
        <p>Analyzing repository architecture...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto py-2">
      {/* Hero Overview */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4 mb-4">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center space-x-2">
              <span>{overview.owner} / {overview.name}</span>
            </h2>
            <p className="text-sm text-slate-400 mt-1 max-w-3xl">
              {overview.description}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="px-3 py-1 bg-brand-500/10 text-brand-400 border border-brand-500/20 rounded-md text-xs font-semibold">
              {overview.primary_language || 'Polyglot'}
            </span>
            <span className="text-xs text-slate-400">
              Commit: <code className="bg-slate-800 px-1.5 py-0.5 rounded text-indigo-300">{overview.commit_sha.slice(0, 8)}</code>
            </span>
          </div>
        </div>

        {/* Problem Solved & Architecture Summary */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800/80">
            <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider block mb-1">
              Problem Solved
            </span>
            <p className="text-sm text-slate-300 leading-relaxed">
              {overview.problem_solved}
            </p>
          </div>
          <div className="bg-slate-950/60 p-4 rounded-lg border border-slate-800/80">
            <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider block mb-1">
              Architecture Summary
            </span>
            <p className="text-sm text-slate-300 leading-relaxed">
              {overview.architecture_summary}
            </p>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 pt-4 border-t border-slate-800/60">
          <div>
            <span className="text-xs text-slate-500 block">Total Files</span>
            <span className="text-lg font-bold text-slate-200">{overview.total_files}</span>
          </div>
          <div>
            <span className="text-xs text-slate-500 block">Total Lines of Code</span>
            <span className="text-lg font-bold text-slate-200">{overview.total_lines.toLocaleString()}</span>
          </div>
          <div>
            <span className="text-xs text-slate-500 block">Frameworks</span>
            <span className="text-lg font-bold text-slate-200">{overview.frameworks.join(', ') || 'Standard'}</span>
          </div>
          <div>
            <span className="text-xs text-slate-500 block">Entry Points</span>
            <span className="text-lg font-bold text-slate-200">{overview.entry_points.length} detected</span>
          </div>
        </div>
      </div>

      {/* Main Grid: Directories & Entry Points */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Important Directories */}
        <div className="md:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center space-x-2 mb-3">
            <FolderGit2 className="w-4 h-4 text-brand-500" />
            <span>Important Directories & Responsibilities</span>
          </h3>
          <div className="space-y-2">
            {overview.important_directories.map((dir, idx) => (
              <div
                key={idx}
                className="flex items-start justify-between p-3 bg-slate-950/70 rounded-lg border border-slate-800/60 hover:border-slate-700 transition"
              >
                <div>
                  <span className="font-mono text-xs font-bold text-indigo-400">{dir.path}/</span>
                  <p className="text-xs text-slate-400 mt-0.5">{dir.role}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Likely Entry Points */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center space-x-2 mb-3">
            <Play className="w-4 h-4 text-emerald-400" />
            <span>Likely Entry Points</span>
          </h3>
          <div className="space-y-2">
            {overview.entry_points.map((ep, idx) => (
              <button
                key={idx}
                onClick={() => setSelectedFile(ep)}
                className="w-full text-left p-2.5 bg-slate-950/70 rounded-lg border border-slate-800/60 hover:border-emerald-500/50 hover:bg-slate-900 transition flex items-center justify-between group"
              >
                <span className="font-mono text-xs text-slate-300 group-hover:text-emerald-300">{ep}</span>
                <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-emerald-400 transition" />
              </button>
            ))}
          </div>

          {/* Local Run & Test Commands */}
          <div className="mt-5 pt-4 border-t border-slate-800">
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center space-x-1.5">
              <Terminal className="w-3.5 h-3.5 text-slate-400" />
              <span>Verified Commands</span>
            </h4>
            <div className="space-y-2 text-xs font-mono">
              {overview.local_run_commands.map((cmd, i) => (
                <div key={i} className="bg-slate-950 p-2 rounded border border-slate-800/80 text-emerald-400">
                  $ {cmd}
                </div>
              ))}
              {overview.test_commands.map((cmd, i) => (
                <div key={i} className="bg-slate-950 p-2 rounded border border-slate-800/80 text-indigo-400">
                  $ {cmd}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
