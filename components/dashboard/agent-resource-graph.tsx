"use client"

import { useState, useEffect } from "react"
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from "recharts"
import { Cpu, HardDrive } from "lucide-react"
import type { ResourceDataPoint } from "@/lib/types"

interface AgentResourceGraphProps {
  agentId: string
  cpuUsage: number
  memoryUsage: number
  compact?: boolean
}

export function AgentResourceGraph({ agentId, cpuUsage, memoryUsage, compact = false }: AgentResourceGraphProps) {
  const getInitialData = () => {
    const now = new Date()
    return [{ time: now.toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" }), value: 0 }]
  }
  const [cpuHistory, setCpuHistory] = useState<ResourceDataPoint[]>(getInitialData)
  const [memoryHistory, setMemoryHistory] = useState<ResourceDataPoint[]>(getInitialData)

  useEffect(() => {
    const now = new Date()
    const time = now.toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" })
    
    setCpuHistory(prev => {
      const newValue = Math.max(0, Math.min(100, cpuUsage + (Math.random() * 10 - 5)))
      const newData = [...prev, { time, value: newValue }]
      return newData.slice(-20)
    })

    setMemoryHistory(prev => {
      const newValue = Math.max(0, memoryUsage + (Math.random() * 20 - 10))
      const newData = [...prev, { time, value: newValue }]
      return newData.slice(-20)
    })
  }, [cpuUsage, memoryUsage])

  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date()
      const time = now.toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" })
      
      setCpuHistory(prev => {
        const lastValue = prev[prev.length - 1]?.value || cpuUsage
        const newValue = Math.max(0, Math.min(100, lastValue + (Math.random() * 6 - 3)))
        const newData = [...prev, { time, value: newValue }]
        return newData.slice(-20)
      })

      setMemoryHistory(prev => {
        const lastValue = prev[prev.length - 1]?.value || memoryUsage
        const newValue = Math.max(0, lastValue + (Math.random() * 10 - 5))
        const newData = [...prev, { time, value: newValue }]
        return newData.slice(-20)
      })
    }, 2000)

    return () => clearInterval(interval)
  }, [cpuUsage, memoryUsage])

  if (compact) {
    return (
      <div className="grid grid-cols-2 gap-1">
        <div className="rounded bg-muted/30 border border-border/30 p-1">
          <div className="flex items-center gap-1 mb-0.5">
            <Cpu className="w-2.5 h-2.5 text-blue-500" />
            <span className="text-[7px] text-muted-foreground uppercase">CPU</span>
            <span className="text-[8px] font-mono ml-auto">{Math.round(cpuHistory[cpuHistory.length - 1]?.value || cpuUsage)}%</span>
          </div>
          <div className="h-8" style={{ minWidth: 50, minHeight: 20 }}>
            <ResponsiveContainer width="100%" height="100%" minWidth={50} minHeight={20}>
              <AreaChart data={cpuHistory}>
                <defs>
                  <linearGradient id={`cpuGradient-${agentId}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <Area 
                  type="monotone" 
                  dataKey="value" 
                  stroke="#3b82f6" 
                  fill={`url(#cpuGradient-${agentId})`}
                  strokeWidth={1}
                  isAnimationActive={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded bg-muted/30 border border-border/30 p-1">
          <div className="flex items-center gap-1 mb-0.5">
            <HardDrive className="w-2.5 h-2.5 text-emerald-500" />
            <span className="text-[7px] text-muted-foreground uppercase">MEM</span>
            <span className="text-[8px] font-mono ml-auto">{Math.round(memoryHistory[memoryHistory.length - 1]?.value || memoryUsage)}MB</span>
          </div>
          <div className="h-8" style={{ minWidth: 50, minHeight: 20 }}>
            <ResponsiveContainer width="100%" height="100%" minWidth={50} minHeight={20}>
              <AreaChart data={memoryHistory}>
                <defs>
                  <linearGradient id={`memGradient-${agentId}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <Area 
                  type="monotone" 
                  dataKey="value" 
                  stroke="#10b981" 
                  fill={`url(#memGradient-${agentId})`}
                  strokeWidth={1}
                  isAnimationActive={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="p-2 rounded-lg border bg-card">
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 text-blue-500" />
            <span className="text-xs font-medium">CPU Usage</span>
          </div>
          <span className="text-xs font-mono text-blue-500">{Math.round(cpuHistory[cpuHistory.length - 1]?.value || cpuUsage)}%</span>
        </div>
        <div className="h-16" style={{ minWidth: 100, minHeight: 40 }}>
          <ResponsiveContainer width="100%" height="100%" minWidth={100} minHeight={40}>
            <AreaChart data={cpuHistory}>
              <defs>
                <linearGradient id={`cpuGradientFull-${agentId}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <XAxis dataKey="time" hide />
              <YAxis domain={[0, 100]} hide />
              <Tooltip 
                contentStyle={{ 
                  background: 'hsl(var(--card))', 
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '6px',
                  fontSize: '11px'
                }}
                labelStyle={{ color: 'hsl(var(--foreground))' }}
                formatter={(value: number) => [`${Math.round(value)}%`, 'CPU']}
              />
              <Area 
                type="monotone" 
                dataKey="value" 
                stroke="#3b82f6" 
                fill={`url(#cpuGradientFull-${agentId})`}
                strokeWidth={2}
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="p-2 rounded-lg border bg-card">
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-1.5">
            <HardDrive className="w-3.5 h-3.5 text-emerald-500" />
            <span className="text-xs font-medium">Memory Usage</span>
          </div>
          <span className="text-xs font-mono text-emerald-500">{Math.round(memoryHistory[memoryHistory.length - 1]?.value || memoryUsage)}MB</span>
        </div>
        <div className="h-16" style={{ minWidth: 100, minHeight: 40 }}>
          <ResponsiveContainer width="100%" height="100%" minWidth={100} minHeight={40}>
            <AreaChart data={memoryHistory}>
              <defs>
                <linearGradient id={`memGradientFull-${agentId}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <XAxis dataKey="time" hide />
              <YAxis domain={[0, 'auto']} hide />
              <Tooltip 
                contentStyle={{ 
                  background: 'hsl(var(--card))', 
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '6px',
                  fontSize: '11px'
                }}
                labelStyle={{ color: 'hsl(var(--foreground))' }}
                formatter={(value: number) => [`${Math.round(value)}MB`, 'Memory']}
              />
              <Area 
                type="monotone" 
                dataKey="value" 
                stroke="#10b981" 
                fill={`url(#memGradientFull-${agentId})`}
                strokeWidth={2}
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
