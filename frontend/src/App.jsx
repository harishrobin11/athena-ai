import { useState } from 'react'
import Sidebar from './components/Sidebar'
import ChatInterface from './components/ChatInterface'
import WorkflowBuilder from './components/WorkflowBuilder'
import IntegrationPanel from './components/IntegrationPanel'
import Dashboard from './components/Dashboard'
import NotificationBell from './components/NotificationBell'
import SecurityDashboard from './components/SecurityDashboard'
import PerformanceDashboard from './components/PerformanceDashboard'

function App() {
  const [activeView, setActiveView] = useState('dashboard')

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#0B0F19] text-slate-100 font-sans relative">
      {/* Ambient background glows */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-indigo-600/20 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-5%] w-[40%] h-[40%] rounded-full bg-purple-600/20 blur-[120px] pointer-events-none" />

      <Sidebar activeView={activeView} setActiveView={setActiveView} />
      
      <main className="flex-1 flex flex-col h-full bg-transparent border-l border-white/5 overflow-hidden relative z-10">
        <header className="h-20 flex items-center justify-between px-8 glass-header shrink-0">
          <h1 className="text-2xl font-bold glow-text">
            {activeView === 'dashboard'   && 'Analytics Dashboard'}
            {activeView === 'chat'        && 'Athena Intelligence'}
            {activeView === 'workflow'    && 'Workflow Builder'}
            {activeView === 'integration' && 'Enterprise API Hub'}
            {activeView === 'security'   && '🔐 Enterprise Security'}
            {activeView === 'performance'&& '⚡ Performance & Cache'}
          </h1>
          <div className="flex items-center gap-3">
            <NotificationBell />
          </div>
        </header>
        
        <div className="flex-1 overflow-auto p-8 scroll-smooth relative z-10">
          {activeView === 'dashboard'   && <Dashboard />}
          {activeView === 'chat'        && <ChatInterface />}
          {activeView === 'workflow'    && <WorkflowBuilder />}
          {activeView === 'integration' && <IntegrationPanel />}
          {activeView === 'security'   && <SecurityDashboard />}
          {activeView === 'performance'&& <PerformanceDashboard />}
        </div>
      </main>
    </div>
  )
}

export default App
