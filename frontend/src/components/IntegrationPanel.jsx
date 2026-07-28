import React from 'react'

export default function IntegrationPanel() {
  const integrations = [
    { name: 'Slack', status: 'Connected', color: 'bg-emerald-500' },
    { name: 'Microsoft Teams', status: 'Disconnected', color: 'bg-rose-500' },
    { name: 'Jira', status: 'Disconnected', color: 'bg-rose-500' },
    { name: 'Salesforce', status: 'Disconnected', color: 'bg-rose-500' },
  ]

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 shadow-lg">
        <h3 className="text-lg font-semibold text-slate-100 mb-1">Active Connections</h3>
        <p className="text-sm text-slate-400 mb-6">Monitor the status of your enterprise API hooks.</p>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {integrations.map(int => (
            <div key={int.name} className="bg-slate-900 rounded-lg p-5 border border-slate-700 flex flex-col items-center justify-center text-center gap-3">
              <h4 className="text-sm font-medium text-slate-200">{int.name}</h4>
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${int.color} shadow-[0_0_8px_currentColor]`}></span>
                <span className="text-xs text-slate-400">{int.status}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 shadow-lg max-w-2xl">
        <h3 className="text-lg font-semibold text-slate-100 mb-6">Configure Integration</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1 uppercase tracking-wider">Platform</label>
            <select className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50">
              <option>Slack</option>
              <option>Microsoft Teams</option>
              <option>Jira</option>
              <option>Salesforce</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1 uppercase tracking-wider">API Key / Bearer Token</label>
            <input 
              type="password" 
              placeholder="••••••••••••••••"
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            />
          </div>
          <button className="w-full mt-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2.5 rounded-lg text-sm font-medium transition-colors shadow-lg shadow-blue-500/20">
            Connect Service
          </button>
        </div>
      </div>
    </div>
  )
}
