import {
  Repository,
  RepositoryOverview,
  ArchitectureGraphResponse,
  ArchitectureAnalytics,
  CodeFlowResponse,
  AdaptiveExplanation,
  QuestionResponse,
  CommitSummary,
  ArchitectureDiff,
  SimulationResponse,
  Bookmark
} from '../types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Request failed with status ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Repositories
  analyzeRepository: (url: string, branch?: string, commit_sha?: string) =>
    fetchJson<{ job_id: string; repository_id: string; status: string; progress_percentage: number; current_step: string }>(
      '/api/v1/repositories/analyze',
      { method: 'POST', body: JSON.stringify({ url, branch, commit_sha }) }
    ),

  getRepositories: () => fetchJson<Repository[]>('/api/v1/repositories'),

  getRepository: (repoId: string) => fetchJson<Repository>(`/api/v1/repositories/${repoId}`),

  getRepositoryStatus: (repoId: string) =>
    fetchJson<{ job_id: string; status: string; progress_percentage: number; current_step: string; snapshot_id?: string }>(
      `/api/v1/repositories/${repoId}/status`
    ),

  getRepositoryOverview: (repoId: string) =>
    fetchJson<RepositoryOverview>(`/api/v1/repositories/${repoId}/overview`),

  getRepositoryFiles: (repoId: string) =>
    fetchJson<Array<{ path: string; language: string; category: string; loc: number; size_bytes: number }>>(
      `/api/v1/repositories/${repoId}/files`
    ),

  // Architecture Graph
  getArchitectureGraph: (repoId: string, level: number = 2) =>
    fetchJson<ArchitectureGraphResponse>(`/api/v1/repositories/${repoId}/architecture?level=${level}`),

  getArchitectureAnalytics: (repoId: string) =>
    fetchJson<ArchitectureAnalytics>(`/api/v1/repositories/${repoId}/analytics`),

  runSimulation: (repoId: string, mutations: Array<{ action: string; source_node: string; target_node?: string }>) =>
    fetchJson<SimulationResponse>(`/api/v1/repositories/${repoId}/simulations`, {
      method: 'POST',
      body: JSON.stringify({ mutations }),
    }),

  // Symbols & Code Flow
  getSymbols: (repoId: string, filePath?: string) =>
    fetchJson<any[]>(`/api/v1/repositories/${repoId}/symbols${filePath ? `?file_path=${encodeURIComponent(filePath)}` : ''}`),

  getCodeFlowTrace: (repoId: string, entry?: string) =>
    fetchJson<CodeFlowResponse>(`/api/v1/repositories/${repoId}/codeflow${entry ? `?entry=${encodeURIComponent(entry)}` : ''}`),

  // Adaptive Learning
  getAdaptiveLearning: (repoId: string, level: 'beginner' | 'developer' | 'senior') =>
    fetchJson<AdaptiveExplanation>(`/api/v1/repositories/${repoId}/learning?level=${level}`),

  // Ask Repository
  askQuestion: (repoId: string, question: string, level: string) =>
    fetchJson<QuestionResponse>(`/api/v1/repositories/${repoId}/questions`, {
      method: 'POST',
      body: JSON.stringify({ question, experience_level: level }),
    }),

  // Git Time Machine
  getRepositoryHistory: (repoId: string) =>
    fetchJson<{ repository_id: string; commits: CommitSummary[]; total_commits: number }>(`/api/v1/repositories/${repoId}/history`),

  getArchitectureDiff: (repoId: string, base: string, target: string) =>
    fetchJson<ArchitectureDiff>(`/api/v1/repositories/${repoId}/diff?base=${base}&target=${target}`),

  // Bookmarks
  getBookmarks: (repoId: string) => fetchJson<Bookmark[]>(`/api/v1/repositories/${repoId}/bookmarks`),

  createBookmark: (repoId: string, data: { title: string; file_path?: string; line_number?: number; symbol_name?: string; notes?: string }) =>
    fetchJson<Bookmark>(`/api/v1/repositories/${repoId}/bookmarks`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  deleteBookmark: (repoId: string, bookmarkId: string) =>
    fetchJson<{ status: string; id: string }>(`/api/v1/repositories/${repoId}/bookmarks/${bookmarkId}`, {
      method: 'DELETE',
    }),
};
