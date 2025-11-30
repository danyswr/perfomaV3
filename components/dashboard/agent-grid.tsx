"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { ScrollArea } from "@/components/ui/scroll-area"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Bot, Trash2, Pause, Play, Clock, Cpu, HardDrive, MoreVertical, Terminal, Maximize2, Activity, Eye, Plus, Wifi, Timer } from "lucide-react"
import { useAgents } from "@/hooks/use-agents"
import type { Agent } from "@/lib/types"
import { AnimatedProgress, LoadingDots, PulseRing, SpinnerProgress } from "@/components/ui/animated-progress"
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, Area, AreaChart } from "recharts"

export function AgentGrid() {
  const { agents, addAgent, removeAgent, pauseAgent, resumeAgent, loading } = useAgents()
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
  const [isDetailOpen, setIsDetailOpen] = useState(false)

  const visibleAgents = agents.slice(0, 9)
  const hasMoreAgents = agents.length > 9

  const handleViewDetails = (agent: Agent) => {
    setSelectedAgent(agent)
    setIsDetailOpen(true)
  }

  const handleAddAgent = async () => {
    await addAgent()
  }

  return (
    <Card className="border-border h-full flex flex-col">
      <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0 px-4 pt-3">
        <div className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-primary" />
          <CardTitle className="text-base font-medium">Active Agents</CardTitle>
          <Badge variant="secondary" className="ml-1 text-xs px-1.5 h-5">
            {agents.length}/10
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            className="h-7 text-xs gap-1.5 bg-transparent"
            onClick={handleAddAgent}
            disabled={loading || agents.length >= 10}
          >
            {loading ? (
              <SpinnerProgress size={12} />
            ) : (
              <Plus className="w-3.5 h-3.5" />
            )}
            Add Agent
          </Button>
          {hasMoreAgents && (
            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" size="sm" className="h-7 text-xs gap-1.5 bg-transparent">
                  <Maximize2 className="w-3.5 h-3.5" />
                  View All ({agents.length})
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-4xl h-[80vh] flex flex-col p-0 gap-0">
                <DialogHeader className="p-6 pb-2">
                  <DialogTitle className="flex items-center gap-2">
                    <Bot className="w-5 h-5" /> All Deployed Agents
                  </DialogTitle>
                  <DialogDescription>Managing {agents.length} active autonomous agents.</DialogDescription>
                </DialogHeader>
                <div className="flex-1 overflow-hidden p-6 pt-2">
                  <ScrollArea className="h-full pr-4">
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 pb-4">
                      {agents.map((agent) => (
                        <AgentCard
                          key={agent.id}
                          agent={agent}
                          compact={true}
                          onPause={() => pauseAgent(agent.id)}
                          onResume={() => resumeAgent(agent.id)}
                          onRemove={() => removeAgent(agent.id)}
                        />
                      ))}
                    </div>
                  </ScrollArea>
                </div>
              </DialogContent>
            </Dialog>
          )}
        </div>
      </CardHeader>

      <CardContent className="flex-1 min-h-0 px-4 pb-4">
        {agents.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-[160px] text-muted-foreground border border-dashed rounded-md bg-muted/5">
            <Bot className="w-10 h-10 mb-2 opacity-20" />
            <p className="text-sm font-medium">No agents deployed</p>
            <p className="text-xs mt-1">Start a mission to deploy agents</p>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {visibleAgents.map((agent) => (
                <AgentCard
                  key={agent.id}
                  agent={agent}
                  compact={true}
                  onPause={() => pauseAgent(agent.id)}
                  onResume={() => resumeAgent(agent.id)}
                  onRemove={() => removeAgent(agent.id)}
                  onViewDetails={() => handleViewDetails(agent)}
                />
              ))}
            </div>
            {hasMoreAgents && (
              <div
                className="text-center p-2 border border-dashed rounded-md bg-muted/5 cursor-pointer hover:bg-muted/10 transition-colors"
                onClick={() => setIsDialogOpen(true)}
              >
                <p className="text-xs text-muted-foreground">
                  + {agents.length - 9} more agents running. Click to view all.
                </p>
              </div>
            )}
          </div>
        )}
      </CardContent>
      
      <AgentDetailDialog 
        agent={selectedAgent}
        open={isDetailOpen}
        onOpenChange={setIsDetailOpen}
      />
    </Card>
  )
}

interface AgentCardProps {
  agent: Agent
  compact?: boolean
  onPause: () => void
  onResume: () => void
  onRemove: () => void
  onViewDetails?: () => void
}

