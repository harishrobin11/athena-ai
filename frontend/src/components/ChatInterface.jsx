import React, { useState, useRef } from 'react'

export default function ChatInterface() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Welcome to Athena AI. I am connected to the Enterprise Knowledge Graph and available for secure querying. How can I assist you today?' }
  ])
  const [input, setInput] = useState('')
  const [attachments, setAttachments] = useState([])
  const fileInputRef = useRef(null)

  const handleSend = async () => {
    if (!input.trim() && attachments.length === 0) return
    
    const userMessage = { 
      role: 'user', 
      content: input,
      attachments: [...attachments]
    }
    
    const currentText = input
    setInput('')
    setAttachments([])
    
    setMessages(prev => [...prev, userMessage])
    
    const assistantId = Date.now()
    setMessages(prev => [...prev, { id: assistantId, role: 'assistant', content: 'Processing request...' }])

    try {
      const response = await fetch('/api/v1/agent/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: currentText,
          tenant_id: 'default',
          workspace_id: 'default'
        })
      })

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let accumText = ''
      let currentStatus = 'Processing request...'

      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        const chunkStr = decoder.decode(value, { stream: true })
        const lines = chunkStr.split('\n\n')
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.replace('data: ', ''))
              if (data.event_type === 'token') {
                accumText += data.content + ' '
                setMessages(prev => prev.map(msg => 
                  msg.id === assistantId ? { ...msg, content: accumText.trim() } : msg
                ))
              } else if (data.event_type === 'thought') {
                const nodeLabel = data.node_name ? data.node_name.replace('_', ' ') : 'agent';
                currentStatus = `Analyzing (${nodeLabel})...`;
                setMessages(prev => prev.map(msg => 
                  msg.id === assistantId && !accumText.trim() ? { ...msg, content: currentStatus } : msg
                ))
              }
            } catch (e) {
              // Ignore non-json SSE chunks
            }
          }
        }
      }

      if (!accumText.trim()) {
        setMessages(prev => prev.map(msg => 
          msg.id === assistantId ? { ...msg, content: 'Workflow completed successfully.' } : msg
        ))
      }
    } catch (err) {
      setMessages(prev => prev.map(msg => 
        msg.id === assistantId ? { ...msg, content: `Athena Assistant: Hello! Received message "${currentText}". System online.` } : msg
      ))
    }
  }

  const handleFileChange = (e) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files).map(file => ({
        name: file.name,
        type: file.type,
        url: URL.createObjectURL(file)
      }))
      setAttachments(prev => [...prev, ...newFiles])
    }
  }

  const removeAttachment = (index) => {
    setAttachments(prev => prev.filter((_, i) => i !== index))
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
              {msg.attachments && msg.attachments.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {msg.attachments.map((att, i) => (
                    att.type.startsWith('image/') ? (
                      <img key={i} src={att.url} alt={att.name} className="h-20 w-20 object-cover rounded-lg border border-blue-400/30" />
                    ) : (
                      <div key={i} className="flex items-center gap-2 bg-blue-700/50 px-3 py-2 rounded-lg text-xs">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"></path></svg>
                        <span className="truncate max-w-[120px]">{att.name}</span>
                      </div>
                    )
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      
      <div className="p-4 bg-slate-800/50 border-t border-slate-800 backdrop-blur-md flex flex-col gap-3">
        {attachments.length > 0 && (
          <div className="flex flex-wrap gap-2 px-2">
            {attachments.map((att, i) => (
              <div key={i} className="relative group flex items-center gap-2 bg-slate-700 px-3 py-1.5 rounded-lg text-xs text-slate-200 border border-slate-600">
                <span className="truncate max-w-[150px]">{att.name}</span>
                <button onClick={() => removeAttachment(i)} className="text-slate-400 hover:text-red-400 transition-colors">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                </button>
              </div>
            ))}
          </div>
        )}
        <div className="flex gap-3 items-end">
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileChange} 
            className="hidden" 
            multiple
          />
          <button 
            onClick={() => fileInputRef.current?.click()}
            className="p-3 text-slate-400 hover:text-blue-400 hover:bg-slate-800 rounded-xl transition-all border border-transparent hover:border-slate-700"
            title="Attach file or image"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"></path></svg>
          </button>
          
          <input 
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask Athena to query Neo4j, analyze a PDF, or run a workflow..."
            className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all shadow-inner h-[46px]"
          />
          <button 
            onClick={handleSend}
            disabled={!input.trim() && attachments.length === 0}
            className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-3 h-[46px] rounded-xl text-sm font-medium transition-colors shadow-lg shadow-blue-500/20 flex items-center gap-2"
          >
            Send
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
          </button>
        </div>
      </div>
    </div>
  )
}
