import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import rehypeSanitize from 'rehype-sanitize'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import { getReport } from '../api'
import type { ReportData, AnalyzedPost } from '../types'

const PIE_COLORS = [
  '#3B82F6',
  '#10B981',
  '#F59E0B',
  '#EF4444',
  '#8B5CF6',
  '#EC4899',
  '#06B6D4',
  '#84CC16',
]

function isSafeUrl(url: string): boolean {
  try {
    const parsed = new URL(url)
    return ['https:', 'http:'].includes(parsed.protocol)
  } catch {
    return false
  }
}

export default function RunDetail() {
  const { runId } = useParams<{ runId: string }>()
  const [report, setReport] = useState<ReportData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'report' | 'posts' | 'stats'>(
    'report',
  )

  useEffect(() => {
    if (!runId) return

    const fetchReport = async () => {
      setLoading(true)
      setError(null)
      try {
        const data = await getReport(runId)
        setReport(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load report')
      } finally {
        setLoading(false)
      }
    }

    fetchReport()
  }, [runId])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-gray-500">Loading report...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-red-700">
          <h3 className="font-semibold mb-2">Error</h3>
          <p>{error}</p>
          <Link
            to="/"
            className="mt-4 inline-block text-blue-600 hover:underline"
          >
            Back to Home
          </Link>
        </div>
      </div>
    )
  }

  if (!report) return null

  const { run, analyzed_posts, big_fish, category_stats } = report

  // Use spread to avoid mutating the original array (immutability)
  const importanceData = [...analyzed_posts]
    .sort(
      (a, b) =>
        (b.analysis.adjusted_importance ?? b.analysis.importance) -
        (a.analysis.adjusted_importance ?? a.analysis.importance),
    )
    .slice(0, 10)
    .map((p) => ({
      author: p.author.slice(0, 15),
      importance: p.analysis.adjusted_importance ?? p.analysis.importance,
    }))

  return (
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">
              Run {run.id.slice(0, 8)}...
            </h2>
            <p className="text-gray-500 text-sm mt-1">
              Created: {new Date(run.created_at).toLocaleString()}
              {run.completed_at &&
                ` | Completed: ${new Date(run.completed_at).toLocaleString()}`}
            </p>
          </div>
          <span
            className={`px-3 py-1 rounded-full text-sm font-medium ${
              run.status === 'completed'
                ? 'bg-green-100 text-green-800'
                : run.status === 'failed'
                  ? 'bg-red-100 text-red-800'
                  : run.status === 'running'
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-yellow-100 text-yellow-800'
            }`}
          >
            {run.status}
          </span>
        </div>

        <div className="mt-3 flex flex-wrap gap-2">
          {run.keywords.map((kw) => (
            <span
              key={kw}
              className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-sm"
            >
              {kw}
            </span>
          ))}
        </div>

        {run.stats && (
          <div className="mt-4 grid grid-cols-2 sm:grid-cols-5 gap-3">
            {[
              { label: 'Searched', value: run.stats.total_searched },
              {
                label: 'Hard Filtered',
                value: run.stats.filtered_by_hard_rules,
              },
              { label: 'Deduped', value: run.stats.filtered_by_dedup },
              { label: 'AI Filtered', value: run.stats.filtered_by_ai },
              { label: 'Valid', value: run.stats.valid_count },
            ].map((stat) => (
              <div key={stat.label} className="bg-gray-50 rounded-lg p-3">
                <div className="text-xs text-gray-500">{stat.label}</div>
                <div className="text-xl font-bold text-gray-800">
                  {stat.value}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-6">
        {(
          [
            { key: 'report', label: 'Report' },
            { key: 'posts', label: `Posts (${analyzed_posts.length})` },
            { key: 'stats', label: 'Charts' },
          ] as const
        ).map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.key
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'report' && (
        <div className="bg-white rounded-lg shadow-md p-6">
          {run.report_markdown ? (
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown rehypePlugins={[rehypeSanitize]}>
                {run.report_markdown}
              </ReactMarkdown>
            </div>
          ) : (
            <p className="text-gray-500">No report available yet.</p>
          )}
        </div>
      )}

      {activeTab === 'posts' && (
        <div className="space-y-4">
          {big_fish.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">
                Big Fish ({big_fish.length})
              </h3>
              <div className="space-y-3">
                {big_fish.map((post) => (
                  <PostCard key={post.id} post={post} highlighted />
                ))}
              </div>
            </div>
          )}

          <h3 className="text-lg font-semibold text-gray-800 mb-3">
            All Posts ({analyzed_posts.length})
          </h3>
          <div className="space-y-3">
            {analyzed_posts.map((post) => (
              <PostCard key={post.id} post={post} />
            ))}
          </div>
          {analyzed_posts.length === 0 && (
            <p className="text-gray-500">No posts found.</p>
          )}
        </div>
      )}

      {activeTab === 'stats' && (
        <div className="space-y-6">
          {/* Category Pie Chart */}
          {category_stats.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">
                Category Distribution
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={category_stats}
                    dataKey="count"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label={({ name, percentage }) =>
                      `${name} (${percentage.toFixed(0)}%)`
                    }
                  >
                    {category_stats.map((_, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={PIE_COLORS[index % PIE_COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Importance Bar Chart */}
          {importanceData.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">
                Top 10 by Importance
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={importanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="author" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="importance" fill="#3B82F6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function PostCard({
  post,
  highlighted = false,
}: {
  post: AnalyzedPost
  highlighted?: boolean
}) {
  const { analysis } = post
  const importance = analysis.adjusted_importance ?? analysis.importance

  return (
    <div
      className={`bg-white rounded-lg shadow-sm border p-4 ${
        highlighted ? 'border-amber-300 bg-amber-50' : 'border-gray-200'
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-medium text-gray-800">{post.author}</span>
            {post.keyword && (
              <span className="px-1.5 py-0.5 bg-blue-50 text-blue-600 rounded text-xs">
                {post.keyword}
              </span>
            )}
          </div>
          <p className="text-gray-600 text-sm line-clamp-3">{post.content}</p>
          <p className="text-gray-500 text-xs mt-1">{analysis.summary}</p>
        </div>
        <div className="ml-4 text-right shrink-0">
          <div
            className={`text-lg font-bold ${
              importance >= 8
                ? 'text-red-600'
                : importance >= 5
                  ? 'text-amber-600'
                  : 'text-gray-600'
            }`}
          >
            {importance}
          </div>
          <div className="text-xs text-gray-400">importance</div>
        </div>
      </div>

      <div className="mt-2 flex flex-wrap gap-1">
        {analysis.categories.map((cat) => (
          <span
            key={cat}
            className="px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded text-xs"
          >
            {cat}
          </span>
        ))}
      </div>

      {post.link && isSafeUrl(post.link) && (
        <a
          href={post.link}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-2 inline-block text-xs text-blue-500 hover:underline"
        >
          View on Threads
        </a>
      )}
    </div>
  )
}
