import { useState, useEffect, useRef } from 'react'

const API_BASE = '/api/notifications'

const typeConfig = {
  info:    { color: 'bg-blue-500/20 border-blue-500/30 text-blue-300',  icon: 'ℹ️', dot: 'bg-blue-400' },
  success: { color: 'bg-green-500/20 border-green-500/30 text-green-300', icon: '✅', dot: 'bg-green-400' },
  warning: { color: 'bg-yellow-500/20 border-yellow-500/30 text-yellow-300', icon: '⚠️', dot: 'bg-yellow-400' },
  error:   { color: 'bg-red-500/20 border-red-500/30 text-red-300',    icon: '❌', dot: 'bg-red-400' },
  agent:   { color: 'bg-indigo-500/20 border-indigo-500/30 text-indigo-300', icon: '🤖', dot: 'bg-indigo-400' },
}

function timeAgo(iso) {
  const diff = Math.floor((Date.now() - new Date(iso)) / 1000)
  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

export default function NotificationBell() {
  const [open, setOpen] = useState(false)
  const [notifications, setNotifications] = useState([])
  const [unread, setUnread] = useState(0)
  const [loading, setLoading] = useState(false)
  const ref = useRef(null)

  const fetchNotifications = async () => {
    try {
      const res = await fetch(`${API_BASE}/?limit=30`)
      if (res.ok) {
        const data = await res.json()
        setNotifications(data)
        setUnread(data.filter(n => !n.read).length)
      }
    } catch (e) {
      // backend might not be ready yet — silently fail
    }
  }

  useEffect(() => {
    fetchNotifications()
    const interval = setInterval(fetchNotifications, 15000) // poll every 15s
    return () => clearInterval(interval)
  }, [])

  // Close on outside click
  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleOpen = () => {
    setOpen(o => !o)
    if (!open) fetchNotifications()
  }

  const markRead = async (id) => {
    try {
      await fetch(`${API_BASE}/${id}/read`, { method: 'PATCH' })
      setNotifications(ns => ns.map(n => n.id === id ? { ...n, read: true } : n))
      setUnread(u => Math.max(0, u - 1))
    } catch (e) {}
  }

  const markAllRead = async () => {
    try {
      await fetch(`${API_BASE}/mark-all-read`, { method: 'PATCH' })
      setNotifications(ns => ns.map(n => ({ ...n, read: true })))
      setUnread(0)
    } catch (e) {}
  }

  const deleteNotif = async (id, e) => {
    e.stopPropagation()
    try {
      await fetch(`${API_BASE}/${id}`, { method: 'DELETE' })
      setNotifications(ns => ns.filter(n => n.id !== id))
    } catch (e) {}
  }

  return (
    <div className="relative" ref={ref}>
      {/* Bell Button */}
      <button
        onClick={handleOpen}
        id="notification-bell-btn"
        className="relative p-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10
                   hover:border-indigo-500/40 transition-all duration-200 group"
        aria-label="Notifications"
      >
        <svg className="w-5 h-5 text-slate-300 group-hover:text-indigo-300 transition-colors" 
             fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6 6 0 10-12 0v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        {unread > 0 && (
          <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 flex items-center justify-center
                           rounded-full bg-indigo-500 text-[10px] font-bold text-white shadow-lg shadow-indigo-500/40
                           animate-pulse">
            {unread > 99 ? '99+' : unread}
          </span>
        )}
      </button>

      {/* Dropdown Panel */}
      {open && (
        <div className="absolute right-0 top-12 w-[380px] max-h-[520px] flex flex-col
                        bg-[#111827]/95 backdrop-blur-xl border border-white/10 rounded-2xl
                        shadow-2xl shadow-black/50 z-50 overflow-hidden
                        animate-in slide-in-from-top-2 duration-200">
          
          {/* Header */}
          <div className="flex items-center justify-between px-5 py-4 border-b border-white/5">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-white">Notifications</h3>
              {unread > 0 && (
                <span className="px-1.5 py-0.5 text-[10px] font-bold bg-indigo-500/20 text-indigo-300 
                                 border border-indigo-500/30 rounded-full">
                  {unread} new
                </span>
              )}
            </div>
            {unread > 0 && (
              <button
                onClick={markAllRead}
                className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors font-medium"
              >
                Mark all read
              </button>
            )}
          </div>

          {/* Notification List */}
          <div className="flex-1 overflow-y-auto divide-y divide-white/5">
            {notifications.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 gap-3 text-center">
                <div className="w-12 h-12 rounded-2xl bg-white/5 flex items-center justify-center text-2xl">🔔</div>
                <p className="text-sm text-slate-400">No notifications yet</p>
                <p className="text-xs text-slate-600">System events will appear here</p>
              </div>
            ) : (
              notifications.map(n => {
                const cfg = typeConfig[n.type] || typeConfig.info
                return (
                  <div
                    key={n.id}
                    onClick={() => !n.read && markRead(n.id)}
                    className={`relative flex gap-3 px-4 py-3.5 cursor-pointer transition-all duration-150
                                hover:bg-white/5 group
                                ${!n.read ? 'bg-indigo-500/5' : ''}`}
                  >
                    {/* Unread dot */}
                    {!n.read && (
                      <div className={`absolute left-1.5 top-1/2 -translate-y-1/2 w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
                    )}

                    {/* Icon */}
                    <div className={`shrink-0 w-8 h-8 rounded-lg border flex items-center justify-center text-sm ${cfg.color}`}>
                      {cfg.icon}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <p className={`text-sm font-medium truncate ${!n.read ? 'text-white' : 'text-slate-300'}`}>
                        {n.title}
                      </p>
                      <p className="text-xs text-slate-500 mt-0.5 line-clamp-2 leading-relaxed">
                        {n.message}
                      </p>
                      <div className="flex items-center gap-2 mt-1.5">
                        <span className="text-[10px] text-slate-600">{timeAgo(n.created_at)}</span>
                        {n.source !== 'system' && (
                          <span className="text-[10px] text-slate-600">• {n.source}</span>
                        )}
                      </div>
                    </div>

                    {/* Delete */}
                    <button
                      onClick={(e) => deleteNotif(n.id, e)}
                      className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity
                                 w-6 h-6 flex items-center justify-center rounded-lg
                                 hover:bg-red-500/20 text-slate-500 hover:text-red-400"
                    >
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                )
              })
            )}
          </div>

          {/* Footer */}
          {notifications.length > 0 && (
            <div className="px-5 py-3 border-t border-white/5 flex justify-between items-center">
              <span className="text-xs text-slate-600">{notifications.length} total</span>
              <button
                onClick={() => setOpen(false)}
                className="text-xs text-slate-500 hover:text-slate-300 transition-colors"
              >
                Close
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
