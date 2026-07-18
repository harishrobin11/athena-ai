import { useState } from 'react'
import Sidebar from './components/Sidebar'
import ChatInterface from './components/ChatInterface'
import WorkflowBuilder from './components/WorkflowBuilder'
import IntegrationPanel from './components/IntegrationPanel'

function App() {
  const [activeView, setActiveView] = useState('chat')

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 font-sans">
      <Sidebar activeView={activeView} setActiveView={setActiveView} />
      
      <main className="flex-1 flex flex-col h-full bg-slate-900 border-l border-slate-800 shadow-2xl overflow-hidden relative">
        <header className="h-16 flex items-center px-6 border-b border-slate-800 bg-slate-900/50 backdrop-blur-sm shrink-0">
          <h1 className="text-xl font-semibold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent drop-shadow-sm">
            {activeView === 'chat' && 'Athena Intelligence'}
            {activeView === 'workflow' && 'Workflow Builder'}
            {activeView === 'integration' && 'Enterprise API Hub'}
          </h1>
        </header>
        
        <div className="flex-1 overflow-auto p-6 scroll-smooth">
          {activeView === 'chat' && <ChatInterface />}
          {activeView === 'workflow' && <WorkflowBuilder />}
          {activeView === 'integration' && <IntegrationPanel />}
        </div>
      </main>
    </div>
  )
}

export default App
