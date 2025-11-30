"use client"

import { useState, useEffect, useCallback, useRef } from "react"

const getWsUrl = () => {
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    
    // Try to get API URL from environment (set at build time)
    const apiUrl = process.env.NEXT_PUBLIC_API_URL
    if (apiUrl) {
      // Convert http/https to ws/wss and derive host from API URL
      const apiHost = apiUrl.replace('http://', '').replace('https://', '')
      return `${protocol.replace(':', '')}://${apiHost}/ws/live`
    }
    
    const host = window.location.host
    
    // In production (no port in URL), use the rewrites path
    if (!host.includes(':')) {
      return `${protocol}//${host}/ws/live`
    }
    
    // In development, connect directly to backend on port 8000
    // This avoids Next.js dev server WebSocket proxy limitations
    const backendHost = host.replace(':5000', ':8000').replace(':3000', ':8000')
    return `${protocol}//${backendHost}/ws/live`
  }
  return "ws://localhost:8000/ws/live"
}
const WS_URL = getWsUrl()

export interface WebSocketMessage {
  type:
    | "system"
    | "mode_change"
    | "queue_list"
    | "queue_add"
    | "queue_remove"
    | "queue_edit"
    | "queue_update"
    | "queue_clear"
    | "chat_response"
    | "agent_update"
    | "agent_status"
    | "model_instruction"
    | "history_update"
    | "mission_update"
    | "findings_explorer_update"
    | "finding_update"
    | "error"
  message?: string
  mode?: string
  queue?: QueueItem[] | QueueState
  state?: QueueState
  total?: number
  commands?: Record<string, string>
  agents?: AgentUpdate[]
  removed?: string
  index?: number
  agent_id?: string
  status?: string
  last_command?: string
  execution_time?: number
  progress?: number
  cpu_usage?: number
  memory_usage?: number
  instruction?: string
  model_name?: string
  instruction_type?: string
  added?: number
  timestamp?: string
  data?: any
  finding?: any
}

export interface QueueItem {
  index: number
  command: string
}

export interface QueueInstruction {
  id: number
  command: string
  status: "pending" | "executing" | "completed"
  added_at?: string
  claimed_by?: string | null
  started_at?: string | null
  completed_at?: string | null
}

export interface QueueState {
  pending: QueueInstruction[]
  executing: QueueInstruction[]
  total_pending: number
  total_executing: number
  total_completed: number
  recent_completed: QueueInstruction[]
}

export interface AgentUpdate {
  id: string
  status: "idle" | "running" | "paused" | "error"
  last_command: string
  execution_time: number
  cpu_usage: number
  memory_usage: number
  progress: number
}

export function useWebSocket() {
  const [connected, setConnected] = useState(false)
  const [connecting, setConnecting] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const [connectionError, setConnectionError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 10
  const messageHandlersRef = useRef<Map<string, (msg: WebSocketMessage) => void>>(new Map())

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN || wsRef.current?.readyState === WebSocket.CONNECTING) return

    setConnecting(true)
    setConnectionError(null)

    try {
      const ws = new WebSocket(WS_URL)

      ws.onopen = () => {
        setConnected(true)
        setConnecting(false)
        setConnectionError(null)
        reconnectAttempts.current = 0
      }

      ws.onclose = (event) => {
        setConnected(false)
        setConnecting(false)

        // Don't reconnect if closed intentionally
        if (event.code === 1000) return

        // Exponential backoff for reconnection
        if (reconnectAttempts.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000)
          reconnectAttempts.current++
          reconnectTimeoutRef.current = setTimeout(connect, delay)
        } else {
          setConnectionError("Unable to connect to backend. Please check if the server is running.")
        }
      }

      ws.onerror = () => {
        setConnecting(false)
        setConnectionError("WebSocket connection error")
      }

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as WebSocketMessage
          setLastMessage(message)
          const handler = messageHandlersRef.current.get(message.type)
          if (handler) {
            handler(message)
          }
        } catch {
          // Failed to parse message
        }
      }

      wsRef.current = ws
    } catch {
      setConnecting(false)
      setConnectionError("Failed to create WebSocket connection")
      reconnectTimeoutRef.current = setTimeout(connect, 3000)
    }
  }, [])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    if (wsRef.current) {
      wsRef.current.close(1000, "User disconnected")
      wsRef.current = null
    }
    setConnected(false)
    setConnecting(false)
  }, [])

  const sendCommand = useCallback((content: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "command",
          content,
        }),
      )
      return true
    }
    return false
  }, [])

  const sendChat = useCallback((content: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "chat",
          content,
        }),
      )
      return true
    }
    return false
  }, [])

  const requestUpdates = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "get_updates",
        }),
      )
    }
  }, [])

  const onMessage = useCallback((type: string, handler: (msg: WebSocketMessage) => void) => {
    messageHandlersRef.current.set(type, handler)
    return () => {
      messageHandlersRef.current.delete(type)
    }
  }, [])

  useEffect(() => {
    connect()

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      wsRef.current?.close()
    }
  }, [connect])

  return {
    connected,
    connecting,
    connectionError,
    lastMessage,
    sendCommand,
    sendChat,
    requestUpdates,
    onMessage,
    disconnect,
    reconnect: connect,
  }
}
