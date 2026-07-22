import React from 'react'

export default function ChatSidebar({ 
  onBackToMain, 
  onNewChat, 
  sessions = [], 
  currentSessionId, 
  onSelectSession, 
  onDeleteSession,
  user,
  onOpenAuth
}) {
  const userInitials = user?.username ? user.username.substring(0, 2).toUpperCase() : 'AD'
  const userName = user?.username || 'Admin User'
  const userRole = user?.role ? `${user.department} • ${user.role}` : 'Enterprise Admin'

  return (
    <div className="w-72 h-full bg-[#090D16] border-r border-slate-800/60 flex flex-col p-3 text-slate-200 shrink-0 select-none z-30">
      {/* 1. Back to Athena Main Page */}
      <button
        onClick={onBackToMain}
        className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl bg-slate-800/40 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700/50 text-xs font-semibold transition-all mb-3 group shadow-sm"
      >
        <span className="p-1 rounded-lg bg-indigo-500/20 text-indigo-400 group-hover:-translate-x-0.5 transition-transform">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
        </span>
        <div className="text-left min-w-0 flex-1">
          <p className="font-bold text-slate-200 group-hover:text-white truncate">Back to Athena AI</p>
          <p className="text-[10px] text-slate-400 font-normal truncate">Return to Analytics & Tools</p>
        </div>
      </button>

      {/* 2. New Chat Button */}
      <button
        onClick={onNewChat}
        className="w-full flex items-center justify-between px-4 py-3 rounded-xl bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 text-white font-semibold text-sm transition-all shadow-lg shadow-indigo-600/25 active:scale-[0.98] mb-4"
      >
        <div className="flex items-center gap-2.5">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M12 4v16m8-8H4" />
          </svg>
          <span>New Chat</span>
        </div>
        <span className="text-[10px] bg-white/20 px-2 py-0.5 rounded-md font-mono">⌘N</span>
      </button>

      {/* 3. Chat History Title */}
      <div className="px-2 pb-2 flex items-center justify-between text-[11px] font-bold text-slate-400 tracking-wider uppercase border-b border-slate-800/50 mb-2">
        <span>Recent Conversations</span>
        <span className="text-slate-500 font-mono text-[10px]">{sessions.length}</span>
      </div>

      {/* 4. Scrollable Chat History List */}
      <div className="flex-1 overflow-y-auto space-y-1 pr-1 custom-scrollbar">
        {sessions.length === 0 ? (
          <div className="p-4 text-center text-xs text-slate-500 italic">
            No past conversations yet. Start a new chat!
          </div>
        ) : (
          sessions.map((sess) => {
            const isActive = sess.id === currentSessionId
            return (
              <div
                key={sess.id}
                onClick={() => onSelectSession(sess.id)}
                className={`group relative flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium cursor-pointer transition-all ${
                  isActive
                    ? 'bg-indigo-600/20 text-indigo-200 border border-indigo-500/30 shadow-[0_0_12px_rgba(99,102,241,0.1)]'
                    : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200 border border-transparent'
                }`}
              >
                <div className="flex items-center gap-2.5 min-w-0 flex-1 pr-2">
                  <svg className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-indigo-400' : 'text-slate-500'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                  <span className="truncate">{sess.title || 'New Conversation'}</span>
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onDeleteSession(sess.id)
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-red-400 hover:bg-slate-700/50 rounded transition-all"
                  title="Delete conversation"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            )
          })
        )}
      </div>

      {/* 5. User Account Footer */}
      <div className="mt-auto pt-3 border-t border-slate-800/80 flex flex-col gap-2">
        <div className="flex items-center gap-3 px-2 py-1.5">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-xs font-bold text-white shadow-inner shrink-0">
            {userInitials}
          </div>
          <div className="text-left flex-1 min-w-0">
            <p className="text-xs font-bold text-slate-200 truncate">{userName}</p>
            <p className="text-[10px] text-indigo-400 font-medium truncate">{userRole}</p>
          </div>
        </div>

        <button 
          onClick={onOpenAuth}
          className="w-full py-1.5 px-3 bg-slate-800/50 hover:bg-slate-800 text-slate-300 border border-slate-700/50 rounded-xl text-[11px] font-semibold transition-colors flex items-center justify-center gap-1.5"
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>
          Account & Preferences
        </button>
      </div>
    </div>
  )
}
