"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { Badge } from "@/components/ui/badge"
import { Timer } from "lucide-react"

interface MissionTimerProps {
  active: boolean
  startTime?: number
  duration: number
  maxDuration?: number | null
}

export function MissionTimer({ active, startTime, duration, maxDuration }: MissionTimerProps) {
  const [elapsed, setElapsed] = useState(duration)
  const fallbackStartRef = useRef<number | null>(null)
  const rafRef = useRef<number | null>(null)
  const lastUpdateRef = useRef<number>(0)

  const updateTimer = useCallback(() => {
    const effectiveStartTime = startTime || fallbackStartRef.current
    
    if (effectiveStartTime) {
      const now = Date.now()
      const diff = Math.floor((now - effectiveStartTime) / 1000)
      setElapsed(Math.max(0, diff))
    } else {
      setElapsed(prev => prev + 1)
    }
  }, [startTime])

  useEffect(() => {
    if (!active) {
      setElapsed(0)
      fallbackStartRef.current = null
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current)
        rafRef.current = null
      }
      return
    }

    if (!startTime && !fallbackStartRef.current) {
      fallbackStartRef.current = Date.now() - (duration * 1000)
    }

    const tick = (timestamp: number) => {
      if (timestamp - lastUpdateRef.current >= 1000) {
        lastUpdateRef.current = timestamp
        updateTimer()
      }
      rafRef.current = requestAnimationFrame(tick)
    }

    updateTimer()
    rafRef.current = requestAnimationFrame(tick)

    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current)
        rafRef.current = null
      }
    }
  }, [active, startTime, duration, updateTimer])

  const formatTime = (seconds: number) => {
    const hrs = Math.floor(seconds / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60

    if (hrs > 0) {
      return `${hrs.toString().padStart(2, "0")}:${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
    }
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
  }

  if (!active) return null

  const isNearLimit = maxDuration && elapsed >= (maxDuration * 60 - 60)

  return (
    <Badge
      variant="outline"
      className={`gap-1.5 font-mono text-sm px-2.5 py-1 ${
        isNearLimit 
          ? "border-destructive/50 text-destructive bg-destructive/5 animate-pulse" 
          : "border-chart-3/50 text-chart-3 bg-chart-3/5"
      }`}
    >
      <Timer className="w-3.5 h-3.5 animate-pulse" />
      {formatTime(elapsed)}
      {maxDuration && (
        <span className="text-xs opacity-70">/ {maxDuration}m</span>
      )}
    </Badge>
  )
}
