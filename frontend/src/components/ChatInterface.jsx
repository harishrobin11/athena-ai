import React, { useState, useRef, useEffect } from 'react'

export default function ChatInterface({ 
  user,
  currentSession,
  onUpdateSessionMessages,
  onNewChat
}) {
  const [messages, setMessages] = useState(currentSession?.messages || [])
  const [input, setInput] = useState('')
  const [attachments, setAttachments] = useState([])
  const [isSearching, setIsSearching] = useState(false)
  const [copiedId, setCopiedId] = useState(null)
  
  const fileInputRef = useRef(null)
  const messagesEndRef = useRef(null)

  // Sync messages when current session changes
  useEffect(() => {
    setMessages(currentSession?.messages || [])
  }, [currentSession?.id])

  // Save messages back to session state whenever messages update
  useEffect(() => {
    if (currentSession?.id && onUpdateSessionMessages) {
      onUpdateSessionMessages(currentSession.id, messages)
    }
  }, [messages])

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isSearching])

  const handleSend = async (textToSend = null) => {
    const messageText = textToSend !== null ? textToSend : input
    if (!messageText.trim() && attachments.length === 0) return

    const userMessage = {
      id: Date.now() + '_user',
      role: 'user',
      content: messageText,
      attachments: [...attachments]
    }

    setInput('')
    setAttachments([])
    setIsSearching(true)

    const updatedMessages = [...messages, userMessage]
    setMessages(updatedMessages)

    const assistantId = Date.now() + '_assistant'
    const initialAssistantMsg = { id: assistantId, role: 'assistant', content: 'Processing request...' }
    setMessages(prev => [...prev, initialAssistantMsg])

    try {
      // 1. Upload attached files in parallel to document service
      const token = localStorage.getItem('token') || localStorage.getItem('accessToken') || ''
      const uploadHeaders = token ? { 'Authorization': `Bearer ${token}` } : {}

      const pendingUploads = userMessage.attachments.filter(att => att.rawFile)
      if (pendingUploads.length > 0) {
        setMessages(prev => prev.map(msg =>
          msg.id === assistantId ? { ...msg, content: `Connecting document vault...` } : msg
        ))
        await Promise.all(pendingUploads.map(async (att) => {
          try {
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
        }))
      }

      const selectedDocs = userMessage.attachments.map(att => att.name)

      const response = await fetch('/api/v1/agent/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: messageText,
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

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  const promptCards = [
    {
      title: "📄 Analyze PDF Invoice",
      subtitle: "Extract line items, grand totals, and tax metadata from uploaded documents.",
      query: "Analyze the uploaded invoice PDF and provide a structured summary of totals and line items."
    },
    {
      title: "🔍 Query Knowledge Graph",
      subtitle: "Search Neo4j graph nodes for risk factors, departments, and compliance entities.",
      query: "Search the Enterprise Knowledge Graph for compliance risks and top-level corporate entities."
    },
    {
      title: "📊 Run SQL Analytics",
      subtitle: "Execute Python and SQL queries to analyze quarterly departmental expense data.",
      query: "Run SQL analytics to calculate the total department expenses and top category breakdown."
    },
    {
      title: "⚡ Automate Workflows",
      subtitle: "Schedule cron jobs, automated triggers, and multi-step external API pipelines.",
      query: "Create a scheduled workflow to perform daily compliance health checks."
    }
  ]

  const userInitials = user?.username ? user.username.substring(0, 2).toUpperCase() : 'ME'

  return (
    <div className="flex flex-col h-full w-full bg-[#0B0F17] text-slate-100 relative overflow-hidden">
      {/* ChatGPT Style Top Header */}
      <div className="h-14 border-b border-slate-800/60 px-6 flex items-center justify-between bg-[#0B0F17]/90 backdrop-blur-md shrink-0 z-20">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1 bg-slate-800/80 hover:bg-slate-800 border border-slate-700/60 rounded-full text-xs font-semibold text-slate-300 transition-colors cursor-pointer">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>Athena AI • Gemini 3.6 Flash</span>
            <svg className="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {onNewChat && (
            <button
              onClick={onNewChat}
              className="px-3 py-1.5 bg-slate-800/60 hover:bg-slate-800 text-slate-300 rounded-lg text-xs font-semibold border border-slate-700/50 transition-colors flex items-center gap-1.5"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" /></svg>
              New Chat
            </button>
          )}
        </div>
      </div>

      {/* Main Conversation Body */}
      <div className="flex-1 overflow-y-auto custom-scrollbar flex flex-col items-center">
        {messages.length === 0 ? (
          /* Empty State / ChatGPT Hero Screen */
          <div className="max-w-3xl w-full px-6 py-12 flex flex-col items-center justify-center my-auto text-center">
            <div className="w-16 h-16 rounded-3xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-600 flex items-center justify-center text-white shadow-[0_0_40px_rgba(99,102,241,0.4)] mb-6 animate-pulse">
              <svg className="w-9 h-9" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
            </div>
            
            <h1 className="text-3xl font-extrabold text-white tracking-tight mb-2">What can I help with today?</h1>
            <p className="text-sm text-slate-400 max-w-md mb-10 leading-relaxed">
              Athena AI is connected to your Enterprise Knowledge Graph, vector vault, and automated workflows.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 w-full text-left">
              {promptCards.map((card, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(card.query)}
                  className="p-4 rounded-2xl bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800 hover:border-slate-700/80 transition-all text-left group shadow-lg flex flex-col justify-between"
                >
                  <div>
                    <h3 className="text-sm font-bold text-slate-200 group-hover:text-indigo-300 transition-colors mb-1">{card.title}</h3>
                    <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">{card.subtitle}</p>
                  </div>
                  <div className="mt-3 flex items-center justify-end text-xs font-semibold text-indigo-400 group-hover:translate-x-1 transition-transform">
                    <span>Ask Athena →</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        ) : (
          /* Active Message Stream */
          <div className="max-w-3xl w-full px-4 py-8 space-y-6">
            {messages.map((msg, idx) => (
              <div 
                key={msg.id || idx} 
                className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {/* Assistant Avatar */}
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center text-white shrink-0 shadow-md mt-1">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                  </div>
                )}

                {/* Message Body */}
                <div className={`group relative max-w-[85%] rounded-2xl px-5 py-4 text-sm leading-relaxed shadow-sm ${
                  msg.role === 'user'
                    ? 'bg-indigo-600 text-white rounded-br-sm shadow-indigo-600/20'
                    : 'bg-slate-900/90 text-slate-100 rounded-bl-sm border border-slate-800/80 backdrop-blur-md'
                }`}>
                  <div className="whitespace-pre-wrap font-sans">{msg.content}</div>

                  {/* Attachments preview list */}
                  {msg.attachments && msg.attachments.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2 pt-2 border-t border-white/10">
                      {msg.attachments.map((att, i) => (
                        att.type && att.type.startsWith('image/') ? (
                          <img key={i} src={att.url} alt={att.name} className="h-20 w-20 object-cover rounded-lg border border-white/20" />
                        ) : (
                          <div key={i} className="flex items-center gap-2 bg-black/20 px-3 py-1.5 rounded-lg text-xs">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"></path></svg>
                            <span className="truncate max-w-[140px]">{att.name}</span>
                          </div>
                        )
                      ))}
                    </div>
                  )}

                  {/* Copy Button for Assistant */}
                  {msg.role === 'assistant' && (
                    <div className="mt-2 flex items-center justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => copyToClipboard(msg.content, msg.id)}
                        className="text-[11px] text-slate-400 hover:text-indigo-300 flex items-center gap-1 bg-slate-800/80 px-2 py-1 rounded-md transition-colors"
                      >
                        {copiedId === msg.id ? (
                          <>
                            <svg className="w-3 h-3 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" /></svg>
                            <span className="text-emerald-400">Copied!</span>
                          </>
                        ) : (
                          <>
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                            <span>Copy</span>
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>

                {/* User Avatar */}
                {msg.role === 'user' && (
                  <div className="w-8 h-8 rounded-xl bg-slate-700 flex items-center justify-center text-xs font-bold text-white shrink-0 shadow-md mt-1">
                    {userInitials}
                  </div>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Floating Bottom Prompt Bar (ChatGPT Style) */}
      <div className="w-full max-w-3xl mx-auto px-4 pb-6 pt-2 shrink-0 z-20">
        {/* File Attachment Chips */}
        {attachments.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-2 px-1">
            {attachments.map((att, i) => (
              <div key={i} className="flex items-center gap-2 bg-slate-800 border border-slate-700 px-3 py-1.5 rounded-xl text-xs text-slate-200">
                <span className="truncate max-w-[160px]">{att.name}</span>
                <button onClick={() => removeAttachment(i)} className="text-slate-400 hover:text-red-400">
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                </button>
              </div>
            ))}
          </div>
        )}

        <div className={`copilot-prompt-container ${isSearching ? 'searching' : ''}`}>
          {isSearching && (
            <div className="copilot-sparkle-layer">
              <div className="copilot-sparkle" style={{ left: '10%', top: '20%', animationDelay: '0s' }} />
              <div className="copilot-sparkle" style={{ left: '35%', top: '70%', animationDelay: '0.3s' }} />
              <div className="copilot-sparkle" style={{ left: '60%', top: '15%', animationDelay: '0.6s' }} />
              <div className="copilot-sparkle" style={{ left: '85%', top: '65%', animationDelay: '0.9s' }} />
            </div>
          )}

          <div className="copilot-prompt-inner">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              className="hidden"
              multiple
            />
            
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="p-2 text-slate-400 hover:text-indigo-300 hover:bg-slate-800/80 rounded-xl transition-all shrink-0"
              title="Attach PDF or Image"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"></path></svg>
            </button>

            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !isSearching && handleSend()}
              placeholder="Message Athena AI..."
              disabled={isSearching}
              className="flex-1 bg-transparent px-2 py-1.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
            />

            <button
              type="button"
              onClick={() => handleSend()}
              disabled={isSearching || (!input.trim() && attachments.length === 0)}
              className="p-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 disabled:opacity-30 disabled:cursor-not-allowed text-white transition-all shadow-md shadow-indigo-600/30 shrink-0 active:scale-95"
            >
              {isSearching ? (
                <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
              )}
            </button>
          </div>
        </div>

        <p className="text-[11px] text-center text-slate-500 mt-2">
          Athena AI may produce accurate results grounded in your enterprise knowledge vault.
        </p>
      </div>
    </div>
  )
}
