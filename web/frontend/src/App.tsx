import { Routes, Route, Link, useLocation } from 'react-router-dom'
import Home from './pages/Home'
import RunDetail from './pages/RunDetail'
import History from './pages/History'

function NavLink({
  to,
  children,
}: {
  to: string
  children: React.ReactNode
}) {
  const location = useLocation()
  const isActive = location.pathname === to

  return (
    <Link
      to={to}
      className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
        isActive
          ? 'bg-gray-900 text-white'
          : 'text-gray-300 hover:bg-gray-700 hover:text-white'
      }`}
    >
      {children}
    </Link>
  )
}

export default function App() {
  return (
    <div className="min-h-screen bg-gray-100">
      {/* Navigation */}
      <nav className="bg-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="text-white font-bold text-lg">
                Threads Monitor
              </Link>
              <div className="ml-10 flex items-baseline space-x-4">
                <NavLink to="/">Monitor</NavLink>
                <NavLink to="/history">History</NavLink>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/run/:runId" element={<RunDetail />} />
          <Route path="/history" element={<History />} />
        </Routes>
      </main>
    </div>
  )
}
