'use client';

import React, { useState, useEffect } from 'react';
import { useRepoStore } from '../../store/useRepoStore';
import { api } from '../../services/api';
import { CodeFlowResponse, CodeFlowNode } from '../../types';
import { GitCommit, ArrowDown, Play, FileCode, CheckCircle2, ChevronRight } from 'lucide-react';

export const CodeFlowExplorer: React.FC = () => {
  const { currentRepo, overview, setSelectedFile } = useRepoStore();
  const [selectedEntry, setSelectedEntry] = useState<string>('');
  const [trace, setTrace] = useState<CodeFlowResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    if (overview?.entry_points.length) {
      setSelectedEntry(overview.entry_points[0]);
    }
  }, [overview]);

  useEffect(() => {
    const fetchTrace = async () => {
      if (!currentRepo) return;
      setLoading(true);
      try {
        const data = await api.getCodeFlowTrace(currentRepo.id, selectedEntry);
        setTrace(data);
      } catch (e) {
        console.error('Failed to trace code flow:', e);
      } finally {
        setLoading(false);
      }
    };
    fetchTrace();
  }, [currentRepo, selectedEntry]);

  return (
    <div className="max-w-5xl mx-auto space-y-6 py-2">
      {/* Selector & Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center space-x-2">
              <Play className="w-5 h-5 text-emerald-400" />
              <span>Code Flow & Execution Path Explorer</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Statically trace call hierarchies from entry points down through services and database layers.
            </p>
          </div>

          {/* Entry Point Selector */}
          <div className="flex items-center space-x-2">
            <span className="text-xs text-slate-400 font-semibold">Entry:</span>
            <select
              value={selectedEntry}
              onChange={(e) => setSelectedEntry(e.target.value)}
              className="bg-slate-950 border border-slate-800 text-xs text-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:border-brand-500 font-mono"
            >
              {overview?.entry_points.map((ep, i) => (
                <option key={i} value={ep}>{ep}</option>
              ))}
            </select>
          </div>
        </div>

        {trace?.narrative && (
          <div className="mt-4 p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs text-slate-300">
            {trace.narrative}
          </div>
        )}
      </div>

      {/* Execution Flow Timeline */}
      {loading ? (
        <div className="text-center p-12 text-slate-400 text-sm">
          Tracing execution calls across static AST graph...
        </div>
      ) : trace && trace.nodes.length > 0 ? (
        <div className="relative pl-6 space-y-4 before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
          {trace.nodes.map((node, idx) => (
            <div key={node.id} className="relative group">
              {/* Timeline Indicator Dot */}
              <div className="absolute -left-6 top-4 w-3.5 h-3.5 rounded-full border-2 border-slate-950 bg-emerald-500 group-hover:scale-125 transition"></div>

              {/* Card */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 hover:border-slate-700 transition flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      Step {node.step_order}: {node.kind}
                    </span>
                    <span className="text-[10px] text-slate-500">
                      Confidence: {node.confidence}
                    </span>
                  </div>
                  <h4 className="text-sm font-bold text-white font-mono">{node.symbol_name}()</h4>
                  <p className="text-xs text-slate-400 font-mono mt-0.5">
                    {node.file_path}:{node.start_line}
                  </p>
                </div>

                <button
                  onClick={() => setSelectedFile(node.file_path, node.start_line)}
                  className="px-3 py-1.5 bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded-lg text-xs font-semibold text-indigo-300 flex items-center space-x-1.5 transition self-start md:self-center"
                >
                  <FileCode className="w-3.5 h-3.5" />
                  <span>View Source</span>
                </button>
              </div>

              {/* Down Arrow connector if not last */}
              {idx < trace.nodes.length - 1 && (
                <div className="flex justify-center -my-1 text-slate-600">
                  <ArrowDown className="w-4 h-4" />
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center p-12 text-slate-500">
          No static execution steps detected for this entry point.
        </div>
      )}
    </div>
  );
};
