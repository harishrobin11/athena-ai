import React from 'react'
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, AreaChart, Area
} from 'recharts'
import { Activity, Users, Database, Zap } from 'lucide-react'

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

const latencyData = [
  { time: '10:00', ms: 120 },
  { time: '10:05', ms: 132 },
  { time: '10:10', ms: 101 },
  { time: '10:15', ms: 140 },
  { time: '10:20', ms: 90 },
  { time: '10:25', ms: 110 },
]

const COLORS = ['#10b981', '#f43f5e']

export default function Dashboard() {
  return (
    <div className="max-w-7xl mx-auto space-y-6">
      
      {/* Top Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'Active Agents', value: '24', icon: Users, color: 'text-blue-400' },
          { label: 'System Memory', value: '4.2 GB', icon: Database, color: 'text-emerald-400' },
          { label: 'Avg Latency', value: '112 ms', icon: Activity, color: 'text-amber-400' },
          { label: 'Total Executions', value: '12,403', icon: Zap, color: 'text-violet-400' },
        ].map((stat, i) => (
          <div key={i} className="bg-slate-800 rounded-xl border border-slate-700 p-6 flex items-center gap-4 shadow-lg">
            <div className={`p-3 bg-slate-900 rounded-lg border border-slate-700 ${stat.color}`}>
              <stat.icon size={24} />
            </div>
            <div>
              <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">{stat.label}</p>
              <h3 className="text-2xl font-bold text-slate-100">{stat.value}</h3>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Token Usage Bar Chart */}
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 shadow-lg md:col-span-2 h-96 flex flex-col">
          <h3 className="text-sm font-semibold text-slate-200 mb-6">Token Usage by Department</h3>
          <div className="flex-1 min-h-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={tokenData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip 
                  cursor={{fill: '#1e293b'}}
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                />
                <Bar dataKey="tokens" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Workflow Success Rate Pie Chart */}
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 shadow-lg h-96 flex flex-col">
          <h3 className="text-sm font-semibold text-slate-200 mb-6">Workflow Execution Rate</h3>
          <div className="flex-1 min-h-0 flex items-center justify-center relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={workflowData}
                  cx="50%"
                  cy="50%"
                  innerRadius={80}
                  outerRadius={110}
                  paddingAngle={5}
                  dataKey="value"
                  stroke="none"
                >
                  {workflowData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-3xl font-bold text-emerald-400">85%</span>
              <span className="text-xs text-slate-400">Success</span>
            </div>
          </div>
        </div>

        {/* API Latency Area Chart */}
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 shadow-lg md:col-span-3 h-80 flex flex-col">
          <h3 className="text-sm font-semibold text-slate-200 mb-6">API Gateway Latency (ms)</h3>
          <div className="flex-1 min-h-0">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={latencyData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorMs" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis dataKey="time" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                />
                <Area type="monotone" dataKey="ms" stroke="#8b5cf6" strokeWidth={3} fillOpacity={1} fill="url(#colorMs)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>
    </div>
  )
}
