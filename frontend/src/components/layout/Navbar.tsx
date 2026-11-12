'use client';

import React from 'react';
import { useRepoStore, ExperienceLevel } from '../../store/useRepoStore';
import { Compass, GitBranch, Cpu, GraduationCap, ShieldCheck } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { currentRepo, experienceLevel, setExperienceLevel } = useRepoStore();

  return (
    <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-50 px-6 py-3 flex items-center justify-between">
      <div className="flex items-center space-x-3">
        <div className="p-2 bg-gradient-to-tr from-brand-600 to-indigo-500 rounded-lg shadow-md shadow-brand-500/20">
          <Compass className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-bold text-lg tracking-tight text-white">RepoVerse</span>
            <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              Digital Twin
            </span>
          </div>
          <p className="text-xs text-slate-400 hidden sm:block">
            Understand Code. Explore Architecture. Travel Through Git History.
          </p>
        </div>
      </div>

      {currentRepo && (
        <div className="hidden md:flex items-center space-x-2 bg-slate-800/80 px-3 py-1.5 rounded-md border border-slate-700/60 text-xs">
          <GitBranch className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-slate-300 font-semibold">{currentRepo.owner}/{currentRepo.name}</span>
          <span className="text-slate-500">({currentRepo.default_branch})</span>
        </div>
      )}

      {/* Adaptive Mode Switcher */}
      <div className="flex items-center bg-slate-950 p-1 rounded-lg border border-slate-800">
        {(['beginner', 'developer', 'senior'] as ExperienceLevel[]).map((level) => {
          const isActive = experienceLevel === level;
          const labels: Record<ExperienceLevel, string> = {
            beginner: 'Beginner',
            developer: 'Developer',
            senior: 'Senior Engineer',
          };
          return (
            <button
              key={level}
              onClick={() => setExperienceLevel(level)}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${
                isActive
                  ? 'bg-brand-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {labels[level]}
            </button>
          );
        })}
      </div>
    </header>
  );
};
