export type RunStatus = 'pending' | 'running' | 'completed' | 'failed'

export interface RunRecord {
  id: string
  status: RunStatus
  keywords: string[]
  created_at: string
  completed_at: string | null
  report_markdown: string | null
  stats: PipelineStats | null
  error_message: string | null
}

export interface PipelineStats {
  total_searched: number
  filtered_by_hard_rules: number
  filtered_by_dedup: number
  filtered_by_ai: number
  valid_count: number
}

export interface AnalyzedPost {
  id: string
  content: string
  author: string
  link: string
  timestamp: string
  keyword?: string
  analysis: PostAnalysis
}

export interface PostAnalysis {
  categories: string[]
  importance: number
  adjusted_importance?: number
  summary: string
  reasoning?: string
  entities?: {
    persons: string[]
    locations: string[]
    organizations: string[]
    events: string[]
  }
  bonus_detail?: Array<{ rule_name: string; bonus: number }>
}

export interface CategoryStat {
  name: string
  count: number
  percentage: number
}

export interface ProgressMessage {
  type: 'status' | 'keyword_progress' | 'pipeline_stats' | 'completed' | 'error'
  data: Record<string, unknown>
}

export interface ReportData {
  run: RunRecord
  analyzed_posts: AnalyzedPost[]
  big_fish: AnalyzedPost[]
  category_stats: CategoryStat[]
}
