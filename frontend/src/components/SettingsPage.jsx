import { useState, useEffect } from 'react'

const API_NOTIF = '/api/notifications/settings'

function Section({ title, children }) {
  return (
    <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-white/5">
        <h3 className="text-sm font-semibold text-white">{title}</h3>
      </div>
      <div className="p-5 space-y-4">{children}</div>
    </div>
  )
}

function Toggle({ label, desc, checked, onChange }) {
  return (
    <div className="flex items-start justify-between gap-4">
      <div>
        <p className="text-sm font-medium text-slate-200">{label}</p>
        {desc && <p className="text-xs text-slate-500 mt-0.5">{desc}</p>}
      </div>
      <button
        onClick={() => onChange(!checked)}
        className={`shrink-0 w-11 h-6 rounded-full transition-all duration-200 relative
          ${checked ? 'bg-indigo-500' : 'bg-white/10'}`}
      >
        <span className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow-sm transition-all duration-200
          ${checked ? 'left-5.5' : 'left-0.5'}`}
          style={{ left: checked ? '22px' : '2px' }}
        />
      </button>
    </div>
  )
}

function Input({ label, value, onChange, placeholder, type = 'text', readonly = false }) {
  return (
    <div>
      <label className="text-xs font-medium text-slate-400 mb-1.5 block">{label}</label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        readOnly={readonly}
        className={`w-full px-3 py-2 rounded-lg text-sm text-slate-200 border transition-all
          bg-white/5 border-white/10 focus:border-indigo-500/50 focus:outline-none focus:ring-1 focus:ring-indigo-500/25
          ${readonly ? 'opacity-60 cursor-not-allowed' : ''}`}
      />
    </div>
  )
}

export default function SettingsPage() {
  const [tab, setTab] = useState('profile')
  const [saved, setSaved] = useState(false)

  // Profile state
  const [displayName, setDisplayName] = useState('Admin User')
  const [email, setEmail]   = useState('admin@athena.ai')
  const [timezone, setTimezone] = useState('UTC')

  // Notifications state
  const [notifSettings, setNotifSettings] = useState({
    slack_webhook_url: '',
    email_enabled: false,
    smtp_host: '',
    smtp_port: 587,
    smtp_user: '',
    smtp_password: '',
    from_email: '',
  })

  // Appearance
  const [density, setDensity]     = useState('comfortable')
  const [animations, setAnimations] = useState(true)

  useEffect(() => {
    fetch(API_NOTIF)
      .then(r => r.json())
      .then(d => setNotifSettings(d))
      .catch(() => {})
  }, [])

  function showSaved() {
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  async function saveNotifications() {
    try {
      await fetch(API_NOTIF, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(notifSettings),
      })
      showSaved()
    } catch (e) {
      alert('Save failed: ' + e.message)
    }
  }

  const tabs = [
    { id: 'profile',      label: 'Profile',       icon: '👤' },
    { id: 'notifications',label: 'Notifications',  icon: '🔔' },
    { id: 'appearance',   label: 'Appearance',     icon: '🎨' },
    { id: 'api',          label: 'API & Keys',     icon: '🔑' },
  ]

  return (
    <div className="p-6 space-y-6 max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">⚙️ Settings</h1>
          <p className="text-sm text-slate-400 mt-1">Configure your Athena AI workspace</p>
        </div>
        {saved && (
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-green-500/15 border border-green-500/30 text-green-400 text-sm animate-fade-in">
            ✔ Saved
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-white/5 p-1 rounded-xl w-fit">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-2
              ${tab === t.id
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/25'
                : 'text-slate-400 hover:text-white'}`}
          >
            <span>{t.icon}</span>
            {t.label}
          </button>
        ))}
      </div>

      {/* Profile Tab */}
      {tab === 'profile' && (
        <div className="space-y-4">
          <Section title="Account Information">
            <div className="flex items-center gap-4 pb-4 border-b border-white/5">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center text-2xl font-bold text-white">
                {displayName.charAt(0)}
              </div>
              <div>
                <p className="text-base font-semibold text-white">{displayName}</p>
                <p className="text-sm text-slate-400">{email}</p>
                <span className="mt-1 inline-flex items-center px-2 py-0.5 rounded-full bg-indigo-500/15 border border-indigo-500/30 text-indigo-400 text-xs">
                  System Administrator
                </span>
              </div>
            </div>
            <Input label="Display Name" value={displayName} onChange={setDisplayName} placeholder="Your name" />
            <Input label="Email Address" value={email} onChange={setEmail} placeholder="you@company.com" type="email" />
            <div>
              <label className="text-xs font-medium text-slate-400 mb-1.5 block">Timezone</label>
              <select
                value={timezone}
                onChange={e => setTimezone(e.target.value)}
                className="w-full px-3 py-2 rounded-lg text-sm text-slate-200 bg-white/5 border border-white/10 focus:border-indigo-500/50 focus:outline-none"
              >
                {['UTC', 'America/New_York', 'America/Los_Angeles', 'Europe/London', 'Asia/Kolkata', 'Asia/Tokyo'].map(tz => (
                  <option key={tz} value={tz} className="bg-slate-900">{tz}</option>
                ))}
              </select>
            </div>
            <button
              onClick={showSaved}
              className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm transition-all"
            >
              Save Profile
            </button>
          </Section>

          <Section title="Password">
            <Input label="Current Password" value="" onChange={() => {}} placeholder="••••••••" type="password" />
            <Input label="New Password" value="" onChange={() => {}} placeholder="••••••••" type="password" />
            <Input label="Confirm New Password" value="" onChange={() => {}} placeholder="••••••••" type="password" />
            <button className="px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 text-sm transition-all">
              Update Password
            </button>
          </Section>
        </div>
      )}

      {/* Notifications Tab */}
      {tab === 'notifications' && (
        <div className="space-y-4">
          <Section title="Slack Notifications">
            <p className="text-xs text-slate-500">Send system notifications to a Slack channel via Incoming Webhook.</p>
            <Input
              label="Slack Webhook URL"
              value={notifSettings.slack_webhook_url || ''}
              onChange={v => setNotifSettings(s => ({ ...s, slack_webhook_url: v }))}
              placeholder="https://hooks.slack.com/services/T.../B.../..."
            />
            {notifSettings.slack_webhook_url && (
              <button
                onClick={async () => {
                  await fetch('/api/notifications/send-slack', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ webhook_url: notifSettings.slack_webhook_url, message: 'Athena AI test notification ✅', title: 'Test' }),
                  })
                  alert('Test notification sent to Slack!')
                }}
                className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
              >
                Send test notification →
              </button>
            )}
          </Section>

          <Section title="Email (SMTP)">
            <Toggle
              label="Enable Email Notifications"
              desc="Requires SMTP configuration below"
              checked={notifSettings.email_enabled}
              onChange={v => setNotifSettings(s => ({ ...s, email_enabled: v }))}
            />
            {notifSettings.email_enabled && (
              <>
                <Input label="SMTP Host" value={notifSettings.smtp_host || ''} onChange={v => setNotifSettings(s => ({ ...s, smtp_host: v }))} placeholder="smtp.gmail.com" />
                <Input label="SMTP Port" value={String(notifSettings.smtp_port || 587)} onChange={v => setNotifSettings(s => ({ ...s, smtp_port: parseInt(v) }))} placeholder="587" />
                <Input label="SMTP Username" value={notifSettings.smtp_user || ''} onChange={v => setNotifSettings(s => ({ ...s, smtp_user: v }))} placeholder="user@company.com" />
                <Input label="SMTP Password" value={notifSettings.smtp_password || ''} onChange={v => setNotifSettings(s => ({ ...s, smtp_password: v }))} placeholder="••••••••" type="password" />
                <Input label="From Email" value={notifSettings.from_email || ''} onChange={v => setNotifSettings(s => ({ ...s, from_email: v }))} placeholder="noreply@athena.ai" />
              </>
            )}
          </Section>

          <button
            onClick={saveNotifications}
            className="px-6 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-all shadow-lg shadow-indigo-500/25"
          >
            Save Notification Settings
          </button>
        </div>
      )}

      {/* Appearance Tab */}
      {tab === 'appearance' && (
        <div className="space-y-4">
          <Section title="Display">
            <Toggle
              label="Smooth Animations"
              desc="Enable micro-animations and transitions"
              checked={animations}
              onChange={setAnimations}
            />

            <div>
              <label className="text-xs font-medium text-slate-400 mb-2 block">Interface Density</label>
              <div className="flex gap-2">
                {['compact', 'comfortable', 'spacious'].map(d => (
                  <button
                    key={d}
                    onClick={() => setDensity(d)}
                    className={`flex-1 py-2 rounded-lg text-xs font-medium capitalize border transition-all
                      ${density === d
                        ? 'bg-indigo-600/30 border-indigo-500/50 text-indigo-300'
                        : 'bg-white/5 border-white/10 text-slate-400 hover:bg-white/10'}`}
                  >
                    {d}
                  </button>
                ))}
              </div>
            </div>
          </Section>

          <Section title="Theme">
            <div className="grid grid-cols-2 gap-3">
              {[
                { id: 'dark-indigo', label: 'Dark Indigo', from: 'from-indigo-500', to: 'to-purple-500' },
                { id: 'dark-cyan',   label: 'Dark Cyan',   from: 'from-cyan-500',   to: 'to-blue-500' },
                { id: 'dark-rose',   label: 'Dark Rose',   from: 'from-rose-500',   to: 'to-pink-500' },
                { id: 'dark-amber',  label: 'Dark Amber',  from: 'from-amber-500',  to: 'to-orange-500' },
              ].map(theme => (
                <button
                  key={theme.id}
                  onClick={showSaved}
                  className="flex items-center gap-3 p-3 rounded-xl bg-white/5 border border-white/10 hover:border-white/20 transition-all"
                >
                  <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${theme.from} ${theme.to}`} />
                  <span className="text-sm text-slate-300">{theme.label}</span>
                </button>
              ))}
            </div>
          </Section>
        </div>
      )}

      {/* API Keys Tab */}
      {tab === 'api' && (
        <div className="space-y-4">
          <Section title="API Access">
            <p className="text-xs text-slate-500">Use these credentials to access the Athena AI API programmatically.</p>
            <Input label="API Base URL" value={window.location.origin + '/api'} onChange={() => {}} readonly />
            <Input label="API Documentation" value={window.location.origin + '/docs'} onChange={() => {}} readonly />
            <div className="flex gap-2 mt-2">
              <a
                href="/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-slate-300 text-sm hover:bg-white/10 transition-all"
              >
                Open Swagger UI →
              </a>
              <a
                href="/redoc"
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-slate-300 text-sm hover:bg-white/10 transition-all"
              >
                Open ReDoc →
              </a>
            </div>
          </Section>

          <Section title="External Integrations">
            {[
              { name: 'OpenAI',        key: 'OPENAI_API_KEY',           configured: true  },
              { name: 'Azure OpenAI',  key: 'AZURE_OPENAI_ENDPOINT',    configured: false },
              { name: 'Azure Search',  key: 'AZURE_SEARCH_ENDPOINT',    configured: false },
              { name: 'Azure Storage', key: 'AZURE_STORAGE_CONNECTION_STRING', configured: false },
              { name: 'Neo4j',         key: 'NEO4J_URI',                configured: false },
              { name: 'Slack Webhook', key: 'SLACK_WEBHOOK_URL',        configured: false },
            ].map(({ name, key, configured }) => (
              <div key={name} className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full shrink-0 ${configured ? 'bg-green-400' : 'bg-slate-600'}`} />
                <div className="flex-1">
                  <p className="text-sm text-slate-200">{name}</p>
                  <p className="text-xs font-mono text-slate-500">{key}</p>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full border ${
                  configured
                    ? 'bg-green-500/10 border-green-500/30 text-green-400'
                    : 'bg-slate-500/10 border-slate-500/30 text-slate-500'
                }`}>
                  {configured ? 'Configured' : 'Not set'}
                </span>
              </div>
            ))}
            <p className="text-xs text-slate-600 mt-2">Configure keys in your <code className="text-indigo-400">.env</code> file and restart the backend container.</p>
          </Section>
        </div>
      )}
    </div>
  )
}
