import { useState, useEffect } from 'react'

const API_CACHE  = '/api/cache'
const API_HEALTH = '/health'

export default function PerformanceDashboard() {
  const [cacheStats,  setCacheStats]  = useState(null)
  const [cacheHealth, setCacheHealth] = useState(null)
  const [flushing,    setFlushing]    = useState(null)
  const [loading,     setLoading]     = useState(true)
  const [lastUpdate,  setLastUpdate]  = useState(null)

  const namespaces = ['metrics', 'prompts', 'search', 'users']

  useEffect(() => {
    loadStats()
    const iv = setInterval(loadStats, 15000)
    return () => clearInterval(iv)
  }, [])

  async function loadStats() {
    setLoading(true)
    try {
      const [stats, health] = await Promise.all([
        fetch(`${API_CACHE}/stats`).then(r => r.json()),
        fetch(`${API_CACHE}/health`).then(r => r.json()),
      ])
      setCacheStats(stats)
      setCacheHealth(health)
      setLastUpdate(new Date().toLocaleTimeString())
    } catch (e) {
      console.error('Perf dashboard error:', e)
    }
    setLoading(false)
  }

  async function flushNamespace(ns) {
    setFlushing(ns)
    try {
      const res = await fetch(`${API_CACHE}/flush/${ns}`, { method: 'DELETE' })
      const data = await res.json()
      alert(`Flushed ${data.keys_deleted} keys from namespace "${ns}"`)
      loadStats()
    } catch (e) {
      alert('Flush failed: ' + e.message)
    }
    setFlushing(null)
  }

  const statusColor = cacheHealth?.status === 'healthy' ? 'text-green-400' : 'text-red-400'
  const statusDot   = cacheHealth?.status === 'healthy' ? 'bg-green-400' : 'bg-red-400'

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            ⚡ Performance & Cache
          </h1>
          <p className="text-sm text-slate-400 mt-1">Sprint 54 — Redis Caching · Latency · GZip · Rate Limiting</p>
        </div>
        <div className="flex items-center gap-3">
          {lastUpdate && <span className="text-xs text-slate-600">Updated {lastUpdate}</span>}
          <button
            onClick={loadStats}
            className="px-4 py-2 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/30 text-indigo-400 text-sm transition-all"
          >
            ↻ Refresh
          </button>
        </div>
      </div>

      {/* Cache Status Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white/5 border border-white/10 rounded-xl p-5">
          <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Cache Status</p>
          <div className="flex items-center gap-2 mt-2">
            <div className={`w-2.5 h-2.5 rounded-full ${statusDot} ${cacheHealth?.status === 'healthy' ? 'animate-pulse' : ''}`} />
            <span className={`text-lg font-bold capitalize ${statusColor}`}>
              {cacheHealth?.status || '…'}
            </span>
          </div>
        </div>

        <div className="bg-white/5 border border-white/10 rounded-xl p-5">
          <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Total Redis Keys</p>
          <p className="text-3xl font-bold text-white mt-2">{cacheStats?.total_keys ?? '—'}</p>
        </div>

        <div className="bg-white/5 border border-white/10 rounded-xl p-5">
          <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Memory Used</p>
          <p className="text-3xl font-bold text-white mt-2">{cacheStats?.used_memory_human || '—'}</p>
          <p className="text-xs text-slate-500 mt-1">Peak: {cacheStats?.used_memory_peak_human || '—'}</p>
        </div>

        <div className="bg-white/5 border border-white/10 rounded-xl p-5">
          <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Max Memory</p>
          <p className="text-3xl font-bold text-white mt-2">
            {cacheStats?.maxmemory_human && cacheStats.maxmemory_human !== '0B' ? cacheStats.maxmemory_human : 'Unlimited'}
          </p>
        </div>
      </div>

      {/* Cache Namespaces */}
      <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-white/5">
          <h3 className="text-sm font-semibold text-white">Cache Namespaces</h3>
          <p className="text-xs text-slate-500 mt-0.5">Flush specific namespace caches or all at once</p>
        </div>
        <div className="divide-y divide-white/5">
          {[...namespaces, 'all'].map(ns => {
            const ttls = { metrics: '30s', prompts: '1h', search: '2m', users: '5m', all: 'varies' }
            const icons = { metrics: '📈', prompts: '📝', search: '🔍', users: '👤', all: '🗑️' }
            const isAll = ns === 'all'
            return (
              <div key={ns} className={`flex items-center gap-4 px-5 py-4 ${isAll ? 'bg-red-500/5' : ''}`}>
                <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center text-lg">
                  {icons[ns]}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-slate-200 capitalize">{ns === 'all' ? 'All Namespaces' : `${ns} cache`}</p>
                  <p className="text-xs text-slate-500">TTL: {ttls[ns]}</p>
                </div>
                <button
                  onClick={() => flushNamespace(ns)}
                  disabled={flushing === ns}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all
                    ${isAll
                      ? 'bg-red-500/15 border border-red-500/30 text-red-400 hover:bg-red-500/25'
                      : 'bg-white/5 border border-white/10 text-slate-400 hover:bg-white/10 hover:text-white'
                    }
                    ${flushing === ns ? 'opacity-50 cursor-wait' : ''}`}
                >
                  {flushing === ns ? 'Flushing…' : 'Flush'}
                </button>
              </div>
            )
          })}
        </div>
      </div>

      {/* Performance Features */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-5">
        <h3 className="text-sm font-semibold text-white mb-4">Active Performance Features</h3>
        <div className="grid md:grid-cols-2 gap-3">
          {[
            { label: 'GZip Compression',      desc: 'All responses > 1KB compressed',           status: true  },
            { label: 'Redis Distributed Cache', desc: 'Metrics, prompts, search, users cached',  status: true  },
            { label: 'Response Time Headers',  desc: 'X-Response-Time on all API responses',     status: true  },
            { label: 'Rate Limiting',          desc: 'FastAPI Limiter via Redis',                 status: true  },
            { label: 'Async Database Queries', desc: 'Non-blocking SQLAlchemy async',             status: true  },
            { label: 'Stream Responses',       desc: 'SSE streaming for chat completions',        status: true  },
          ].map(({ label, desc, status }) => (
            <div key={label} className="flex items-start gap-3 p-3 bg-white/3 rounded-lg">
              <div className={`mt-0.5 w-5 h-5 rounded-full flex items-center justify-center text-xs shrink-0
                ${status ? 'bg-green-500/20 text-green-400' : 'bg-slate-500/20 text-slate-500'}`}>
                {status ? '✓' : '○'}
              </div>
              <div>
                <p className="text-sm font-medium text-slate-200">{label}</p>
                <p className="text-xs text-slate-500 mt-0.5">{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