function AgentCard({ agent, compact, onPause, onResume, onRemove, onViewDetails }: AgentCardProps) {
  const [displayTime, setDisplayTime] = useState(agent.executionTime)
  
  useEffect(() => {
    setDisplayTime(agent.executionTime)
  }, [agent.executionTime])

  useEffect(() => {
    if (agent.status !== "running" && agent.status !== "break") {
      return
    }
    
    const parseTime = (timeStr: string): number => {
      const parts = timeStr.split(':').map(Number)
      if (parts.length === 3) {
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
      } else if (parts.length === 2) {
        return parts[0] * 60 + parts[1]
      }
      return 0
    }
    
    const formatSeconds = (totalSeconds: number): string => {
      const hrs = Math.floor(totalSeconds / 3600)
      const mins = Math.floor((totalSeconds % 3600) / 60)
      const secs = totalSeconds % 60
      
      if (hrs > 0) {
        return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
      }
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }
    
    let baseSeconds = parseTime(agent.executionTime)
    
    const interval = setInterval(() => {
      baseSeconds += 1
      setDisplayTime(formatSeconds(baseSeconds))
    }, 1000)
    
    return () => clearInterval(interval)
  }, [agent.status, agent.executionTime])

  const statusColors: Record<string, string> = {
    idle: "bg-muted text-muted-foreground border-border",
    running: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
    paused: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20",
    error: "bg-red-500/10 text-red-500 border-red-500/20",
    break: "bg-blue-500/10 text-blue-500 border-blue-500/20",
  }

  const indicatorColors: Record<string, string> = {
    idle: "bg-muted-foreground",
    running: "bg-emerald-500",
    paused: "bg-yellow-500",
    error: "bg-red-500",
    break: "bg-blue-500",
  }

  const isBreak = agent.status === "break"
  const isRunning = agent.status === "running"

  return (
    <div
      className={`group relative rounded-lg border p-2.5 transition-all hover:shadow-sm ${
        isBreak ? "border-blue-500/30 bg-blue-500/5" :
        isRunning ? "border-primary/20 bg-primary/5" : "border-border bg-card"
      }`}
    >
      <div className="flex items-center justify-between mb-1.5">
        <div className="flex items-center gap-2">
          <div className="relative">
            <Bot className="w-5 h-5 p-0.5 rounded bg-background border text-muted-foreground" />
            <div
              className={`absolute -top-0.5 -right-0.5 w-1.5 h-1.5 rounded-full border border-background ${
                indicatorColors[agent.status] || "bg-gray-400"
              }`}
            />
          </div>
          <div className="flex flex-col leading-none gap-0">
            <span className="font-semibold text-sm">Agent-{agent.id}</span>
            <span className={`text-[8px] uppercase font-mono ${
              isBreak ? "text-blue-500" : "text-muted-foreground"
            }`}>
              {isBreak ? "BREAK" : agent.status}
            </span>
          </div>
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-5 w-5 -mr-1">
              <MoreVertical className="w-3 h-3 text-muted-foreground" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-32">
            {onViewDetails && (
              <DropdownMenuItem onClick={onViewDetails} className="text-xs">
                <Eye className="w-3 h-3 mr-1.5" /> Details
              </DropdownMenuItem>
            )}
            {agent.status === "running" ? (
              <DropdownMenuItem onClick={onPause} className="text-xs">
                <Pause className="w-3 h-3 mr-1.5" /> Pause
              </DropdownMenuItem>
            ) : agent.status === "paused" ? (
              <DropdownMenuItem onClick={onResume} className="text-xs">
                <Play className="w-3 h-3 mr-1.5" /> Resume
              </DropdownMenuItem>
            ) : null}
            <DropdownMenuItem onClick={onRemove} className="text-xs text-destructive">
              <Trash2 className="w-3 h-3 mr-1.5" /> Terminate
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <div className="mb-1.5 p-1 rounded bg-black/80 font-mono text-[9px] text-green-400 border border-border/50 flex items-center gap-1 overflow-hidden min-w-0">
        <Terminal className="w-2.5 h-2.5 text-muted-foreground shrink-0" />
        <span className="opacity-90 line-clamp-1 min-w-0 truncate group-hover:truncate-none group-hover:whitespace-nowrap animate-scroll-text" style={{
          display: "inline-block"
        }}>
          {agent.lastCommand}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-1 mb-1.5">
        <MetricItem icon={Cpu} label="CPU" value={`${agent.cpuUsage}%`} />
        <MetricItem icon={HardDrive} label="MEM" value={`${agent.memoryUsage}MB`} />
        <MetricItem icon={Activity} label="PROG" value={`${agent.progress}%`} />
      </div>

      <div className={`p-1.5 rounded border ${
        isBreak ? "bg-blue-500/5 border-blue-500/20" : "bg-muted/30 border-border/30"
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1">
            <Timer className={`w-3 h-3 ${isBreak ? "text-blue-500" : "text-primary"}`} />
            <span className="text-[9px] text-muted-foreground">
              {isBreak ? "Break" : "Execution Time"}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <span className={`text-sm font-mono font-bold ${isBreak ? "text-blue-500" : "text-primary"}`}>
              {displayTime}
            </span>
            {isRunning && <PulseRing size="sm" className="ml-0.5" />}
            {isBreak && (
              <Badge variant="outline" className="text-[8px] px-1 py-0 h-4 bg-blue-500/10 text-blue-500 border-blue-500/30">
                Waiting
              </Badge>
            )}
          </div>
        </div>
        {isBreak && agent.breakReason && (
          <p className="text-[8px] text-blue-400 mt-1 truncate">{agent.breakReason}</p>
        )}
      </div>
    </div>
  )
}

function MetricItem({ icon: Icon, label, value }: { icon: any; label: string; value: string }) {
  return (
    <div className="flex flex-col items-center justify-center p-0.5 rounded bg-muted/30 border border-border/30">
      <Icon className="w-2.5 h-2.5 text-muted-foreground mb-0.5" />
      <span className="text-[7px] text-muted-foreground uppercase leading-none">{label}</span>
      <span className="text-[8px] font-mono font-medium leading-none mt-0.5">{value}</span>
    </div>
  )
}

interface AgentDetailDialogProps {
  agent: Agent | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

interface InstructionHistoryItem {
  id: number
  instruction: string
  instruction_type: string
  timestamp: string
  model_name: string
}

function AgentDetailDialog({ agent, open, onOpenChange }: AgentDetailDialogProps) {
  const [cpuHistory, setCpuHistory] = useState<{value: number, time: string}[]>([])
  const [memoryHistory, setMemoryHistory] = useState<{value: number, time: string}[]>([])
  const [diskHistory, setDiskHistory] = useState<{value: number, time: string}[]>([])
  const [networkHistory, setNetworkHistory] = useState<{value: number, time: string}[]>([])
  const [displayTime, setDisplayTime] = useState(agent?.executionTime || "00:00")
  const [instructionHistory, setInstructionHistory] = useState<InstructionHistoryItem[]>([])
  const [loadingHistory, setLoadingHistory] = useState(false)

  useEffect(() => {
    if (!agent || !open) return

    const generateData = () => {
      const now = new Date()
      const time = now.toLocaleTimeString()
      
      setCpuHistory(prev => {
        const newData = [...prev, { value: Math.max(0, Math.min(100, agent.cpuUsage + Math.random() * 10 - 5)), time }]
        return newData.slice(-30)
      })
      
      setMemoryHistory(prev => {
        const newData = [...prev, { value: Math.max(0, agent.memoryUsage + Math.random() * 20 - 10), time }]
        return newData.slice(-30)
      })

      setDiskHistory(prev => {
        const newData = [...prev, { value: Math.max(0, Math.min(100, 30 + Math.random() * 20)), time }]
        return newData.slice(-30)
      })

      setNetworkHistory(prev => {
        const newData = [...prev, { value: Math.max(0, 100 + Math.random() * 200), time }]
        return newData.slice(-30)
      })
    }

    generateData()
    const interval = setInterval(generateData, 2000)
    return () => clearInterval(interval)
  }, [agent, open])

  useEffect(() => {
    if (!agent || !open) return

    const fetchHistory = async () => {
      setLoadingHistory(true)
      try {
        const res = await fetch(`/api/agents/${agent.id}/history`)
        if (res.ok) {
          const data = await res.json()
          setInstructionHistory(data.history || [])
        }
      } catch {
      } finally {
        setLoadingHistory(false)
      }
    }

    fetchHistory()
    const interval = setInterval(fetchHistory, 5000)
    return () => clearInterval(interval)
  }, [agent, open])

  useEffect(() => {
    if (agent) {
      setDisplayTime(agent.executionTime)
    }
  }, [agent?.executionTime])

  useEffect(() => {
    if (!agent || !open || agent.status !== "running") return
    
    const parseTime = (timeStr: string): number => {
      const parts = timeStr.split(':').map(Number)
      if (parts.length === 3) {
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
      } else if (parts.length === 2) {
        return parts[0] * 60 + parts[1]
      }
      return 0
    }
    
    const formatSeconds = (totalSeconds: number): string => {
      const hrs = Math.floor(totalSeconds / 3600)
      const mins = Math.floor((totalSeconds % 3600) / 60)
      const secs = totalSeconds % 60
      return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }
    
    let baseSeconds = parseTime(agent.executionTime)
    
    const interval = setInterval(() => {
      baseSeconds += 1
      setDisplayTime(formatSeconds(baseSeconds))
    }, 1000)
    
    return () => clearInterval(interval)
  }, [agent, open, agent?.status, agent?.executionTime])

  const getStatusColor = (value: number) => {
    if (value >= 80) return "text-destructive"
    if (value >= 60) return "text-chart-3"
    return "text-primary"
  }

  const getProgressColor = (value: number) => {
    if (value >= 80) return "bg-destructive"
    if (value >= 60) return "bg-chart-3"
    return "bg-primary"
  }

  if (!agent) return null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Bot className="w-5 h-5" />
            Agent-{agent.id} Details
            <Badge variant={agent.status === "running" ? "default" : "secondary"} className="ml-2">
              {agent.status}
            </Badge>
          </DialogTitle>
          <DialogDescription>
            Real-time monitoring and resource usage for this agent.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="p-3 rounded-lg bg-primary/10 border border-primary/20">
              <div className="flex items-center gap-2 mb-1">
                <Timer className="w-4 h-4 text-primary" />
                <span className="text-xs text-muted-foreground">Execution Time</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-2xl font-mono font-bold text-primary">
                  {displayTime}
                </span>
                {agent.status === "running" && <PulseRing size="sm" />}
              </div>
            </div>
            <div className="p-3 rounded-lg bg-muted/30 border">
              <div className="flex items-center gap-2 mb-1">
                <Cpu className="w-4 h-4 text-muted-foreground" />
                <span className="text-xs text-muted-foreground">CPU Usage</span>
              </div>
              <span className={`text-lg font-mono font-semibold ${getStatusColor(agent.cpuUsage)}`}>{agent.cpuUsage}%</span>
              <Progress value={agent.cpuUsage} className={`h-1 mt-1 ${getProgressColor(agent.cpuUsage)}`} />
            </div>
            <div className="p-3 rounded-lg bg-muted/30 border">
              <div className="flex items-center gap-2 mb-1">
                <HardDrive className="w-4 h-4 text-muted-foreground" />
                <span className="text-xs text-muted-foreground">Memory</span>
              </div>
              <span className="text-lg font-mono font-semibold text-chart-2">{agent.memoryUsage}MB</span>
              <Progress value={Math.min(100, agent.memoryUsage / 5)} className="h-1 mt-1 bg-chart-2" />
            </div>
            <div className="p-3 rounded-lg bg-muted/30 border">
              <div className="flex items-center gap-2 mb-1">
                <Wifi className="w-4 h-4 text-muted-foreground" />
                <span className="text-xs text-muted-foreground">Network</span>
              </div>
              <span className="text-lg font-mono font-semibold text-chart-4">{networkHistory.length > 0 ? Math.round(networkHistory[networkHistory.length - 1].value) : 0}KB/s</span>
              <Progress value={Math.min(100, (networkHistory.length > 0 ? networkHistory[networkHistory.length - 1].value : 0) / 10)} className="h-1 mt-1 bg-chart-4" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="p-3 rounded-lg border bg-card">
              <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                <Cpu className="w-4 h-4 text-blue-500" />
                CPU Usage History
              </h4>
              <div className="h-32" style={{ minWidth: 200, minHeight: 100 }}>
                <ResponsiveContainer width="100%" height="100%" minWidth={200} minHeight={100}>
                  <AreaChart data={cpuHistory}>
                    <defs>
                      <linearGradient id="agentCpuGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="time" hide />
                    <YAxis domain={[0, 100]} hide />
                    <Tooltip 
                      contentStyle={{ background: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px', fontSize: '12px' }}
                      labelStyle={{ color: 'hsl(var(--foreground))' }}
                      formatter={(value: number) => [`${value.toFixed(1)}%`, 'CPU']}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="value" 
                      stroke="#3b82f6" 
                      fill="url(#agentCpuGradient)" 
                      strokeWidth={2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="p-3 rounded-lg border bg-card">
              <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                <HardDrive className="w-4 h-4 text-emerald-500" />
                Memory Usage History
              </h4>
              <div className="h-32" style={{ minWidth: 200, minHeight: 100 }}>
                <ResponsiveContainer width="100%" height="100%" minWidth={200} minHeight={100}>
                  <AreaChart data={memoryHistory}>
                    <defs>
                      <linearGradient id="agentMemGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="time" hide />
                    <YAxis domain={[0, 'auto']} hide />
                    <Tooltip 
                      contentStyle={{ background: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px', fontSize: '12px' }}
                      labelStyle={{ color: 'hsl(var(--foreground))' }}
                      formatter={(value: number) => [`${value.toFixed(1)}MB`, 'Memory']}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="value" 
                      stroke="#10b981" 
                      fill="url(#agentMemGradient)" 
                      strokeWidth={2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="p-3 rounded-lg border bg-card">
              <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                <HardDrive className="w-4 h-4 text-orange-500" />
                Disk I/O History
              </h4>
              <div className="h-32" style={{ minWidth: 200, minHeight: 100 }}>
                <ResponsiveContainer width="100%" height="100%" minWidth={200} minHeight={100}>
                  <AreaChart data={diskHistory}>
                    <defs>
                      <linearGradient id="agentDiskGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#f97316" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#f97316" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="time" hide />
                    <YAxis domain={[0, 100]} hide />
                    <Tooltip 
                      contentStyle={{ background: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px', fontSize: '12px' }}
                      labelStyle={{ color: 'hsl(var(--foreground))' }}
                      formatter={(value: number) => [`${value.toFixed(1)}%`, 'Disk I/O']}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="value" 
                      stroke="#f97316" 
                      fill="url(#agentDiskGradient)" 
                      strokeWidth={2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="p-3 rounded-lg border bg-card">
              <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                <Wifi className="w-4 h-4 text-purple-500" />
                Network Activity
              </h4>
              <div className="h-32" style={{ minWidth: 200, minHeight: 100 }}>
                <ResponsiveContainer width="100%" height="100%" minWidth={200} minHeight={100}>
                  <AreaChart data={networkHistory}>
                    <defs>
                      <linearGradient id="agentNetGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#a855f7" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#a855f7" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="time" hide />
                    <YAxis domain={[0, 'auto']} hide />
                    <Tooltip 
                      contentStyle={{ background: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: '8px', fontSize: '12px' }}
                      labelStyle={{ color: 'hsl(var(--foreground))' }}
                      formatter={(value: number) => [`${value.toFixed(1)}KB/s`, 'Network']}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="value" 
                      stroke="#a855f7" 
                      fill="url(#agentNetGradient)" 
                      strokeWidth={2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <div className="p-3 rounded-lg border bg-black/80">
            <h4 className="text-xs font-medium mb-2 text-green-400 flex items-center gap-2">
              <Terminal className="w-3 h-3" />
              Last Command
            </h4>
            <pre className="text-xs font-mono text-green-400/80 whitespace-pre-wrap">
              {agent.lastCommand}
            </pre>
          </div>

          <div className="p-3 rounded-lg border bg-card">
            <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
              <Clock className="w-4 h-4 text-primary" />
              Instruction History
              <Badge variant="outline" className="text-xs ml-auto">
                {instructionHistory.length} instructions
              </Badge>
            </h4>
            <ScrollArea className="h-40">
              {loadingHistory ? (
                <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                  Loading history...
                </div>
              ) : instructionHistory.length === 0 ? (
                <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                  No instructions yet
                </div>
              ) : (
                <div className="space-y-2 pr-2">
                  {instructionHistory.slice().reverse().map((item) => (
                    <div 
                      key={item.id} 
                      className={`p-2 rounded border text-xs ${
                        item.instruction_type === 'command' 
                          ? 'bg-emerald-500/10 border-emerald-500/20' 
                          : item.instruction_type === 'decision'
                          ? 'bg-amber-500/10 border-amber-500/20'
                          : 'bg-blue-500/10 border-blue-500/20'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <Badge 
                          variant="outline" 
                          className={`text-[10px] ${
                            item.instruction_type === 'command' ? 'text-emerald-400' : 
                            item.instruction_type === 'decision' ? 'text-amber-400' : 'text-blue-400'
                          }`}
                        >
                          {item.instruction_type}
                        </Badge>
                        <span className="text-[10px] text-muted-foreground">
                          {new Date(item.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      <p className="font-mono text-[11px] line-clamp-2 text-muted-foreground">
                        {item.instruction}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 rounded-lg border bg-muted/30">
              <div className="text-xs text-muted-foreground mb-1">Target</div>
              <div className="text-sm font-medium truncate">{agent.target || "Not set"}</div>
            </div>
            <div className="p-3 rounded-lg border bg-muted/30">
              <div className="text-xs text-muted-foreground mb-1">Category</div>
              <div className="text-sm font-medium">{agent.category || "domain"}</div>
            </div>
            <div className="p-3 rounded-lg border bg-muted/30">
              <div className="text-xs text-muted-foreground mb-1">Progress</div>
              <div className="text-sm font-medium">{agent.progress}%</div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
