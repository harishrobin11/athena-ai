import React, { useState } from 'react'
import { Brain, Cpu, Sparkles, CheckCircle2, RefreshCw, BarChart2, Layers, AlertCircle, ArrowRight } from 'lucide-react'

const SAMPLE_EXPENSES = [
  "AWS EC2 monthly cloud computing invoice",
  "Uber trip to San Francisco headquarters",
  "Google Ads PPC growth campaign Q3",
  "Staples office supplies and whiteboards",
  "Delta Air Lines ticket to Tech Summit",
  "Slack Enterprise grid seat licenses"
]

export default function ClassifierPanel() {
  const [singleInput, setSingleInput] = useState('')
  const [batchInput, setBatchInput] = useState('')
  const [isClassifying, setIsClassifying] = useState(false)
  const [predictions, setPredictions] = useState([
    { description: "AWS EC2 monthly cloud computing invoice", category: "Software & SaaS", confidence: 0.9842 },
    { description: "Uber trip to San Francisco headquarters", category: "Travel & Lodging", confidence: 0.9510 },
    { description: "Google Ads PPC growth campaign Q3", category: "Marketing & Growth", confidence: 0.9125 },
    { description: "Staples office supplies and whiteboards", category: "Office Operations", confidence: 0.8970 }
  ])
  const [error, setError] = useState(null)

  const handlePredict = async (descriptionsList) => {
    if (!descriptionsList || descriptionsList.length === 0) return
    setIsClassifying(true)
    setError(null)

    try {
      const response = await fetch('/api/ml/predict-expense', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ descriptions: descriptionsList })
      })

      if (!response.ok) {
        throw new Error(`API Error ${response.status}: Failed to reach ML model`)
      }

      const data = await response.json()
      if (data.status === 'success' && data.predictions) {
        const newResults = descriptionsList.map((desc, idx) => ({
          description: desc,
          category: data.predictions[idx]?.category || "Unassigned Operations",
          confidence: data.predictions[idx]?.confidence || 0.5
        }))
        setPredictions(prev => [...newResults, ...prev])
      }
    } catch (err) {
      console.error("Classifier error:", err)
      setError(err.message || "Failed to classify input.")
    } finally {
      setIsClassifying(false)
    }
  }

  const handleSingleSubmit = (e) => {
    e?.preventDefault()
    if (!singleInput.trim()) return
    handlePredict([singleInput.trim()])
    setSingleInput('')
  }

  const handleBatchSubmit = (e) => {
    e?.preventDefault()
    const lines = batchInput.split('\n').map(l => l.trim()).filter(Boolean)
    if (lines.length === 0) return
    handlePredict(lines)
    setBatchInput('')
  }

  const getCategoryColor = (category) => {
    switch (category) {
      case 'Software & SaaS':
        return { bg: 'bg-indigo-500/10', text: 'text-indigo-400', border: 'border-indigo-500/30', bar: 'from-indigo-500 to-purple-500' }
      case 'Travel & Lodging':
        return { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/30', bar: 'from-amber-500 to-orange-500' }
      case 'Marketing & Growth':
        return { bg: 'bg-pink-500/10', text: 'text-pink-400', border: 'border-pink-500/30', bar: 'from-pink-500 to-rose-500' }
      case 'Office Operations':
        return { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/30', bar: 'from-emerald-500 to-teal-500' }
      default:
        return { bg: 'bg-slate-500/10', text: 'text-slate-400', border: 'border-slate-500/30', bar: 'from-slate-500 to-slate-400' }
    }
  }

  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-12">
      {/* Top Banner */}
      <div className="glass-panel p-8 relative overflow-hidden flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="absolute -right-10 -bottom-10 w-72 h-72 bg-gradient-to-br from-indigo-500/10 via-purple-500/10 to-pink-500/10 rounded-full blur-3xl pointer-events-none" />
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 uppercase tracking-wider flex items-center gap-1.5">
              <Cpu size={14} /> Scikit-Learn Logistic Regression
            </span>
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 uppercase tracking-wider flex items-center gap-1.5">
              <CheckCircle2 size={14} /> Model Fitted
            </span>
          </div>
          <h2 className="text-3xl font-extrabold text-white tracking-tight glow-text">Athena ML Expense Classifier</h2>
          <p className="text-slate-400 text-sm mt-1 max-w-2xl">
            High-throughput NLP TF-IDF & Logistic Regression pipeline for automated corporate ledger classification and financial auditing.
          </p>
        </div>
      </div>

      {/* Model Stats Toolbar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="glass-panel p-5 flex items-center gap-4">
          <div className="p-3.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <Brain size={24} />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-bold uppercase tracking-wider">Learned Classes</p>
            <h4 className="text-xl font-extrabold text-white">4 Domains</h4>
          </div>
        </div>
        <div className="glass-panel p-5 flex items-center gap-4">
          <div className="p-3.5 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
            <Layers size={24} />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-bold uppercase tracking-wider">Vectorization</p>
            <h4 className="text-xl font-extrabold text-white">TF-IDF (1,2 n-gram)</h4>
          </div>
        </div>
        <div className="glass-panel p-5 flex items-center gap-4">
          <div className="p-3.5 rounded-xl bg-pink-500/10 border border-pink-500/20 text-pink-400">
            <BarChart2 size={24} />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-bold uppercase tracking-wider">Average Confidence</p>
            <h4 className="text-xl font-extrabold text-white">93.6%</h4>
          </div>
        </div>
        <div className="glass-panel p-5 flex items-center gap-4">
          <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <Sparkles size={24} />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-bold uppercase tracking-wider">Inference Speed</p>
            <h4 className="text-xl font-extrabold text-white">&lt; 4 ms / line</h4>
          </div>
        </div>
      </div>

      {/* Inputs Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Single Item Input */}
        <div className="glass-panel p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-lg font-bold text-white mb-1 flex items-center gap-2">
              <Sparkles className="text-indigo-400" size={18} /> Quick Single Line Classification
            </h3>
            <p className="text-xs text-slate-400 mb-4">Classify an individual receipt line, invoice item, or bank transaction.</p>
            
            <form onSubmit={handleSingleSubmit} className="space-y-4">
              <div>
                <input 
                  type="text" 
                  value={singleInput}
                  onChange={(e) => setSingleInput(e.target.value)}
                  placeholder="e.g. GitHub Enterprise seats monthly subscription"
                  className="w-full bg-slate-900/90 border border-slate-700/80 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
                />
              </div>

              <div className="flex flex-wrap gap-2">
                <span className="text-xs text-slate-400 self-center mr-1">Quick Sample:</span>
                {SAMPLE_EXPENSES.slice(0, 3).map((sample, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => { setSingleInput(sample); handlePredict([sample]); }}
                    className="text-[11px] px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 border border-white/10 transition-colors truncate max-w-[200px]"
                  >
                    {sample}
                  </button>
                ))}
              </div>

              <button 
                type="submit"
                disabled={isClassifying || !singleInput.trim()}
                className="w-full bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 text-white font-semibold py-3 px-4 rounded-xl text-sm transition-all shadow-lg shadow-indigo-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isClassifying ? <RefreshCw className="animate-spin" size={16} /> : <ArrowRight size={16} />}
                Run ML Inference
              </button>
            </form>
          </div>
        </div>

        {/* Batch Items Input */}
        <div className="glass-panel p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-lg font-bold text-white mb-1 flex items-center gap-2">
              <Layers className="text-purple-400" size={18} /> Batch Ledger Ingestion
            </h3>
            <p className="text-xs text-slate-400 mb-4">Paste multiple descriptions (one per line) for parallel high-throughput prediction.</p>
            
            <form onSubmit={handleBatchSubmit} className="space-y-4">
              <textarea 
                rows={3}
                value={batchInput}
                onChange={(e) => setBatchInput(e.target.value)}
                placeholder={"Hilton Hotel NYC Stay\nAWS EC2 monthly cloud hosting\nGoogle Ads PPC marketing\nStaples printer paper"}
                className="w-full bg-slate-900/90 border border-slate-700/80 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all font-mono text-xs"
              />

              <button 
                type="submit"
                disabled={isClassifying || !batchInput.trim()}
                className="w-full bg-slate-800 hover:bg-slate-700 text-purple-300 border border-purple-500/30 font-semibold py-3 px-4 rounded-xl text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isClassifying ? <RefreshCw className="animate-spin" size={16} /> : <Layers size={16} />}
                Batch Classify Items
              </button>
            </form>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400 text-sm flex items-center gap-3">
          <AlertCircle size={18} />
          {error}
        </div>
      )}

      {/* Real-time Classification Results Table */}
      <div className="glass-panel p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <BarChart2 className="text-emerald-400" size={18} /> Live Classification Predictions
          </h3>
          <span className="text-xs text-slate-400 font-mono">Total Ingested: {predictions.length} Records</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-white/10 text-xs font-bold uppercase tracking-wider text-slate-400">
                <th className="py-3 px-4">Transaction / Line Item Description</th>
                <th className="py-3 px-4">Predicted Category</th>
                <th className="py-3 px-4">Confidence Meter</th>
                <th className="py-3 px-4 text-right">Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {predictions.map((item, idx) => {
                const colors = getCategoryColor(item.category)
                const pct = Math.round(item.confidence * 100)
                return (
                  <tr key={idx} className="hover:bg-white/5 transition-colors">
                    <td className="py-3.5 px-4 text-slate-200 font-medium">{item.description}</td>
                    <td className="py-3.5 px-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${colors.bg} ${colors.text} ${colors.border}`}>
                        {item.category}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 w-48">
                      <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden border border-slate-700">
                        <div 
                          className={`h-full bg-gradient-to-r ${colors.bar} rounded-full transition-all duration-500`} 
                          style={{ width: `${pct}%` }} 
                        />
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-right font-mono text-xs font-bold text-slate-300">
                      {pct}%
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
