import React from 'react'

export default function Sidebar({ activeView, setActiveView }) {
  const navItems = [
    { id: 'dashboard',   label: 'Dashboard',       icon: '📊' },
    { id: 'chat',        label: 'Chat Interface',   icon: '💬' },
    { id: 'workflow',    label: 'Workflow Builder', icon: '⚡' },
    { id: 'integration', label: 'API Hub',          icon: '🔌' },
    { id: 'security',    label: 'Security',         icon: '🔐' },
    { id: 'performance', label: 'Performance',      icon: '📈' },
    { id: 'settings',    label: 'Settings',         icon: '⚙️' },
  ]

  return (
    <div className="w-72 h-full bg-[#0B0F19]/80 backdrop-blur-2xl flex flex-col p-5 shrink-0 relative z-20">
      <div className="flex items-center gap-4 mb-10 px-2 py-4 border-b border-white/5">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center text-white shadow-[0_0_20px_rgba(99,102,241,0.4)]">
          <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
        </div>
        <div>
          <h2 className="text-xl font-extrabold text-white tracking-wide drop-shadow-md">Athena AI</h2>
          <p className="text-[10px] text-indigo-400 font-bold uppercase tracking-widest mt-0.5">Enterprise v1.0</p>
        </div>
      </div>
      
      <nav className="flex-1 space-y-2">
        {navItems.map(item => (
          <button
            key={item.id}
            onClick={() => setActiveView(item.id)}
            className={`w-full flex items-center gap-4 px-5 py-3.5 rounded-xl text-sm font-semibold transition-all duration-300 ${
              activeView === item.id 
                ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 shadow-[0_0_15px_rgba(99,102,241,0.15)]' 
                : 'text-slate-400 hover:bg-white/5 hover:text-slate-200 border border-transparent'
            }`}
          >
            <span className={`text-xl transition-transform duration-300 ${activeView === item.id ? 'scale-110' : ''}`}>{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>
      
      <div className="mt-auto p-4 glass-panel flex flex-col gap-1">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 flex items-center justify-center text-xs font-bold text-white shadow-inner">
            AD
          </div>
          <div className="text-left flex-1">
            <p className="text-sm font-bold text-slate-100">Admin User</p>
            <p className="text-xs text-indigo-300 font-medium">System Administrator</p>
          </div>
        </div>
        <div className="mt-3 flex items-center gap-2 px-1">
           <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_rgba(52,211,153,0.8)]"></div>
           <span className="text-[10px] font-semibold text-emerald-400 tracking-wider uppercase">System Online</span>
        </div>
      </div>
    </div>
  )
}
