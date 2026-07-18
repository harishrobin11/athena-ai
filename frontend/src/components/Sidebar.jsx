import React from 'react'

export default function Sidebar({ activeView, setActiveView }) {
  const navItems = [
    { id: 'chat', label: 'Chat Interface', icon: '💬' },
    { id: 'workflow', label: 'Workflow Builder', icon: '⚡' },
    { id: 'integration', label: 'API Hub', icon: '🔌' },
  ]

  return (
    <div className="w-72 h-full bg-slate-950 flex flex-col p-4 shrink-0 shadow-lg relative z-10">
      <div className="flex items-center gap-3 mb-8 px-2 py-4 border-b border-slate-800">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-emerald-500 flex items-center justify-center text-white shadow-[0_0_15px_rgba(59,130,246,0.5)]">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
        </div>
        <div>
          <h2 className="text-lg font-bold text-slate-100 tracking-wide">Athena AI</h2>
          <p className="text-xs text-slate-400 font-medium">Enterprise Engine v2.0</p>
        </div>
      </div>
      
      <nav className="flex-1 space-y-2">
        {navItems.map(item => (
          <button
            key={item.id}
            onClick={() => setActiveView(item.id)}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
              activeView === item.id 
                ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-[0_0_10px_rgba(37,99,235,0.1)]' 
                : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
            }`}
          >
            <span className="text-lg">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>
      
      <div className="mt-auto p-4 bg-slate-900/50 rounded-xl border border-slate-800 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-xs font-bold ring-2 ring-emerald-500/30">
            AD
          </div>
          <div className="text-left">
            <p className="text-sm font-medium text-slate-200">Admin User</p>
            <p className="text-xs text-emerald-400">System Online</p>
          </div>
        </div>
      </div>
    </div>
  )
}
