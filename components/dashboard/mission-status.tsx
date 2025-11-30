"use client"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Target, Clock, StopCircle, Bot, CheckCircle2, AlertTriangle } from "lucide-react"
import type { Mission } from "@/lib/types"
import { formatDuration } from "@/lib/utils"

interface MissionStatusProps {
  mission: Mission
  onStop: () => void
}

export function MissionStatus({ mission, onStop }: MissionStatusProps) {
  if (!mission.active && !mission.target) {
    return (
      <div className="rounded-lg border border-dashed border-border p-6 text-center">
        <Target className="w-8 h-8 mx-auto text-muted-foreground mb-2" />
        <p className="text-sm text-muted-foreground">
          No active mission. Click Configure to start a new security assessment.
        </p>
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        {/* Mission Info */}
        <div className="flex items-center gap-4">
          <div className={`p-3 rounded-lg ${mission.active ? "bg-primary/10 border border-primary/20" : "bg-muted"}`}>
            <Target className={`w-5 h-5 ${mission.active ? "text-primary" : "text-muted-foreground"}`} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-semibold">{mission.target}</h3>
              <Badge variant="outline" className="text-xs">
                {mission.category}
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground truncate max-w-md">
              {mission.instruction || "Security Assessment"}
            </p>
          </div>
        </div>

        {/* Status & Metrics */}
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 text-sm">
            <Clock className="w-4 h-4 text-muted-foreground" />
            <span className="font-mono">{formatDuration(mission.duration)}</span>
          </div>

          <div className="flex items-center gap-2 text-sm">
            <Bot className="w-4 h-4 text-muted-foreground" />
            <span>
              {mission.activeAgents}/{mission.totalAgents}
            </span>
          </div>

          <div className="hidden md:flex items-center gap-4">
            <div className="flex items-center gap-1.5 text-sm">
              <CheckCircle2 className="w-4 h-4 text-primary" />
              <span>{mission.completedTasks}</span>
            </div>
            <div className="flex items-center gap-1.5 text-sm">
              <AlertTriangle className="w-4 h-4 text-chart-3" />
              <span>{mission.findings}</span>
            </div>
          </div>

          {mission.active && (
            <Button variant="destructive" size="sm" onClick={onStop} className="gap-1.5">
              <StopCircle className="w-4 h-4" />
              Stop
            </Button>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      {mission.active && (
        <div className="mt-4 space-y-1.5">
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Progress</span>
            <span>{mission.progress}%</span>
          </div>
          <Progress value={mission.progress} className="h-1.5" />
        </div>
      )}
    </div>
  )
}
