import React, { useState } from 'react'

export default function ChatInterface() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Welcome to Athena AI. I am connected to the Enterprise Knowledge Graph and available for secure querying. How can I assist you today?' }
  ])
  const [input, setInput] = useState('')

  const handleSend = () => {
    if (!input.trim()) return
    setMessages(prev => [...prev, { role: 'user', content: input }])
    
    // Simulate streaming response
    setTimeout(() => {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Processing request through Supervisor orchestrator...' }])
    }, 500)
    
    setInput('')
  }

  return (
    <div className="flex flex-col h-full bg-slate-900 rounded-xl border border-slate-800 shadow-inner overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-2xl px-5 py-4 shadow-md ${
              msg.role === 'user' 
                ? 'bg-blue-600 text-white rounded-br-none shadow-blue-900/20' 
                : 'bg-slate-800 text-slate-200 rounded-bl-none border border-slate-700/50'
            }`}>
              <p className="text-sm leading-relaxed">{msg.content}</p>
            </div>
          </div>
        ))}
      </div>
      
      <div className="p-4 bg-slate-800/50 border-t border-slate-800 backdrop-blur-md">
        <div className="flex gap-3">
          <input 
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask Athena to query Neo4j, analyze a PDF, or run a workflow..."
            className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all shadow-inner"
          />
          <button 
            onClick={handleSend}
            className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-3 rounded-xl text-sm font-medium transition-colors shadow-lg shadow-blue-500/20 flex items-center gap-2"
          >
            Send
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
          </button>
        </div>
      </div>
    </div>
  )
}
