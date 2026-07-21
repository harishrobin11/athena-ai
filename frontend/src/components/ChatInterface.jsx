import React, { useState, useRef } from 'react'

export default function ChatInterface() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Welcome to Athena AI. I am connected to the Enterprise Knowledge Graph and available for secure querying. How can I assist you today?' }
  ])
  const [input, setInput] = useState('')
  const [attachments, setAttachments] = useState([])
  const fileInputRef = useRef(null)

  const [isSearching, setIsSearching] = useState(false)

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
    setIsSearching(true)
    
    setMessages(prev => [...prev, userMessage])
    
    const assistantId = Date.now()
    setMessages(prev => [...prev, { id: assistantId, role: 'assistant', content: 'Processing request...' }])

    try {
      // 1. Upload any attached files to vector storage first
      const token = localStorage.getItem('token') || localStorage.getItem('accessToken') || ''
      const uploadHeaders = token ? { 'Authorization': `Bearer ${token}` } : {}

      for (const att of userMessage.attachments) {
        if (att.rawFile) {
          try {
            setMessages(prev => prev.map(msg => 
              msg.id === assistantId ? { ...msg, content: `Ingesting document "${att.name}" into knowledge vault...` } : msg
            ))
            const formData = new FormData()
            formData.append('file', att.rawFile)
            const uploadRes = await fetch('/api/upload', {
              method: 'POST',
              headers: uploadHeaders,
              body: formData
            })
            if (!uploadRes.ok) {
              const errData = await uploadRes.json().catch(() => ({}))
              console.warn("Auto-upload attachment warning:", errData)
            }
          } catch (uploadErr) {
            console.warn("Auto-upload attachment error:", uploadErr)
          }
        }
      }


      const selectedDocs = userMessage.attachments.map(att => att.name)

      const response = await fetch('/api/v1/agent/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: currentText,
          tenant_id: 'default',
          workspace_id: 'default',
          selected_documents: selectedDocs
        })
      })

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let accumText = ''
      let currentStatus = 'Processing request...'
      let sseBuffer = ''

      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        sseBuffer += decoder.decode(value, { stream: true })

        const rawEvents = sseBuffer.split('\n\n')
        sseBuffer = rawEvents.pop() || ''

        for (const rawEvent of rawEvents) {
          const lines = rawEvent.split('\n')
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const jsonStr = line.slice(6).trim()
                if (!jsonStr) continue
                const data = JSON.parse(jsonStr)
                if (data.error) {
                  accumText = `Error: ${data.error}`
                  setMessages(prev => prev.map(msg => 
                    msg.id === assistantId ? { ...msg, content: accumText } : msg
                  ))
                } else if (data.event_type === 'token') {
                  accumText = data.content
                  setMessages(prev => prev.map(msg => 
                    msg.id === assistantId ? { ...msg, content: accumText } : msg
                  ))
                } else if (data.event_type === 'final') {
                  if (data.content && !accumText.trim()) {
                    accumText = data.content
                  }
                  setMessages(prev => prev.map(msg => 
                    msg.id === assistantId ? { ...msg, content: accumText || 'Workflow completed successfully.' } : msg
                  ))
                } else if (data.event_type === 'thought') {
                  const nodeLabel = data.node_name ? data.node_name.replace('_', ' ') : 'agent';
                  currentStatus = `Analyzing (${nodeLabel})...`;
                  setMessages(prev => prev.map(msg => 
                    msg.id === assistantId && !accumText.trim() ? { ...msg, content: currentStatus } : msg
                  ))
                }
              } catch (e) {
                // Ignore incomplete fragments
              }
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
      console.error("Chat API error:", err)
      setMessages(prev => prev.map(msg => 
        msg.id === assistantId ? { ...msg, content: `Error: Unable to complete request (${err.message || 'Server connection failed'})` } : msg
      ))
    } finally {
      setIsSearching(false)
    }
  }

  const handleFileChange = (e) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files).map(file => ({
        rawFile: file,
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
    <div className="flex flex-col h-full bg-slate-900/90 rounded-2xl border border-slate-800/80 shadow-2xl overflow-hidden backdrop-blur-xl">
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-2xl px-5 py-4 shadow-lg ${
              msg.role === 'user' 
                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-br-none shadow-indigo-900/30 border border-indigo-400/20' 
                : 'bg-slate-800/90 text-slate-100 rounded-bl-none border border-slate-700/60 shadow-black/40 backdrop-blur-md'
            }`}>
              <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
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
      
      <div className="p-4 bg-slate-950/40 border-t border-slate-800/60 backdrop-blur-2xl flex flex-col gap-3">
        {attachments.length > 0 && (
          <div className="flex flex-wrap gap-2 px-2">
            {attachments.map((att, i) => (
              <div key={i} className="relative group flex items-center gap-2 bg-slate-800/90 px-3 py-1.5 rounded-xl text-xs text-slate-200 border border-slate-700">
                <span className="truncate max-w-[150px]">{att.name}</span>
                <button onClick={() => removeAttachment(i)} className="text-slate-400 hover:text-red-400 transition-colors">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                </button>
              </div>
            ))}
          </div>
        )}
        
        {/* Copilot-style animated prompt box wrapper */}
        <div className={`copilot-prompt-container ${isSearching ? 'searching' : ''}`}>
          {isSearching && (
            <div className="copilot-sparkle-layer">
              <div className="copilot-sparkle" style={{ left: '15%', top: '25%', animationDelay: '0s' }} />
              <div className="copilot-sparkle" style={{ left: '42%', top: '65%', animationDelay: '0.4s' }} />
              <div className="copilot-sparkle" style={{ left: '68%', top: '20%', animationDelay: '0.8s' }} />
              <div className="copilot-sparkle" style={{ left: '88%', top: '55%', animationDelay: '1.2s' }} />
            </div>
          )}

          <div className="copilot-prompt-inner">
            <div className="flex gap-3 items-center w-full">
              <input 
                type="file" 
                ref={fileInputRef} 
                onChange={handleFileChange} 
                className="hidden" 
                multiple
              />
              <button 
                onClick={() => fileInputRef.current?.click()}
                className="p-2.5 text-slate-400 hover:text-indigo-400 hover:bg-slate-800/80 rounded-xl transition-all border border-transparent hover:border-slate-700/50"
                title="Attach file or image"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"></path></svg>
              </button>
              
              <input 
                type="text" 
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !isSearching && handleSend()}
                placeholder="Ask Athena to query Neo4j, analyze a PDF, or run a workflow..."
                disabled={isSearching}
                className="flex-1 bg-transparent border-0 px-2 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none transition-all h-[44px]"
              />
              <button 
                onClick={handleSend}
                disabled={isSearching || (!input.trim() && attachments.length === 0)}
                className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 disabled:opacity-50 disabled:cursor-not-allowed text-white px-5 py-2.5 h-[44px] rounded-xl text-sm font-semibold transition-all shadow-lg shadow-indigo-500/25 flex items-center gap-2 shrink-0 active:scale-95"
              >
                {isSearching ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-1 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Searching...
                  </>
                ) : (
                  <>
                    Send
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

