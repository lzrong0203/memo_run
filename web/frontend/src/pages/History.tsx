import { Link } from 'react-router-dom'
import { useHistory } from '../hooks/useHistory'

const ITEMS_PER_PAGE = 20

export default function History() {
  const { runs, total, page, loading, error, fetchPage } = useHistory()
  const totalPages = Math.ceil(total / ITEMS_PER_PAGE)

  if (loading && runs.length === 0) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-gray-500">Loading history...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-red-700">
          <h3 className="font-semibold mb-2">Error</h3>
          <p>{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Run History</h2>

      {runs.length === 0 ? (
        <div className="bg-white rounded-lg shadow-md p-8 text-center text-gray-500">
          No runs yet. Start a monitor from the{' '}
          <Link to="/" className="text-blue-600 hover:underline">
            home page
          </Link>
          .
        </div>
      ) : (
        <>
          <div className="bg-white rounded-lg shadow-md overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Run ID
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Keywords
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Posts
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {runs.map((run) => (
                  <tr key={run.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <Link
                        to={`/run/${run.id}`}
                        className="text-blue-600 hover:underline font-mono text-sm"
                      >
                        {run.id.slice(0, 8)}...
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${
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
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {run.keywords.slice(0, 3).map((kw) => (
                          <span
                            key={kw}
                            className="px-1.5 py-0.5 bg-blue-50 text-blue-700 rounded text-xs"
                          >
                            {kw}
                          </span>
                        ))}
                        {run.keywords.length > 3 && (
                          <span className="text-xs text-gray-400">
                            +{run.keywords.length - 3}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {run.stats?.valid_count ?? '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {new Date(run.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-4 flex items-center justify-between">
              <div className="text-sm text-gray-500">
                Page {page} of {totalPages} ({total} total runs)
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => fetchPage(page - 1)}
                  disabled={page <= 1 || loading}
                  className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <button
                  onClick={() => fetchPage(page + 1)}
                  disabled={page >= totalPages || loading}
                  className="px-3 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
