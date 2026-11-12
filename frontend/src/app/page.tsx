'use client';

import React, { useState, useEffect } from 'react';
import { useRepoStore, TabType } from '../store/useRepoStore';
import { api } from '../services/api';
import { OverviewTab } from '../components/repository/OverviewTab';
import { ArchitectureGraph } from '../components/graph/ArchitectureGraph';
import { CodeFlowExplorer } from '../components/codeflow/CodeFlowExplorer';
import { AdaptiveLearningStudio } from '../components/learning/AdaptiveLearningStudio';
import { AskRepositoryChat } from '../components/chat/AskRepositoryChat';
import { GitTimeMachine } from '../components/history/GitTimeMachine';
import { ArchitectureLab } from '../components/analytics/ArchitectureLab';
import { SourceViewer } from '../components/code/SourceViewer';
import { AnalyticsView } from '../components/analytics/AnalyticsView';

import {
  Compass,
  Search,
  Layers,
  GraduationCap,
  GitBranch,
  Play,
  MessageSquare,
  History,
  FlaskConical,
  FileCode2,
  BarChart3,
  Sparkles,
  Loader2,
  CheckCircle2,
  ArrowRight
} from 'lucide-react';

export default function HomePage() {
  const { currentRepo, activeTab, setCurrentRepo, setOverview, setActiveTab } = useRepoStore();
  const [urlInput, setUrlInput] = useState<string>('https://github.com/pallets/flask');
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [progressMsg, setProgressMsg] = useState<string>('');
  const [errorMsg, setErrorMsg] = useState<string>('');

  // Auto-load initial repo on mount
  useEffect(() => {
    const loadDefault = async () => {
      try {
        const repos = await api.getRepositories();
        if (repos.length > 0) {
          setCurrentRepo(repos[0]);
          const ov = await api.getRepositoryOverview(repos[0].id);
          setOverview(ov);
        }
      } catch (e) {
        console.warn('Initial repository load deferred:', e);
      }
    };
    loadDefault();
  }, [setCurrentRepo, setOverview]);

  const handleStartAnalysis = async (targetUrl?: string) => {
    const url = targetUrl || urlInput;
    if (!url.trim()) return;

    setAnalyzing(true);
    setErrorMsg('');
    setProgressMsg('Initiating repository clone and security validation...');

    try {
      const job = await api.analyzeRepository(url);
      const pollInterval = setInterval(async () => {
        try {
          const status = await api.getRepositoryStatus(job.repository_id);
          setProgressMsg(`${status.current_step} (${status.progress_percentage}%)`);

          if (status.status === 'completed' && status.snapshot_id) {
            clearInterval(pollInterval);
            const repo = await api.getRepository(job.repository_id);
            const ov = await api.getRepositoryOverview(job.repository_id);
            setCurrentRepo(repo);
            setOverview(ov);
            setAnalyzing(false);
            setProgressMsg('');
          } else if (status.status === 'failed') {
            clearInterval(pollInterval);
            setErrorMsg(status.error || 'Repository analysis failed.');
            setAnalyzing(false);
          }
        } catch (err: any) {
          clearInterval(pollInterval);
          setErrorMsg(err.message || 'Error tracking job status.');
          setAnalyzing(false);
        }
      }, 1500);
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to submit analysis job.');
      setAnalyzing(false);
    }
  };

  const tabs: Array<{ id: TabType; label: string; icon: any }> = [
    { id: 'overview', label: 'Overview', icon: Layers },
    { id: 'graph', label: 'Architecture Map', icon: Compass },
    { id: 'codeflow', label: 'Code Flow', icon: Play },
    { id: 'learning', label: 'Adaptive Studio', icon: GraduationCap },
    { id: 'chat', label: 'Ask RepoVerse', icon: MessageSquare },
    { id: 'history', label: 'Git Time Machine', icon: History },
    { id: 'lab', label: 'Architecture Lab', icon: FlaskConical },
    { id: 'source', label: 'Source Viewer', icon: FileCode2 },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
  ];

  return (
    <div className="flex flex-col flex-1 space-y-4">
      {/* Top Search & Ingestion Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex-1 w-full flex items-center space-x-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Paste public GitHub repository URL (e.g. https://github.com/pallets/flask)"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleStartAnalysis()}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-brand-500 font-mono"
            />
          </div>

          <button
            onClick={() => handleStartAnalysis()}
            disabled={analyzing}
            className="px-4 py-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition shadow"
          >
            {analyzing ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                <span>Analyze Repo</span>
              </>
            )}
          </button>
        </div>

        {/* Quick Demo Repositories */}
        <div className="flex items-center space-x-2 text-xs text-slate-400 shrink-0">
          <span>Examples:</span>
          <button
            onClick={() => {
              setUrlInput('https://github.com/pallets/flask');
              handleStartAnalysis('https://github.com/pallets/flask');
            }}
            className="px-2.5 py-1 bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded text-slate-300 font-mono text-[11px] transition"
          >
            pallets/flask
          </button>
          <button
            onClick={() => {
              setUrlInput('https://github.com/facebook/react');
              handleStartAnalysis('https://github.com/facebook/react');
            }}
            className="px-2.5 py-1 bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded text-slate-300 font-mono text-[11px] transition"
          >
            facebook/react
          </button>
        </div>
      </div>

      {/* Progress / Error Alerts */}
      {progressMsg && (
        <div className="bg-brand-950/40 border border-brand-500/30 p-3 rounded-lg text-xs text-brand-300 flex items-center space-x-2 animate-pulse">
          <Loader2 className="w-4 h-4 animate-spin text-brand-400" />
          <span>{progressMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div className="bg-rose-950/40 border border-rose-500/30 p-3 rounded-lg text-xs text-rose-300">
          {errorMsg}
        </div>
      )}

      {/* Main Workspace Tabs Header */}
      <div className="flex items-center space-x-1 border-b border-slate-800 pb-2 overflow-x-auto">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-xs font-semibold whitespace-nowrap transition ${
                isActive
                  ? 'bg-slate-800 text-brand-400 border border-slate-700/60 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab Panels */}
      <div className="flex-1">
        {activeTab === 'overview' && <OverviewTab />}
        {activeTab === 'graph' && <ArchitectureGraph />}
        {activeTab === 'codeflow' && <CodeFlowExplorer />}
        {activeTab === 'learning' && <AdaptiveLearningStudio />}
        {activeTab === 'chat' && <AskRepositoryChat />}
        {activeTab === 'history' && <GitTimeMachine />}
        {activeTab === 'lab' && <ArchitectureLab />}
        {activeTab === 'source' && <SourceViewer />}
        {activeTab === 'analytics' && <AnalyticsView />}
      </div>
    </div>
  );
}
