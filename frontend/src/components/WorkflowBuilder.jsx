import React, { useState } from 'react'

export default function WorkflowBuilder() {
  const [actions, setActions] = useState([])
  const [selectedAction, setSelectedAction] = useState('Run OCR Extraction')

  const availableActions = [
    "Run OCR Extraction",
    "Analyze Sentiment", 
    "Send Slack Message",
    "Create Jira Ticket",
    "Fetch Salesforce Data"
  ]

  const handleAdd = () => {
    setActions([...actions, selectedAction])
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 shadow-lg">
        <h3 className="text-lg font-semibold text-slate-100 mb-1">Create New Workflow</h3>
        <p className="text-sm text-slate-400 mb-6">Design and save event-driven automation sequences.</p>
        
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1 uppercase tracking-wider">Trigger</label>
            <select className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/50">
              <option>Manual (Run Now)</option>
              <option>On Document Upload</option>
              <option>Scheduled (Cron)</option>
            </select>
          </div>
          
          <div className="pt-4 border-t border-slate-700/50">
            <label className="block text-xs font-medium text-slate-400 mb-1 uppercase tracking-wider">Add Action</label>
            <div className="flex gap-3">
              <select 
                value={selectedAction}
                onChange={(e) => setSelectedAction(e.target.value)}
                className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              >
                {availableActions.map(a => <option key={a}>{a}</option>)}
              </select>
              <button 
                onClick={handleAdd}
                className="bg-slate-700 hover:bg-slate-600 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-colors border border-slate-600"
              >
                + Add Step
              </button>
            </div>
          </div>
        </div>
      </div>
      
      {actions.length > 0 && (
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 shadow-lg">
          <h4 className="text-sm font-semibold text-slate-200 mb-4 flex items-center justify-between">
            Execution Sequence
            <span className="bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded text-xs border border-blue-500/30">
              {actions.length} Steps
            </span>
          </h4>
          <div className="space-y-3">
            {actions.map((act, i) => (
              <div key={i} className="flex items-center gap-4 bg-slate-900/80 rounded-lg p-3 border border-slate-700">
                <div className="w-8 h-8 rounded-md bg-slate-800 flex items-center justify-center text-xs font-bold text-slate-400 border border-slate-700">
                  {i + 1}
                </div>
                <p className="text-sm text-slate-200 font-medium">{act}</p>
              </div>
            ))}
          </div>
          
          <div className="mt-6 pt-4 border-t border-slate-700/50 flex justify-end gap-3">
            <button 
              onClick={() => setActions([])}
              className="px-4 py-2 text-sm font-medium text-slate-400 hover:text-slate-200 transition-colors"
            >
              Clear
            </button>
            <button className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2 rounded-lg text-sm font-medium transition-colors shadow-lg shadow-emerald-500/20">
              Save & Deploy
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
