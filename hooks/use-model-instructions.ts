"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import type { ModelInstruction } from "@/lib/types"
import { useWebSocket } from "@/hooks/use-websocket"

const STORAGE_KEY = "performa_model_instructions"
const PROCESSED_KEY = "performa_processed_commands"
const MAX_INSTRUCTIONS = 15

function generateUUID(): string {
  if (typeof window !== 'undefined' && window.crypto && window.crypto.randomUUID) {
    return window.crypto.randomUUID()
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = Math.random() * 16 | 0
    const v = c === 'x' ? r : (r & 0x3 | 0x8)
    return v.toString(16)
  })
}

function loadFromStorage(): ModelInstruction[] {
  if (typeof window === 'undefined') return []
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (e) {
    console.error("Failed to load model instructions from storage:", e)
  }
  return []
}

function loadProcessedCommands(): Set<string> {
  if (typeof window === 'undefined') return new Set()
  try {
    const stored = localStorage.getItem(PROCESSED_KEY)
    if (stored) {
      return new Set(JSON.parse(stored))
    }
  } catch (e) {
    console.error("Failed to load processed commands from storage:", e)
  }
  return new Set()
}

function saveToStorage(instructions: ModelInstruction[]) {
  if (typeof window === 'undefined') return
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(instructions.slice(0, MAX_INSTRUCTIONS)))
  } catch (e) {
    console.error("Failed to save model instructions to storage:", e)
  }
}

function saveProcessedCommands(commands: Set<string>) {
  if (typeof window === 'undefined') return
  try {
    const arr = Array.from(commands).slice(-500)
    localStorage.setItem(PROCESSED_KEY, JSON.stringify(arr))
  } catch (e) {
    console.error("Failed to save processed commands to storage:", e)
  }
}

