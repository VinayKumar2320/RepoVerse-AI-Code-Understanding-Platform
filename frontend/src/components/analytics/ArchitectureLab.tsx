'use client';

import React, { useState, useEffect } from 'react';
import { useRepoStore } from '../../store/useRepoStore';
import { api } from '../../services/api';
import { SimulationResponse, ArchitectureAnalytics } from '../../types';
import { FlaskConical, ArrowRight, Play, CheckCircle2, ShieldAlert, Sparkles, RefreshCw } from 'lucide-react';

export const ArchitectureLab: React.FC = () => {
  const { currentRepo } = useRepoStore();
  const [analytics, setAnalytics] = useState<ArchitectureAnalytics | null>(null);
  const [selectedSource, setSelectedSource] = useState<string>('');
  const [selectedTarget, setSelectedTarget] = useState<string>('');
  const [action, setAction] = useState<string>('remove_dependency');
  const [simulationResult, setSimulationResult] = useState<SimulationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    const fetchAnalytics = async () => {
      if (!currentRepo) return;
      try {
        const data = await api.getArchitectureAnalytics(currentRepo.id);
        setAnalytics(data);
        if (data.fan_out_hotspots.length) {
          setSelectedSource(data.fan_out_hotspots[0].node_id);
        }
      } catch (e) {
        console.error('Failed to load analytics:', e);
      }
    };
    fetchAnalytics();
  }, [currentRepo]);

  const handleSimulate = async () => {
    if (!currentRepo || !selectedSource) return;
    setLoading(true);
    try {
      const res = await api.runSimulation(currentRepo.id, [
        {
          action: action,
          source_node: selectedSource,
          target_node: selectedTarget || undefined,
        },
      ]);
      setSimulationResult(res);
    } catch (e) {
      console.error('Simulation failed:', e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 py-2">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h2 className="text-xl font-bold text-white flex items-center space-x-2">
          <FlaskConical className="w-5 h-5 text-purple-400" />
          <span>Architecture Lab: Speculative &quot;What-If&quot; Simulator</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1 max-w-3xl">
          Simulate hypothetical structural refactorings (removing couplings, decoupling cycles, re-architecting boundaries)
          on an in-memory graph copy. The real repository is never modified.
        </p>

        {/* Experiment Controls */}
        <div className="mt-5 p-4 bg-slate-950 rounded-lg border border-slate-800 grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
          <div>
            <label className="text-[11px] font-semibold text-slate-400 block mb-1">Action</label>
            <select
              value={action}
              onChange={(e) => setAction(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 text-xs text-slate-200 rounded-md p-2 focus:outline-none focus:border-brand-500"
            >
              <option value="remove_dependency">Remove Dependency Edge</option>
              <option value="add_dependency">Add Dependency Edge</option>
              <option value="move_module">Move Module to Subsystem</option>
            </select>
          </div>

          <div>
            <label className="text-[11px] font-semibold text-slate-400 block mb-1">Source Module</label>
            <input
              type="text"
              placeholder="e.g. file::services.py"
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 text-xs text-slate-200 rounded-md p-2 font-mono focus:outline-none focus:border-brand-500"
            />
          </div>

          <div>
            <label className="text-[11px] font-semibold text-slate-400 block mb-1">Target Module (Optional)</label>
            <input
              type="text"
              placeholder="e.g. file::models.py"
              value={selectedTarget}
              onChange={(e) => setSelectedTarget(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 text-xs text-slate-200 rounded-md p-2 font-mono focus:outline-none focus:border-brand-500"
            />
          </div>

          <button
            onClick={handleSimulate}
            disabled={loading || !selectedSource}
            className="w-full py-2 px-4 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white rounded-md text-xs font-semibold flex items-center justify-center space-x-1.5 transition shadow"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Run Simulation</span>
          </button>
        </div>
      </div>

      {/* Simulation Results */}
      {simulationResult && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Simulation Impact Analysis</span>
          </h3>

          <p className="text-xs text-slate-200 font-mono bg-slate-950 p-3 rounded-lg border border-slate-800">
            {simulationResult.impact_summary}
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-2">
            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-semibold block">Original Cycles</span>
              <span className="text-lg font-bold text-slate-300">{simulationResult.original_cycles_count}</span>
            </div>
            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-semibold block">Simulated Cycles</span>
              <span className="text-lg font-bold text-emerald-400">{simulationResult.simulated_cycles_count}</span>
            </div>
            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-semibold block">Original Coupling</span>
              <span className="text-lg font-bold text-slate-300">{simulationResult.original_coupling}</span>
            </div>
            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-semibold block">Simulated Coupling</span>
              <span className="text-lg font-bold text-indigo-400">{simulationResult.simulated_coupling}</span>
            </div>
          </div>
        </div>
      )}

      {/* Analytics Reference Cards */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <h4 className="text-xs font-bold text-indigo-400 uppercase tracking-wider mb-3">
              Efferent Coupling Hotspots (High Fan-Out)
            </h4>
            <div className="space-y-2">
              {analytics.fan_out_hotspots.map((h, i) => (
                <button
                  key={i}
                  onClick={() => setSelectedSource(h.node_id)}
                  className="w-full text-left p-2.5 bg-slate-950 hover:bg-slate-800 rounded border border-slate-800 text-xs flex items-center justify-between transition group"
                >
                  <span className="font-mono text-slate-300 group-hover:text-indigo-300">{h.label}</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-400">
                    Fan-Out: {h.fan_out}
                  </span>
                </button>
              ))}
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-3">
              Afferent Coupling Hotspots (High Fan-In)
            </h4>
            <div className="space-y-2">
              {analytics.fan_in_hotspots.map((h, i) => (
                <button
                  key={i}
                  onClick={() => setSelectedTarget(h.node_id)}
                  className="w-full text-left p-2.5 bg-slate-950 hover:bg-slate-800 rounded border border-slate-800 text-xs flex items-center justify-between transition group"
                >
                  <span className="font-mono text-slate-300 group-hover:text-emerald-300">{h.label}</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400">
                    Fan-In: {h.fan_in}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
