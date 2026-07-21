import { useState, useEffect } from 'react'
import Sidebar from './components/Sidebar'
import ChatInterface from './components/ChatInterface'
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

  useEffect(() => {
    const savedUser = localStorage.getItem('athena_user')
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser))
      } catch (e) {}
    }
  }, [])

  const handleAuthSuccess = (userData) => {
    setUser(userData)
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
            {activeView === 'chat'        && 'Athena Intelligence'}
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
          {activeView === 'chat'        && <ChatInterface user={user} />}
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
