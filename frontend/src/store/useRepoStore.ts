import { create } from 'zustand';
import { Repository, RepositoryOverview } from '../types';

export type TabType =
  | 'overview'
  | 'graph'
  | 'codeflow'
  | 'learning'
  | 'chat'
  | 'history'
  | 'lab'
  | 'source'
  | 'analytics';

export type ExperienceLevel = 'beginner' | 'developer' | 'senior';

interface RepoState {
  currentRepo: Repository | null;
  overview: RepositoryOverview | null;
  activeTab: TabType;
  experienceLevel: ExperienceLevel;
  selectedFile: string | null;
  selectedLine: number | null;
  selectedSymbol: string | null;

  setCurrentRepo: (repo: Repository | null) => void;
  setOverview: (overview: RepositoryOverview | null) => void;
  setActiveTab: (tab: TabType) => void;
  setExperienceLevel: (level: ExperienceLevel) => void;
  setSelectedFile: (file: string | null, line?: number | null) => void;
  setSelectedSymbol: (symbol: string | null) => void;
}

export const useRepoStore = create<RepoState>((set) => ({
  currentRepo: null,
  overview: null,
  activeTab: 'overview',
  experienceLevel: 'developer',
  selectedFile: null,
  selectedLine: null,
  selectedSymbol: null,

  setCurrentRepo: (repo) => set({ currentRepo: repo }),
  setOverview: (overview) => set({ overview }),
  setActiveTab: (tab) => set({ activeTab: tab }),
  setExperienceLevel: (level) => set({ experienceLevel: level }),
  setSelectedFile: (file, line = null) => set({ selectedFile: file, selectedLine: line, activeTab: 'source' }),
  setSelectedSymbol: (symbol) => set({ selectedSymbol: symbol }),
}));