export function useModelInstructions() {
  const [instructions, setInstructions] = useState<ModelInstruction[]>([])
  const { lastMessage, connected } = useWebSocket()
  const processedCommands = useRef<Set<string>>(new Set())
  const isInitialized = useRef(false)

  useEffect(() => {
    if (!isInitialized.current && typeof window !== 'undefined') {
      const stored = loadFromStorage()
      const processed = loadProcessedCommands()
      
      if (stored.length > 0) {
        setInstructions(stored)
      }
      
      processedCommands.current = processed
      
      stored.forEach(inst => {
        const key = `${inst.agentId}-${inst.instruction}`
        processedCommands.current.add(key)
      })
      
      isInitialized.current = true
    }
  }, [])

  useEffect(() => {
    if (isInitialized.current && instructions.length > 0) {
      saveToStorage(instructions)
      saveProcessedCommands(processedCommands.current)
    }
  }, [instructions])

  useEffect(() => {
    if (lastMessage) {
      const data = lastMessage as unknown as Record<string, unknown>
      
      if (data.type === "broadcast_event") {
        const eventType = String(data.event_type || "info") as ModelInstruction["type"]
        const content = String(data.content || data.instruction || "")
        const agentId = String(data.agent_id || "system")
        const severity = data.severity as ModelInstruction["severity"]
        const commandKey = `${agentId}-${content}-${Date.now()}`
        
        if (content && !processedCommands.current.has(commandKey)) {
          processedCommands.current.add(commandKey)
          const newInstruction: ModelInstruction = {
            id: generateUUID(),
            agentId,
            modelName: String(data.model_name || "System"),
            instruction: content,
            timestamp: new Date().toLocaleTimeString(),
            type: eventType,
            severity
          }
          setInstructions(prev => [newInstruction, ...prev].slice(0, MAX_INSTRUCTIONS))
        }
      }

      if (data.type === "model_instruction") {
        const newInstruction: ModelInstruction = {
          id: generateUUID(),
          agentId: String(data.agent_id || "unknown"),
          modelName: String(data.model_name || "GPT-4 Turbo"),
          instruction: String(data.instruction || data.content || ""),
          timestamp: new Date().toLocaleTimeString(),
          type: (data.instruction_type as ModelInstruction["type"]) || "command"
        }
        
        const commandKey = `${newInstruction.agentId}-${newInstruction.instruction}-${Date.now()}`
        if (!processedCommands.current.has(commandKey)) {
          processedCommands.current.add(commandKey)
          setInstructions(prev => [newInstruction, ...prev].slice(0, MAX_INSTRUCTIONS))
        }
      }
      
      if (data.type === "agent_finding" || data.type === "finding") {
        const findingContent = String(data.content || data.finding || "")
        const agentId = String(data.agent_id || "unknown")
        const severity = data.severity as ModelInstruction["severity"]
        const commandKey = `${agentId}-finding-${Date.now()}`
        
        if (findingContent && !processedCommands.current.has(commandKey)) {
          processedCommands.current.add(commandKey)
          const newInstruction: ModelInstruction = {
            id: generateUUID(),
            agentId,
            modelName: String(data.model || "Agent"),
            instruction: findingContent,
            timestamp: new Date().toLocaleTimeString(),
            type: "found",
            severity
          }
          setInstructions(prev => [newInstruction, ...prev].slice(0, MAX_INSTRUCTIONS))
        }
      }
      
      if (data.type === "agent_execute" || data.type === "execute") {
        const commandContent = String(data.command || data.content || "")
        const agentId = String(data.agent_id || "unknown")
        const commandKey = `${agentId}-exec-${Date.now()}`
        
        if (commandContent && !processedCommands.current.has(commandKey)) {
          processedCommands.current.add(commandKey)
          const newInstruction: ModelInstruction = {
            id: generateUUID(),
            agentId,
            modelName: String(data.model || "Agent"),
            instruction: commandContent,
            timestamp: new Date().toLocaleTimeString(),
            type: "execute"
          }
          setInstructions(prev => [newInstruction, ...prev].slice(0, MAX_INSTRUCTIONS))
        }
      }

      if (data.type === "agent_command" || data.type === "command") {
        const commandContent = String(data.command || data.content || "")
        const agentId = String(data.agent_id || "unknown")
        const commandKey = `${agentId}-cmd-${Date.now()}`
        
        if (commandContent && !processedCommands.current.has(commandKey)) {
          processedCommands.current.add(commandKey)
          const newInstruction: ModelInstruction = {
            id: generateUUID(),
            agentId,
            modelName: String(data.model || "AI Model"),
            instruction: commandContent,
            timestamp: new Date().toLocaleTimeString(),
            type: "command"
          }
          setInstructions(prev => [newInstruction, ...prev].slice(0, MAX_INSTRUCTIONS))
        }
      }

      // Handle real-time history updates from WebSocket
      if (data.type === "history_update") {
        const history = data.history as Array<{
          instruction: string
          instruction_type: string
          timestamp: string
          model_name: string
          agent_id?: string
        }> | undefined
        
        if (history && Array.isArray(history)) {
          history.forEach((item) => {
            const agentId = String(item.agent_id || "unknown")
            const commandKey = `${agentId}-${item.instruction}`
            
            if (!processedCommands.current.has(commandKey)) {
              processedCommands.current.add(commandKey)
              
              const newInstruction: ModelInstruction = {
                id: generateUUID(),
                agentId,
                modelName: item.model_name || "AI Model",
                instruction: item.instruction,
                timestamp: new Date(item.timestamp).toLocaleTimeString(),
                type: (item.instruction_type as ModelInstruction["type"]) || "command"
              }
              setInstructions(prev => {
                // Add only if not already present
                const exists = prev.some(p => 
                  p.agentId === agentId && p.instruction === item.instruction
                )
                if (exists) return prev
                return [newInstruction, ...prev].slice(0, MAX_INSTRUCTIONS)
              })
            }
          })
        }
      }
    }
  }, [lastMessage])

  const addInstruction = useCallback((instruction: Omit<ModelInstruction, "id" | "timestamp">) => {
    const newInstruction: ModelInstruction = {
      ...instruction,
      id: generateUUID(),
      timestamp: new Date().toLocaleTimeString()
    }
    const commandKey = `${newInstruction.agentId}-${newInstruction.instruction}`
    if (!processedCommands.current.has(commandKey)) {
      processedCommands.current.add(commandKey)
      setInstructions(prev => [newInstruction, ...prev].slice(0, MAX_INSTRUCTIONS))
    }
  }, [])

  const clearInstructions = useCallback(() => {
    setInstructions([])
    processedCommands.current.clear()
    if (typeof window !== 'undefined') {
      localStorage.removeItem(STORAGE_KEY)
      localStorage.removeItem(PROCESSED_KEY)
    }
  }, [])

  return {
    instructions,
    addInstruction,
    clearInstructions,
    connected
  }
}
