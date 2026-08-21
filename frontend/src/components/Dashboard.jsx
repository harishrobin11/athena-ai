import React, { useState, useEffect } from 'react'
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, AreaChart, Area
} from 'recharts'
import { Activity, Users, Database, Zap, Wifi, WifiOff } from 'lucide-react'

// Mock Data
const tokenData = [
  { name: 'Finance', tokens: 4000 },
  { name: 'Legal', tokens: 3000 },
  { name: 'HR', tokens: 2000 },
  { name: 'Engineering', tokens: 2780 },
  { name: 'Sales', tokens: 1890 },
]

const workflowData = [
  { name: 'Successful', value: 85 },
  { name: 'Failed', value: 15 },
]

const COLORS = ['#10b981', '#f43f5e']

export default function Dashboard() {
  const [latencyData, setLatencyData] = useState([])
  const [kpis, setKpis] = useState({
    activeAgents: 24,
    memoryGb: 4.2,
    latencyMs: 112,
    totalExecutions: 12403
  })
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    let ws = null
    let reconnectTimeout = null
    let isUnmounted = false

    const connect = () => {
      if (isUnmounted) return
      
      const baseUrl = import.meta.env.VITE_API_URL || window.location.origin
      let wsUrl = ""
      try {
        const url = new URL(baseUrl)
        const protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
        wsUrl = `${protocol}//${url.host}/api/v1/metrics/live`
      } catch (e) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        wsUrl = `${protocol}//${window.location.host}/api/v1/metrics/live`
      }
      
      try {
        ws = new WebSocket(wsUrl)

        ws.onopen = () => {
          if (!isUnmounted) {
            setIsConnected(true)
          }
        }

        ws.onmessage = (event) => {
          if (isUnmounted) return
          try {
            const data = JSON.parse(event.data)
            setKpis({
              activeAgents: data.activeAgents,
              memoryGb: data.memoryGb,
              latencyMs: data.latencyMs,
              totalExecutions: data.totalExecutions
            })

            // Update time series
            const now = new Date()
            const timeString = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`
            
            setLatencyData(prev => {
              const newData = [...prev, { time: timeString, ms: data.latencyMs }]
              if (newData.length > 20) newData.shift() // Keep last 20 points
              return newData
            })
          } catch (e) {
            console.error('Failed to parse WebSocket metrics:', e)
          }
        }

        ws.onerror = () => {
          if (!isUnmounted) {
            setIsConnected(false)
          }
        }

        ws.onclose = () => {
          if (!isUnmounted) {
            setIsConnected(false)
            // Schedule reconnection attempt in 3 seconds
            reconnectTimeout = setTimeout(connect, 3000)
          }
        }
      } catch (err) {
        console.error('WebSocket connection error:', err)
        if (!isUnmounted) {
          setIsConnected(false)
          reconnectTimeout = setTimeout(connect, 3000)
        }
      }
    }

    connect()

    return () => {
      isUnmounted = true
      if (reconnectTimeout) clearTimeout(reconnectTimeout)
      if (ws) ws.close()
    }
  }, [])


  return (
    <div className="max-w-7xl mx-auto space-y-6">
      
      {/* Header with Connection Status */}
      <div className="flex justify-between items-center glass-panel p-5">
        <h2 className="text-xl font-bold text-slate-100 tracking-tight">Live System Metrics</h2>
        <div className={`flex items-center gap-2 px-4 py-2 rounded-full text-xs font-bold border uppercase tracking-wider ${isConnected ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 shadow-[0_0_10px_rgba(52,211,153,0.2)]' : 'bg-rose-500/10 text-rose-400 border-rose-500/30'}`}>
          {isConnected ? <Wifi size={16} /> : <WifiOff size={16} />}
          {isConnected ? 'Live Connection' : 'Disconnected'}
        </div>
      </div>

      {/* Top Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {[
          { label: 'Active Agents', value: kpis.activeAgents, icon: Users, color: 'text-indigo-400', bg: 'bg-indigo-500/10 border-indigo-500/20' },
          { label: 'System Memory', value: `${kpis.memoryGb} GB`, icon: Database, color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' },
          { label: 'Avg Latency', value: `${kpis.latencyMs} ms`, icon: Activity, color: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/20' },
          { label: 'Total Executions', value: kpis.totalExecutions.toLocaleString(), icon: Zap, color: 'text-purple-400', bg: 'bg-purple-500/10 border-purple-500/20' },
        ].map((stat, i) => (
          <div key={i} className="glass-panel p-6 flex items-center gap-5 transition-transform hover:-translate-y-1 duration-300">
            <div className={`p-4 rounded-xl border ${stat.bg} ${stat.color} shadow-inner`}>
              <stat.icon size={28} />
            </div>
            <div>
              <p className="text-xs text-slate-400 font-bold uppercase tracking-widest">{stat.label}</p>
              <h3 className="text-3xl font-extrabold text-white mt-1 drop-shadow-md">{stat.value}</h3>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Token Usage Bar Chart */}
        <div className="glass-panel p-6 md:col-span-2 h-[420px] flex flex-col">
          <h3 className="text-base font-bold text-slate-200 mb-6 tracking-wide">Token Usage by Department</h3>
          <div className="flex-1 min-h-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={tokenData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff15" vertical={false} />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip 
                  cursor={{fill: '#ffffff0a'}}
                  contentStyle={{ backgroundColor: '#111827dd', borderColor: '#ffffff20', borderRadius: '12px', backdropFilter: 'blur(10px)', color: '#fff' }}
                  itemStyle={{ color: '#fff' }}
                />
                <Bar dataKey="tokens" fill="url(#barGradient)" radius={[6, 6, 0, 0]} />
                <defs>
                  <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#818cf8"/>
                    <stop offset="100%" stopColor="#4f46e5"/>
                  </linearGradient>
                </defs>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Workflow Success Rate Pie Chart */}
        <div className="glass-panel p-6 h-[420px] flex flex-col">
          <h3 className="text-base font-bold text-slate-200 mb-6 tracking-wide">Workflow Execution Rate</h3>
          <div className="flex-1 min-h-0 flex items-center justify-center relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={workflowData}
                  cx="50%"
                  cy="50%"
                  innerRadius={90}
                  outerRadius={120}
                  paddingAngle={6}
                  dataKey="value"
                  stroke="none"
                >
                  {workflowData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={index === 0 ? '#10b981' : '#f43f5e'} style={{ filter: 'drop-shadow(0 0 8px rgba(0,0,0,0.5))' }}/>
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: '#111827dd', borderColor: '#ffffff20', borderRadius: '12px', backdropFilter: 'blur(10px)', color: '#fff' }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none drop-shadow-lg">
              <span className="text-4xl font-extrabold text-emerald-400">85%</span>
              <span className="text-xs text-slate-300 font-medium uppercase tracking-widest mt-1">Success</span>
            </div>
          </div>
        </div>

        {/* API Latency Area Chart */}
        <div className="glass-panel p-6 md:col-span-3 h-80 flex flex-col">
          <h3 className="text-base font-bold text-slate-200 mb-6 tracking-wide">API Gateway Latency (ms)</h3>
          <div className="flex-1 min-h-0">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={latencyData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorMs" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#d946ef" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#d946ef" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff15" vertical={false} />
                <XAxis dataKey="time" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#111827dd', borderColor: '#ffffff20', borderRadius: '12px', backdropFilter: 'blur(10px)', color: '#fff' }}
                />
                <Area type="monotone" dataKey="ms" stroke="#d946ef" strokeWidth={4} fillOpacity={1} fill="url(#colorMs)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>
    </div>
  )
}
