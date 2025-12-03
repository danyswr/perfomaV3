"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { MessageSquare, Send, Bot, User, ListOrdered, Terminal, Wifi, WifiOff, AlertCircle, RefreshCw, History } from "lucide-react"
import { useChat } from "@/hooks/use-chat"
import type { ChatMessage } from "@/lib/types"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

const CHAT_HISTORY_KEY = "performa_chat_history"
const MAX_HISTORY_ITEMS = 50

function loadChatHistory(): ChatMessage[] {
  if (typeof window === 'undefined') return []
  try {
    const stored = localStorage.getItem(CHAT_HISTORY_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (e) {
    console.error("Failed to load chat history:", e)
  }
  return []
}

function saveChatHistory(messages: ChatMessage[]) {
  if (typeof window === 'undefined') return
  try {
    localStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(messages.slice(-MAX_HISTORY_ITEMS)))
  } catch (e) {
    console.error("Failed to save chat history:", e)
  }
}

export function LiveChat() {
  const [input, setInput] = useState("")
  const [activeTab, setActiveTab] = useState<"chat" | "queue" | "history">("chat")
  const { messages, sendMessage, sendQueueCommand, mode, setMode, connected, connectionError, reconnect } = useChat()
  const scrollRef = useRef<HTMLDivElement>(null)
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([])

  useEffect(() => {
    const history = loadChatHistory()
    if (history.length > 0) {
      setChatHistory(history)
    }
  }, [])

  useEffect(() => {
    if (messages.length > 0) {
      saveChatHistory(messages)
      setChatHistory(prev => {
        const newHistory = [...prev, ...messages.filter(m => !prev.some(p => p.id === m.id))]
        return newHistory.slice(-MAX_HISTORY_ITEMS)
      })
    }
  }, [messages])

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return

    if (input.startsWith("/queue")) {
      sendQueueCommand(input)
    } else if (input.startsWith("/chat")) {
      setMode("chat")
    } else {
      sendMessage(input, mode)
    }
    setInput("")
  }

  const getErrorDisplay = (error: string) => {
    // Only show 402 if it's an actual payment error from OpenRouter API
    if (error.startsWith("OpenRouter 402") || (error.includes("402") && error.includes("Payment Required") && error.includes("insufficient credits"))) {
      return {
        title: "API Credits Required",
        message: "Please add credits to your OpenRouter account to continue using AI features.",
        action: "Add Credits",
        url: "https://openrouter.ai/credits"
      }
    }
    if (error.includes("OpenRouter 401") || (error.includes("Unauthorized") && error.includes("API key"))) {
      return {
        title: "Invalid API Key",
        message: "Please check your OpenRouter API key configuration.",
        action: null,
        url: null
      }
    }
    return {
      title: "Connection Error",
      message: error,
      action: "Retry",
      url: null
    }
  }

  return (
    <Card className="border-border flex flex-col h-[500px]">
      <CardHeader className="flex flex-row items-center justify-between pb-3 flex-shrink-0">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-primary" />
          <CardTitle className="text-lg">Live Chat</CardTitle>
          {connected ? (
            <Badge variant="outline" className="bg-primary/10 text-primary border-primary/20 text-xs">
              <Wifi className="w-3 h-3 mr-1" />
              Online
            </Badge>
          ) : (
            <Badge variant="outline" className="bg-destructive/10 text-destructive border-destructive/20 text-xs">
              <WifiOff className="w-3 h-3 mr-1" />
              Offline
            </Badge>
          )}
        </div>
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)} className="w-auto">
          <TabsList className="h-7 p-0.5">
            <TabsTrigger value="chat" className="text-xs h-6 px-2 gap-1" onClick={() => setMode("chat")}>
              <MessageSquare className="w-3 h-3" />
              Chat
            </TabsTrigger>
            <TabsTrigger value="queue" className="text-xs h-6 px-2 gap-1" onClick={() => setMode("queue")}>
              <ListOrdered className="w-3 h-3" />
              Queue
            </TabsTrigger>
            <TabsTrigger value="history" className="text-xs h-6 px-2 gap-1">
              <History className="w-3 h-3" />
              History
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col p-0 min-h-0 overflow-hidden">
        {connectionError && 
         connectionError !== "WebSocket connection error" && 
         !connectionError.includes("Unable to connect") && 
         !connectionError.includes("connection error") &&
         (connectionError.includes("402") || connectionError.includes("401") || connectionError.includes("API")) && (
          <div className="mx-4 mb-2 p-3 rounded-lg bg-destructive/10 border border-destructive/20 shrink-0">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-destructive shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-destructive">{getErrorDisplay(connectionError).title}</p>
                <p className="text-xs text-muted-foreground mt-0.5">{getErrorDisplay(connectionError).message}</p>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="h-7 text-xs shrink-0"
                onClick={() => {
                  const errorInfo = getErrorDisplay(connectionError)
                  if (errorInfo.url) {
                    window.open(errorInfo.url, '_blank')
                  } else {
                    reconnect()
                  }
                }}
              >
                <RefreshCw className="w-3 h-3 mr-1" />
                {getErrorDisplay(connectionError).action || "Retry"}
              </Button>
            </div>
          </div>
        )}

        {activeTab === "history" ? (
          <ScrollArea className="flex-1 min-h-0 px-4" ref={scrollRef}>
            <div className="space-y-4 py-4 max-h-[300px] overflow-y-auto">
              {chatHistory.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <History className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No chat history yet</p>
                </div>
              ) : (
                chatHistory.map((message) => <ChatBubble key={message.id} message={message} />)
              )}
            </div>
          </ScrollArea>
        ) : (
          <ScrollArea className="flex-1 min-h-0 px-4" ref={scrollRef}>
            <div className="space-y-4 py-4 max-h-[300px] overflow-y-auto">
              {messages.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Bot className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">Start a conversation with the AI.</p>
                  <p className="text-xs mt-1">Use /queue commands to manage task queue.</p>
                  <div className="mt-4 text-left max-w-xs mx-auto">
                    <p className="text-xs font-medium mb-2">Available Commands:</p>
                    <ul className="text-xs space-y-1 text-muted-foreground">
                      <li>
                        <code className="bg-muted px-1 rounded">/chat</code> - Switch to chat mode
                      </li>
                      <li>
                        <code className="bg-muted px-1 rounded">/queue list</code> - View queue
                      </li>
                      <li>
                        <code className="bg-muted px-1 rounded">/queue add</code> - Add command
                      </li>
                      <li>
                        <code className="bg-muted px-1 rounded">/queue rm &lt;index&gt;</code> - Remove
                      </li>
                      <li>
                        <code className="bg-muted px-1 rounded">/queue edit &lt;index&gt;</code> - Edit
                      </li>
                    </ul>
                  </div>
                </div>
              ) : (
                messages.map((message) => <ChatBubble key={message.id} message={message} />)
              )}
            </div>
          </ScrollArea>
        )}

        <div className="p-4 border-t border-border flex-shrink-0">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <div className="relative flex-1">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={mode === "chat" ? "Type a message..." : "/queue list, /queue add {...}"}
                className="pr-20 bg-muted border-border"
              />
              <Badge variant="outline" className="absolute right-2 top-1/2 -translate-y-1/2 text-xs">
                {mode}
              </Badge>
            </div>
            <Button type="submit" size="icon" disabled={!connected}>
              <Send className="w-4 h-4" />
            </Button>
          </form>
          <div className="mt-2 flex flex-wrap gap-1">
            <Badge
              variant="secondary"
              className="text-xs cursor-pointer hover:bg-secondary/80"
              onClick={() => setInput("/queue list")}
            >
              /queue list
            </Badge>
            <Badge
              variant="secondary"
              className="text-xs cursor-pointer hover:bg-secondary/80"
              onClick={() => setInput('/queue add {"1":"RUN ')}
            >
              /queue add
            </Badge>
            <Badge
              variant="secondary"
              className="text-xs cursor-pointer hover:bg-secondary/80"
              onClick={() => setInput("/queue rm ")}
            >
              /queue rm
            </Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function ChatBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user"
  const isSystem = message.role === "system"
  const isError = isSystem && message.content.toLowerCase().includes("error")

  if (isSystem) {
    return (
      <div className="flex justify-center">
        <div className={`px-3 py-1.5 rounded-lg text-xs flex items-start gap-1.5 max-w-[90%] ${
          isError 
            ? "bg-destructive/10 text-destructive border border-destructive/20" 
            : "bg-muted text-muted-foreground"
        }`}>
          {isError ? (
            <AlertCircle className="w-3 h-3 mt-0.5 flex-shrink-0" />
          ) : (
            <Terminal className="w-3 h-3 mt-0.5 flex-shrink-0" />
          )}
          <pre className="whitespace-pre-wrap font-mono">{message.content}</pre>
        </div>
      </div>
    )
  }

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
          isUser ? "bg-primary/20" : "bg-muted"
        }`}
      >
        {isUser ? <User className="w-4 h-4 text-primary" /> : <Bot className="w-4 h-4 text-muted-foreground" />}
      </div>
      <div
        className={`max-w-[80%] rounded-lg px-3 py-2 ${
          isUser ? "bg-primary text-primary-foreground" : "bg-muted text-foreground"
        }`}
      >
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        <p className={`text-xs mt-1 ${isUser ? "text-primary-foreground/70" : "text-muted-foreground"}`}>
          {message.timestamp}
        </p>
      </div>
    </div>
  )
}
