export interface Repository {
  id: string;
  url: string;
  owner: string;
  name: string;
  description?: string;
  default_branch: string;
  stars: number;
  primary_language?: string;
  created_at: string;
  updated_at: string;
}

export interface RepositoryOverview {
  repository_id: string;
  snapshot_id: string;
  name: string;
  owner: string;
  description?: string;
  commit_sha: string;
  branch: string;
  primary_language?: string;
  languages: Record<string, number>;
  total_files: number;
  total_lines: number;
  problem_solved: string;
  frameworks: string[];
  entry_points: string[];
  important_directories: Array<{ path: string; role: string }>;
  core_components: Array<{ name: string; file: string; purpose: string }>;
  local_run_commands: string[];
  test_commands: string[];
  architecture_summary: string;
}

export interface GraphNode {
  id: string;
  entity_type: string;
  label: string;
  qualified_name: string;
  file_path?: string;
  level: number;
  metadata?: Record<string, any>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  edge_type: string;
  evidence?: string;
  confidence: string;
  source_line?: number;
}

export interface ArchitectureGraphResponse {
  snapshot_id: string;
  level: number;
  nodes: GraphNode[];
  edges: GraphEdge[];
  total_nodes: number;
  total_edges: number;
}

export interface ArchitectureAnalytics {
  snapshot_id: string;
  total_modules: number;
  total_dependencies: number;
  dependency_cycles: string[][];
  strongly_connected_components: string[][];
  top_central_modules: Array<{
    node_id: string;
    label: string;
    centrality_score: number;
    entity_type: string;
  }>;
  fan_in_hotspots: Array<{
    node_id: string;
    label: string;
    fan_in: number;
    description: string;
  }>;
  fan_out_hotspots: Array<{
    node_id: string;
    label: string;
    fan_out: number;
    description: string;
  }>;
  instability_scores: Record<string, number>;
  summary_verdict: string;
}

export interface LearningStep {
  step_id: number;
  title: string;
  summary: string;
  detailed_explanation: string;
  key_takeaways: string[];
  citations: Array<{
    file_path: string;
    start_line: number;
    end_line: number;
    symbol?: string;
  }>;
  suggested_files: string[];
  difficulty: string;
  comprehension_check?: {
    question: string;
    options: string[];
    correct: string;
  };
}

export interface AdaptiveExplanation {
  experience_level: 'beginner' | 'developer' | 'senior';
  overview: string;
  mental_model: string;
  architecture_breakdown: Array<{ component: string; what_it_does: string }>;
  steps: LearningStep[];
  tradeoffs_and_patterns?: string[];
  common_pitfalls?: string[];
}

export interface CodeFlowNode {
  id: string;
  symbol_name: string;
  qualified_name: string;
  kind: string;
  file_path: string;
  start_line: number;
  end_line: number;
  snippet?: string;
  step_order: number;
  confidence: string;
}

export interface CodeFlowResponse {
  entry_point_id: string;
  entry_symbol: string;
  entry_file: string;
  nodes: CodeFlowNode[];
  call_edges: Array<{
    source: string;
    target: string;
    evidence: string;
    confidence: string;
  }>;
  narrative: string;
}

export interface Citation {
  file_path: string;
  start_line: number;
  end_line: number;
  symbol_name?: string;
  commit_sha: string;
  snippet?: string;
}

export interface QuestionResponse {
  answer: string;
  experience_level: string;
  citations: Citation[];
  retrieved_symbols: string[];
  mode_used: string;
}

export interface CommitSummary {
  sha: string;
  short_sha: string;
  message: string;
  author: string;
  date: string;
  is_analyzed: boolean;
}

export interface ArchitectureDiff {
  base_commit: string;
  target_commit: string;
  added_nodes: Array<{ id: string; label: string; type: string }>;
  removed_nodes: Array<{ id: string; label: string; type: string }>;
  added_dependencies: Array<{ source: string; target: string; type: string }>;
  removed_dependencies: Array<{ source: string; target: string; type: string }>;
  cycle_delta: number;
  coupling_delta: number;
  structural_summary: string;
}

export interface SimulationResponse {
  snapshot_id: string;
  original_cycles_count: number;
  simulated_cycles_count: number;
  original_coupling: number;
  simulated_coupling: number;
  impact_summary: string;
  affected_nodes: string[];
  cycle_changes: Record<string, any>;
}

export interface Bookmark {
  id: string;
  repository_id: string;
  title: string;
  file_path?: string;
  line_number?: number;
  symbol_name?: string;
  notes?: string;
  created_at: string;
}
