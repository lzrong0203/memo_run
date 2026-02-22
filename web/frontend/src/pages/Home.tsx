import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMonitor } from '../hooks/useMonitor'

export default function Home() {
  const [keywordInput, setKeywordInput] = useState('')
  const { status, runId, progress, error, start, reset } = useMonitor()
  const navigate = useNavigate()
  const progressRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (progressRef.current) {
      progressRef.current.scrollTop = progressRef.current.scrollHeight
    }
  }, [progress])

  const handleStart = async () => {
    const keywords = keywordInput
      .split(',')
      .map((k) => k.trim())
      .filter((k) => k.length > 0)

    if (keywords.length === 0) return
    await start(keywords)
  }

  const handleViewReport = () => {
    if (runId) {
      navigate(`/run/${runId}`)
    }
  }

  const isRunning = status === 'connecting' || status === 'running'

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">
          Start Monitoring
        </h2>
        <p className="text-gray-600 mb-6">
          Enter keywords separated by commas to monitor Threads posts.
        </p>

        <div className="space-y-4">
          <div>
            <label
              htmlFor="keywords"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Keywords
            </label>
            <input
              id="keywords"
              type="text"
              value={keywordInput}
              onChange={(e) => setKeywordInput(e.target.value)}
              placeholder="e.g. AI, blockchain, startup"
              disabled={isRunning}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !isRunning) handleStart()
              }}
            />
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleStart}
              disabled={isRunning || keywordInput.trim().length === 0}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {isRunning ? 'Running...' : 'Start Monitor'}
            </button>

            {status !== 'idle' && (
              <button
                onClick={reset}
                className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Reset
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Progress Panel */}
      {status !== 'idle' && (
        <div className="mt-6 bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-800">Progress</h3>
            <span
              className={`px-3 py-1 rounded-full text-sm font-medium ${
                status === 'completed'
                  ? 'bg-green-100 text-green-800'
                  : status === 'failed'
                    ? 'bg-red-100 text-red-800'
                    : status === 'running'
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-yellow-100 text-yellow-800'
              }`}
            >
              {status}
            </span>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          <div ref={progressRef} className="space-y-2 max-h-64 overflow-y-auto">
            {progress.map((msg, i) => (
              <div
                key={i}
                className={`p-2 rounded text-sm ${
                  msg.type === 'error'
                    ? 'bg-red-50 text-red-700'
                    : msg.type === 'completed'
                      ? 'bg-green-50 text-green-700'
                      : 'bg-gray-50 text-gray-700'
                }`}
              >
                <span className="font-mono text-xs text-gray-400 mr-2">
                  [{msg.type}]
                </span>
                {JSON.stringify(msg.data)}
              </div>
            ))}
            {progress.length === 0 && isRunning && (
              <div className="text-gray-400 text-sm">
                Waiting for progress updates...
              </div>
            )}
          </div>

          {status === 'completed' && runId && (
            <div className="mt-4">
              <button
                onClick={handleViewReport}
                className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                View Report
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
