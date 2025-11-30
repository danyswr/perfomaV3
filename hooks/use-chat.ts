"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import { useWebSocket } from "./use-websocket"
import type { ChatMessage } from "@/lib/types"
import { formatTime } from "@/lib/utils"

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [mode, setMode] = useState<"chat" | "queue">("chat")
  const [sendingMessage, setSendingMessage] = useState(false)
  const messageQueue = useRef<string[]>([])
  const { connected, connecting, connectionError, sendCommand, sendChat, lastMessage, reconnect } = useWebSocket()

  const addMessage = useCallback((role: "user" | "assistant" | "system", content: string, isTemporary = false) => {
    const message: ChatMessage = {
      id: isTemporary ? `temp-${Date.now()}` : Date.now().toString(),
      role,
      content,
      timestamp: formatTime(new Date()),
    }
    setMessages((prev) => [...prev, message])
    return message
  }, [])

  useEffect(() => {
    if (!lastMessage) return

    switch (lastMessage.type) {
      case "system":
        addMessage("system", lastMessage.message || "Connected to system")
        break
      case "mode_change":
        setMode(lastMessage.mode === "chat" ? "chat" : "queue")
        addMessage("system", lastMessage.message || `Switched to ${lastMessage.mode} mode`)
        break
      case "chat_response":
        addMessage("assistant", lastMessage.message || "")
        break
      case "queue_list":
        if (lastMessage.queue && Array.isArray(lastMessage.queue) && lastMessage.queue.length > 0) {
          const queueStr = (lastMessage.queue as Array<{index: number; command: string}>).map((item) => `${item.index}. ${item.command}`).join("\n")
          addMessage("system", `Queue (${lastMessage.total} items):\n${queueStr}`)
        } else {
          addMessage("system", "Queue is empty")
        }
        break
      case "queue_add":
        addMessage("system", lastMessage.message || "Commands added to queue")
        break
      case "queue_remove":
        addMessage("system", lastMessage.message || "Command removed from queue")
        break
      case "queue_edit":
        addMessage("system", lastMessage.message || "Queue item updated")
        break
      case "error":
        addMessage("system", `Error: ${lastMessage.message}`)
        break
    }
  }, [lastMessage, addMessage])

  const sendMessage = useCallback(
    (content: string, currentMode: "chat" | "queue") => {
      if (!connected) {
        addMessage("system", "Not connected to server. Click 'Offline' badge to reconnect.")
        return
      }
      
      addMessage("user", content)
      setSendingMessage(true)

      let success = false
      if (currentMode === "chat") {
        success = sendChat(content)
      } else {
        success = sendCommand(content)
      }
      
      if (!success) {
        addMessage("system", "Failed to send message. Please try again.")
      }
      
      setTimeout(() => setSendingMessage(false), 500)
    },
    [addMessage, sendChat, sendCommand, connected],
  )

  const sendQueueCommand = useCallback(
    (command: string) => {
      if (!connected) {
        addMessage("system", "Not connected to server. Click 'Offline' badge to reconnect.")
        return
      }
      addMessage("user", command)
      const success = sendCommand(command)
      if (!success) {
        addMessage("system", "Failed to send command. Please try again.")
      }
    },
    [addMessage, sendCommand, connected],
  )

  const clearMessages = useCallback(() => {
    setMessages([])
  }, [])

  return {
    messages,
    sendMessage,
    sendQueueCommand,
    clearMessages,
    mode,
    setMode,
    connected,
    connecting,
    connectionError,
    reconnect,
    sendingMessage,
  }
}
