"use client"

import type React from "react"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Cpu, MemoryStick, HardDrive, Wifi, Activity } from "lucide-react"
import { useResources } from "@/hooks/use-resources"
import { AreaChart, Area, XAxis, YAxis, ResponsiveContainer, Tooltip } from "recharts"

export function ResourceMonitor() {
  const { resources, history } = useResources()

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

  return (
    <Card className="border-border">
      <CardHeader className="flex flex-row items-center justify-between pb-4">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-primary" />
          <CardTitle className="text-lg">System Resources</CardTitle>
        </div>
        <Badge variant="outline" className="text-xs">
          Real-time
        </Badge>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Resource Bars */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <ResourceBar
            icon={Cpu}
            label="CPU"
            value={resources.cpu}
            unit="%"
            color={getProgressColor(resources.cpu)}
            textColor={getStatusColor(resources.cpu)}
          />
          <ResourceBar
            icon={MemoryStick}
            label="Memory"
            value={resources.memory}
            unit="%"
            color={getProgressColor(resources.memory)}
            textColor={getStatusColor(resources.memory)}
          />
          <ResourceBar
            icon={HardDrive}
            label="Disk I/O"
            value={resources.disk}
            unit="%"
            color={getProgressColor(resources.disk)}
            textColor={getStatusColor(resources.disk)}
          />
          <ResourceBar
            icon={Wifi}
            label="Network"
            value={resources.network}
            unit="KB/s"
            color="bg-chart-2"
            textColor="text-chart-2"
            max={1000}
          />
        </div>

        {/* Usage Chart */}
        <div className="h-[150px] mt-4" style={{ minWidth: 200, minHeight: 100 }}>
          <ResponsiveContainer width="100%" height="100%" minWidth={200} minHeight={100}>
            <AreaChart data={history}>
              <defs>
                <linearGradient id="cpuGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="oklch(0.72 0.19 160)" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="oklch(0.72 0.19 160)" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="memGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="oklch(0.65 0.18 250)" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="oklch(0.65 0.18 250)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="time"
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 10, fill: "oklch(0.65 0 0)" }}
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 10, fill: "oklch(0.65 0 0)" }}
                domain={[0, 100]}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "oklch(0.15 0.01 260)",
                  border: "1px solid oklch(0.25 0.01 260)",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
              />
              <Area
                type="monotone"
                dataKey="cpu"
                stroke="oklch(0.72 0.19 160)"
                fill="url(#cpuGradient)"
                strokeWidth={2}
              />
              <Area
                type="monotone"
                dataKey="memory"
                stroke="oklch(0.65 0.18 250)"
                fill="url(#memGradient)"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Legend */}
        <div className="flex justify-center gap-6 text-xs text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-0.5 rounded bg-primary" />
            <span>CPU</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-0.5 rounded bg-chart-2" />
            <span>Memory</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

interface ResourceBarProps {
  icon: React.ElementType
  label: string
  value: number
  unit: string
  color: string
  textColor: string
  max?: number
}

function formatNetworkValue(value: number): { display: string; unit: string } {
  if (value >= 1024 * 1024) {
    return { display: (value / (1024 * 1024)).toFixed(1), unit: "GB/s" }
  } else if (value >= 1024) {
    return { display: (value / 1024).toFixed(1), unit: "MB/s" }
  } else {
    return { display: value.toFixed(0), unit: "KB/s" }
  }
}

function ResourceBar({ icon: Icon, label, value, unit, color, textColor, max = 100 }: ResourceBarProps) {
  const percentage = Math.min((value / max) * 100, 100)
  
  const isNetwork = unit === "KB/s"
  const displayValue = isNetwork ? formatNetworkValue(value) : null

  return (
    <div className="p-3 rounded-lg bg-muted/30 space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Icon className="w-4 h-4 text-muted-foreground" />
          <span className="text-xs text-muted-foreground">{label}</span>
        </div>
        <span className={`text-sm font-mono font-medium ${textColor}`}>
          {isNetwork && displayValue ? `${displayValue.display}${displayValue.unit}` : `${value}${unit}`}
        </span>
      </div>
      <Progress value={percentage} className={`h-1.5 ${color}`} />
    </div>
  )
}
