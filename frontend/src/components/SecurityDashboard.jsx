import { useState, useEffect } from 'react'

const API = '/api/security'

function StatCard({ label, value, sub, color = 'indigo' }) {
  const colors = {
    indigo: 'from-indigo-600/20 to-indigo-500/10 border-indigo-500/20 text-indigo-400',
    green:  'from-green-600/20  to-green-500/10  border-green-500/20  text-green-400',
    red:    'from-red-600/20    to-red-500/10    border-red-500/20    text-red-400',
    yellow: 'from-yellow-600/20 to-yellow-500/10 border-yellow-500/20 text-yellow-400',
    slate:  'from-slate-600/20  to-slate-500/10  border-slate-500/20  text-slate-400',
  }
  return (
    <div className={`bg-gradient-to-br ${colors[color]} border rounded-xl p-5`}>
      <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">{label}</p>
      <p className="text-3xl font-bold text-white">{value}</p>
      {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
    </div>
  )
}

function Badge({ ok, label }) {
  return ok
    ? <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-green-500/15 border border-green-500/30 text-green-400 text-xs font-medium">✔ {label}</span>
    : <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-red-500/15 border border-red-500/30 text-red-400 text-xs font-medium">✘ {label}</span>
}

export default function SecurityDashboard() {
  const [report,   setReport]   = useState(null)
  const [auditLog, setAuditLog] = useState([])
  const [secrets,  setSecrets]  = useState([])
  const [sso,      setSso]      = useState(null)
  const [integrity, setIntegrity] = useState(null)
  const [loading,  setLoading]  = useState(true)
  const [tab,      setTab]      = useState('overview')

  useEffect(() => {
    loadAll()
  }, [])

  async function loadAll() {
    setLoading(true)
    try {
      const [rep, log, sec, ssoConf, integ] = await Promise.all([
        fetch(`${API}/compliance/report?period_days=30`).then(r => r.json()),
        fetch(`${API}/audit?limit=50`).then(r => r.json()),
        fetch(`${API}/secrets/status`).then(r => r.json()),
        fetch(`${API}/sso/config`).then(r => r.json()),
        fetch(`${API}/audit/verify?sample_size=200`).then(r => r.json()),
      ])
      setReport(rep)
      setAuditLog(Array.isArray(log) ? log : [])
      setSecrets(sec.secrets || [])
      setSso(ssoConf)
      setIntegrity(integ)
    } catch (e) {
      console.error('Security dashboard error:', e)
    }
    setLoading(false)
  }

  const tabs = ['overview', 'audit', 'sso', 'secrets']

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 rounded-full border-2 border-indigo-500/30 border-t-indigo-500 animate-spin" />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            🔐 Enterprise Security
          </h1>
          <p className="text-sm text-slate-400 mt-1">Sprint 55 — Audit Logs · SSO · Secrets · Compliance</p>
        </div>
        <button
          onClick={loadAll}
          className="px-4 py-2 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/30 text-indigo-400 text-sm transition-all"
        >
          ↻ Refresh
        </button>
      </div>

      {/* Compliance Warnings */}
      {report?.warnings?.length > 0 && (
        <div className="rounded-xl border border-yellow-500/20 bg-yellow-500/5 p-4 space-y-1">
          <p className="text-yellow-400 text-sm font-semibold mb-2">⚠ Compliance Warnings</p>
          {report.warnings.map((w, i) => (
            <p key={i} className="text-xs text-yellow-300/80">• {w}</p>
          ))}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 bg-white/5 p-1 rounded-xl w-fit">
        {tabs.map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-all duration-200
              ${tab === t
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/25'
                : 'text-slate-400 hover:text-white'}`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {tab === 'overview' && report && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Audit Events (30d)" value={report.total_events} color="indigo" />
            <StatCard
              label="Failed / Denied"
              value={report.failed_events}
              color={report.failed_events > 20 ? 'red' : 'green'}
            />
            <StatCard
              label="Audit Integrity"
              value={report.audit_integrity_ok ? '✔ Pass' : '✘ Fail'}
              color={report.audit_integrity_ok ? 'green' : 'red'}
            />
            <StatCard
              label="Secrets Configured"
              value={`${report.secrets_configured.length} / ${secrets.length}`}
              color="slate"
            />
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* By Action */}
            <div className="bg-white/5 border border-white/10 rounded-xl p-5">
              <h3 className="text-sm font-semibold text-white mb-4">Events by Action</h3>
              <div className="space-y-2">
                {Object.entries(report.by_action).sort((a, b) => b[1] - a[1]).map(([action, count]) => {
                  const pct = report.total_events > 0 ? (count / report.total_events) * 100 : 0
                  return (
                    <div key={action}>
                      <div className="flex justify-between text-xs text-slate-400 mb-1">
                        <span className="font-mono">{action}</span>
                        <span>{count}</span>
                      </div>
                      <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                        <div className="h-full rounded-full bg-indigo-500" style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  )
                })}
                {Object.keys(report.by_action).length === 0 && (
                  <p className="text-xs text-slate-500">No events recorded yet.</p>
                )}
              </div>
            </div>

            {/* By Outcome */}
            <div className="bg-white/5 border border-white/10 rounded-xl p-5">
              <h3 className="text-sm font-semibold text-white mb-4">Events by Outcome</h3>
              <div className="space-y-3">
                {Object.entries(report.by_outcome).map(([outcome, count]) => {
                  const color = outcome === 'success' ? 'bg-green-500' : outcome === 'failure' ? 'bg-red-500' : 'bg-yellow-500'
                  const pct = report.total_events > 0 ? (count / report.total_events) * 100 : 0
                  return (
                    <div key={outcome}>
                      <div className="flex justify-between text-xs text-slate-400 mb-1">
                        <span className="capitalize">{outcome}</span>
                        <span>{count} ({pct.toFixed(1)}%)</span>
                      </div>
                      <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  )
                })}
                {Object.keys(report.by_outcome).length === 0 && (
                  <p className="text-xs text-slate-500">No events recorded yet.</p>
                )}
              </div>
            </div>
          </div>

          {/* Integrity card */}
          {integrity && (
            <div className="bg-white/5 border border-white/10 rounded-xl p-5 flex items-center gap-4">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-2xl
                ${integrity.integrity_ok ? 'bg-green-500/15' : 'bg-red-500/15'}`}>
                {integrity.integrity_ok ? '🔒' : '⚠️'}
              </div>
              <div>
                <p className="text-sm font-semibold text-white">
                  Audit HMAC Integrity — {integrity.integrity_ok ? 'All Clean' : 'Tamper Detected!'}
                </p>
                <p className="text-xs text-slate-400 mt-0.5">
                  Checked {integrity.checked} events · {integrity.tampered} failed signature verification
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Audit Log Tab */}
      {tab === 'audit' && (
        <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-white/5 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Audit Log (Last 50 Events)</h3>
            <span className="text-xs text-slate-500">{auditLog.length} events</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-white/5">
                  {['Timestamp', 'User', 'Action', 'Resource', 'Outcome', 'IP'].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-slate-500 font-medium uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {auditLog.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-slate-500">
                      No audit events yet. They will appear here as users interact with the system.
                    </td>
                  </tr>
                ) : (
                  auditLog.map((e, i) => {
                    const outcomeColor = e.outcome === 'success'
                      ? 'text-green-400' : e.outcome === 'failure'
                      ? 'text-red-400' : 'text-yellow-400'
                    return (
                      <tr key={i} className="hover:bg-white/3 transition-colors">
                        <td className="px-4 py-3 text-slate-500 font-mono whitespace-nowrap">
                          {new Date(e.timestamp).toLocaleString()}
                        </td>
                        <td className="px-4 py-3 text-slate-300 font-mono">{e.user_id}</td>
                        <td className="px-4 py-3 text-indigo-400 font-medium">{e.action}</td>
                        <td className="px-4 py-3 text-slate-400">{e.resource}</td>
                        <td className={`px-4 py-3 font-medium ${outcomeColor}`}>{e.outcome}</td>
                        <td className="px-4 py-3 text-slate-500 font-mono">{e.ip_address || '—'}</td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* SSO Tab */}
      {tab === 'sso' && sso && (
        <div className="space-y-4">
          <div className="bg-white/5 border border-white/10 rounded-xl p-6 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/15 flex items-center justify-center text-lg">🔑</div>
              <div>
                <h3 className="text-sm font-semibold text-white">SSO / OIDC Configuration</h3>
                <p className="text-xs text-slate-500">Azure Entra ID · Google · Okta · Generic OIDC</p>
              </div>
              <div className="ml-auto">
                <Badge ok={sso.enabled} label={sso.enabled ? 'Enabled' : 'Disabled'} />
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-4 pt-2">
              {[
                { label: 'Provider',     value: sso.provider || '—' },
                { label: 'Client ID',    value: sso.client_id ? `${sso.client_id.slice(0,8)}…` : 'Not set' },
                { label: 'Tenant ID',    value: sso.tenant_id || '—' },
                { label: 'OIDC Issuer',  value: sso.oidc_issuer || (sso.tenant_id ? `Auto (${sso.tenant_id})` : '—') },
                { label: 'Redirect URI', value: sso.redirect_uri || '—' },
                { label: 'Scopes',       value: (sso.scopes || []).join(', ') },
              ].map(({ label, value }) => (
                <div key={label} className="bg-white/5 rounded-lg p-3">
                  <p className="text-xs text-slate-500 mb-0.5">{label}</p>
                  <p className="text-sm text-slate-200 font-mono break-all">{value}</p>
                </div>
              ))}
            </div>

            {sso.enabled && (
              <button
                onClick={() => fetch(`${API}/sso/login-url`).then(r => r.json()).then(d => window.open(d.login_url, '_blank'))}
                className="mt-4 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm transition-all"
              >
                Test SSO Login →
              </button>
            )}

            {!sso.enabled && (
              <p className="text-xs text-slate-500 bg-white/5 rounded-lg p-3 mt-2">
                To enable SSO, set <code className="text-indigo-400">AZURE_AD_CLIENT_ID</code>, <code className="text-indigo-400">AZURE_AD_TENANT_ID</code>, and <code className="text-indigo-400">AZURE_AD_REDIRECT_URI</code> in your <code>.env</code> file, then restart the backend.
              </p>
            )}
          </div>
        </div>
      )}

      {/* Secrets Tab */}
      {tab === 'secrets' && (
        <div className="space-y-4">
          <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden">
            <div className="px-5 py-4 border-b border-white/5">
              <h3 className="text-sm font-semibold text-white">Secrets & Credentials Status</h3>
              <p className="text-xs text-slate-500 mt-0.5">Values are masked. Source priority: Azure Key Vault → Environment Variables</p>
            </div>
            <div className="divide-y divide-white/5">
              {secrets.map(s => (
                <div key={s.name} className="flex items-center gap-4 px-5 py-3.5">
                  <div className={`w-2 h-2 rounded-full ${s.configured ? 'bg-green-400' : 'bg-red-400'}`} />
                  <div className="flex-1">
                    <p className="text-sm font-mono text-slate-200">{s.name}</p>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {s.configured ? s.masked_value : 'Not configured'}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full border ${
                      s.source === 'vault'   ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-400' :
                      s.source === 'env'     ? 'bg-slate-500/10 border-slate-500/30 text-slate-400' :
                                               'bg-red-500/10 border-red-500/30 text-red-400'
                    }`}>
                      {s.source}
                    </span>
                    <Badge ok={s.configured} label={s.configured ? 'Set' : 'Missing'} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
