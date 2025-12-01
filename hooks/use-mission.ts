"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { api } from "@/lib/api"
import type { Mission, MissionConfig } from "@/lib/types"

const MISSION_CONFIG_KEY = "performa_mission_config"

function saveMissionConfig(config: MissionConfig | null) {
  if (typeof window === 'undefined') return
  try {
    if (config) {
      localStorage.setItem(MISSION_CONFIG_KEY, JSON.stringify(config))
    } else {
      localStorage.removeItem(MISSION_CONFIG_KEY)
    }
  } catch (e) {
    console.error("Failed to save mission config:", e)
  }
}

const initialMission: Mission = {
  active: false,
  target: "",
  category: "",
  instruction: "",
  duration: 0,
  progress: 0,
  activeAgents: 0,
  totalAgents: 0,
  completedTasks: 0,
  findings: 0,
}

export function useMission() {
  const [mission, setMission] = useState<Mission>(initialMission)
  const [error, setError] = useState<string | null>(null)
  const timerRef = useRef<NodeJS.Timeout | null>(null)
  const findingsIntervalRef = useRef<NodeJS.Timeout | null>(null)

  const fetchFindings = useCallback(async () => {
    try {
      const response = await api.getFindings()
      if (response.data) {
        setMission((prev) => ({
          ...prev,
          findings: response.data!.total,
        }))
      }
    } catch {
    }
  }, [])

  const startMission = useCallback(
    async (config: MissionConfig): Promise<string[] | null> => {
      setError(null)
      
      saveMissionConfig(config)
      
      try {
        const response = await api.startMission({
          target: config.target,
          category: config.category,
          custom_instruction: config.customInstruction,
          stealth_mode: config.stealthMode,
          aggressive_mode: config.aggressiveLevel > 2,
          model_name: config.modelName,
          num_agents: config.numAgents,
          os_type: config.osType,
          stealth_options: config.stealthOptions as unknown as Record<string, boolean>,
          capabilities: config.capabilities as unknown as Record<string, boolean>,
          batch_size: config.batchSize,
          rate_limit_rps: config.rateLimitEnabled ? config.rateLimitRps : 0,
          execution_duration: config.executionDuration,
          requested_tools: config.requestedTools,
          allowed_tools_only: config.allowedToolsOnly,
          instruction_delay_ms: config.instructionDelayMs || 0,
          model_delay_ms: config.modelDelayMs || 0,
        })

        if (response.error) {
          setError(response.error)
          return null
        }

        const agentIds = response.data?.agent_ids || []

        const missionStartTime = Date.now()
        setMission({
          active: true,
          target: config.target,
          category: config.category,
          instruction: config.customInstruction,
          duration: 0,
          progress: 0,
          activeAgents: agentIds.length,
          totalAgents: config.numAgents,
          completedTasks: 0,
          findings: 0,
          startTime: missionStartTime,
          maxDuration: config.executionDuration || null,
        })

        timerRef.current = setInterval(() => {
          setMission((prev) => ({
            ...prev,
            duration: prev.duration + 1,
          }))
        }, 1000)

        findingsIntervalRef.current = setInterval(fetchFindings, 5000)

        return agentIds
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to start mission")
        return null
      }
    },
    [fetchFindings],
  )

  const stopMission = useCallback(async () => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
    if (findingsIntervalRef.current) {
      clearInterval(findingsIntervalRef.current)
      findingsIntervalRef.current = null
    }
    
    try {
      const response = await api.stopMission()
      if (response.data) {
        setMission((prev) => ({ 
          ...prev, 
          active: false,
          summary: response.data?.summary || null,
          reportsGenerated: response.data?.reports_generated_for || []
        }))
      } else {
        setMission((prev) => ({ ...prev, active: false }))
      }
    } catch {
      setMission((prev) => ({ ...prev, active: false }))
    }
    
    saveMissionConfig(null)
  }, [])

  const updateProgress = useCallback((progress: number, activeAgents: number, completedTasks: number) => {
    setMission((prev) => {
      const newState = {
        ...prev,
        progress,
        activeAgents,
        completedTasks,
      }
      if (prev.active && !prev.startTime) {
        newState.startTime = Date.now() - (prev.duration * 1000)
      }
      return newState
    })
  }, [])

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
      if (findingsIntervalRef.current) {
        clearInterval(findingsIntervalRef.current)
      }
    }
  }, [])

  return { mission, error, startMission, stopMission, updateProgress }
}
