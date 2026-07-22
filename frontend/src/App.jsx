import { useState, useEffect } from 'react'
import Sidebar from './components/Sidebar'
import ChatSidebar from './components/ChatSidebar'
import ChatInterface from './components/ChatInterface'
import ClassifierPanel from './components/ClassifierPanel'
import WorkflowBuilder from './components/WorkflowBuilder'
import IntegrationPanel from './components/IntegrationPanel'
import Dashboard from './components/Dashboard'
import NotificationBell from './components/NotificationBell'
import SecurityDashboard from './components/SecurityDashboard'
import PerformanceDashboard from './components/PerformanceDashboard'
import SettingsPage from './components/SettingsPage'
import AuthModal from './components/AuthModal'

function App() {
  const [activeView, setActiveView] = useState('dashboard')
  const [user, setUser] = useState(null)
  const [isAuthOpen, setIsAuthOpen] = useState(false)

  // Chat sessions state with local storage persistence
  const [chatSessions, setChatSessions] = useState(() => {
    try {
      const saved = localStorage.getItem('athena_chat_sessions')
      return saved ? JSON.parse(saved) : [
        { id: 'sess_1', title: 'Enterprise Knowledge Query', messages: [] }
      ]
    } catch(e) {
      return [{ id: 'sess_1', title: 'Enterprise Knowledge Query', messages: [] }]
    }
  })
  const [currentSessionId, setCurrentSessionId] = useState(() => chatSessions[0]?.id || 'sess_1')

  useEffect(() => {
    const savedUser = localStorage.getItem('athena_user')
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser))
      } catch (e) {}
    }
  }, [])

  useEffect(() => {
    try {
      localStorage.setItem('athena_chat_sessions', JSON.stringify(chatSessions))
    } catch(e) {}
  }, [chatSessions])

  const handleAuthSuccess = (userData) => {
    setUser(userData)
  }

  const handleNewChat = () => {
    const newId = 'sess_' + Date.now()
    const newSession = { id: newId, title: 'New Conversation', messages: [] }
    setChatSessions(prev => [newSession, ...prev])
    setCurrentSessionId(newId)
  }

  const handleSelectSession = (id) => {
    setCurrentSessionId(id)
  }

  const handleDeleteSession = (id) => {
    setChatSessions(prev => {
      const filtered = prev.filter(s => s.id !== id)
      if (currentSessionId === id && filtered.length > 0) {
        setCurrentSessionId(filtered[0].id)
      } else if (filtered.length === 0) {
        const fallbackId = 'sess_' + Date.now()
        filtered.push({ id: fallbackId, title: 'New Conversation', messages: [] })
        setCurrentSessionId(fallbackId)
      }
      return filtered
    })
  }

  const handleUpdateSessionMessages = (sessionId, messages) => {
    setChatSessions(prev => prev.map(s => {
      if (s.id === sessionId) {
        let title = s.title
        const firstUserMsg = messages.find(m => m.role === 'user')
        if (firstUserMsg && (s.title === 'New Conversation' || s.title === 'Enterprise Knowledge Query' || !s.title)) {
          title = firstUserMsg.content.slice(0, 28) + (firstUserMsg.content.length > 28 ? '...' : '')
        }
        return { ...s, title, messages }
      }
      return s
    }))
  }

  // Full-Screen ChatGPT View Mode
  if (activeView === 'chat') {
    const currentSession = chatSessions.find(s => s.id === currentSessionId) || { id: currentSessionId, messages: [] }
    return (
      <div className="flex h-screen w-screen overflow-hidden bg-[#0B0F19] text-slate-100 font-sans relative">
        <ChatSidebar
          onBackToMain={() => setActiveView('dashboard')}
          onNewChat={handleNewChat}
          sessions={chatSessions}
          currentSessionId={currentSessionId}
          onSelectSession={handleSelectSession}
          onDeleteSession={handleDeleteSession}
          user={user}
          onOpenAuth={() => setIsAuthOpen(true)}
        />
        <main className="flex-1 h-full overflow-hidden relative z-10">
          <ChatInterface
            user={user}
            currentSession={currentSession}
            onUpdateSessionMessages={handleUpdateSessionMessages}
            onNewChat={handleNewChat}
          />
        </main>

        <AuthModal 
          isOpen={isAuthOpen}
          onClose={() => setIsAuthOpen(false)}
          onAuthSuccess={handleAuthSuccess}
        />
      </div>
    )
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#0B0F19] text-slate-100 font-sans relative">
      {/* Ambient background glows */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-indigo-600/20 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-5%] w-[40%] h-[40%] rounded-full bg-purple-600/20 blur-[120px] pointer-events-none" />

      <Sidebar 
        activeView={activeView} 
        setActiveView={setActiveView} 
        user={user}
        onOpenAuth={() => setIsAuthOpen(true)}
      />
      
      <main className="flex-1 flex flex-col h-full bg-transparent border-l border-white/5 overflow-hidden relative z-10">
        <header className="h-20 flex items-center justify-between px-8 glass-header shrink-0">
          <h1 className="text-2xl font-bold glow-text">
            {activeView === 'dashboard'   && 'Analytics Dashboard'}
            {activeView === 'classifier'  && '🧠 ML Expense Classifier'}
            {activeView === 'workflow'    && 'Workflow Builder'}
            {activeView === 'integration' && 'Enterprise API Hub'}
            {activeView === 'security'   && '🔐 Enterprise Security'}
            {activeView === 'performance'&& '⚡ Performance & Cache'}
            {activeView === 'settings'   && '⚙️ Settings'}
          </h1>
          <div className="flex items-center gap-3">
            <button 
              onClick={() => setIsAuthOpen(true)}
              className="px-4 py-2 bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 border border-indigo-500/30 rounded-xl text-xs font-semibold transition-colors flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"></path></svg>
              {user ? `Account (${user.username})` : 'Register / Login'}
            </button>
            <NotificationBell />
          </div>
        </header>
        
        <div className="flex-1 overflow-auto p-8 scroll-smooth relative z-10">
          {activeView === 'dashboard'   && <Dashboard />}
          {activeView === 'classifier'  && <ClassifierPanel />}
          {activeView === 'workflow'    && <WorkflowBuilder />}
          {activeView === 'integration' && <IntegrationPanel />}
          {activeView === 'security'   && <SecurityDashboard />}
          {activeView === 'performance'&& <PerformanceDashboard />}
          {activeView === 'settings'   && <SettingsPage />}
        </div>
      </main>

      <AuthModal 
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        onAuthSuccess={handleAuthSuccess}
      />
    </div>
  )
}

export default App
