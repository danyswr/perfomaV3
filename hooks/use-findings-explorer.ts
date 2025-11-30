"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import { api, type FindingsExplorerResponse, type FileInfo, type FolderInfo, type FileContentResponse, type AgentLogEntry } from "@/lib/api"
import { useWebSocket } from "./use-websocket"

interface AgentRealtimeLogs {
  [agentId: string]: AgentLogEntry[]
}

export function useFindingsExplorer() {
  const [explorer, setExplorer] = useState<FindingsExplorerResponse>({
    folders: [],
    root_files: [],
    total_files: 0,
    last_updated: new Date().toISOString()
  })
  const [loading, setLoading] = useState(false)
  const [selectedFile, setSelectedFile] = useState<FileInfo | null>(null)
  const [fileContent, setFileContent] = useState<FileContentResponse | null>(null)
  const [fileLoading, setFileLoading] = useState(false)
  const [logs, setLogs] = useState<FileInfo[]>([])
  const [realtimeLogs, setRealtimeLogs] = useState<AgentRealtimeLogs>({})
  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  const { lastMessage } = useWebSocket()

  const fetchExplorer = useCallback(async () => {
    try {
      const response = await api.getFindingsExplorer()
      if (response.data) {
        setExplorer(response.data)
      }
    } catch {
    }
  }, [])

  const fetchLogs = useCallback(async () => {
    try {
      const response = await api.getAgentLogs()
      if (response.data) {
        setLogs(response.data.logs)
      }
    } catch {
    }
  }, [])

  const fetchFileContent = useCallback(async (filePath: string) => {
    setFileLoading(true)
    try {
      const response = await api.getFileContent(filePath)
      if (response.data) {
        setFileContent(response.data)
      }
    } catch {
      setFileContent(null)
    } finally {
      setFileLoading(false)
    }
  }, [])

  const fetchLogContent = useCallback(async (fileName: string) => {
    setFileLoading(true)
    try {
      const response = await api.getLogContent(fileName)
      if (response.data) {
        setFileContent({
          type: "log",
          content: response.data.content,
          filename: response.data.filename
        })
      }
    } catch {
      setFileContent(null)
    } finally {
      setFileLoading(false)
    }
  }, [])

  const openFile = useCallback((file: FileInfo, isLog: boolean = false) => {
    setSelectedFile(file)
    if (isLog) {
      fetchLogContent(file.name)
    } else {
      fetchFileContent(file.path)
    }
  }, [fetchFileContent, fetchLogContent])

  const closeFile = useCallback(() => {
    setSelectedFile(null)
    setFileContent(null)
  }, [])

  useEffect(() => {
    if (lastMessage?.type === "findings_explorer_update" && lastMessage.data) {
      setExplorer(lastMessage.data as FindingsExplorerResponse)
    }
    
    if (lastMessage?.type === "agent_log" && lastMessage.agent_id && lastMessage.log) {
      setRealtimeLogs(prev => {
        const agentId = lastMessage.agent_id as string
        const newLog = lastMessage.log as AgentLogEntry
        const existingLogs = prev[agentId] || []
        return {
          ...prev,
          [agentId]: [...existingLogs.slice(-99), newLog]
        }
      })
    }
    
    if (lastMessage?.type === "finding_update" && lastMessage.finding) {
      fetchExplorer()
    }
  }, [lastMessage, fetchExplorer])

  useEffect(() => {
    setLoading(true)
    Promise.all([fetchExplorer(), fetchLogs()]).finally(() => setLoading(false))

    intervalRef.current = setInterval(() => {
      fetchExplorer()
      fetchLogs()
    }, 500)

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [fetchExplorer, fetchLogs])

  return {
    explorer,
    logs,
    realtimeLogs,
    loading,
    selectedFile,
    fileContent,
    fileLoading,
    openFile,
    closeFile,
    refetch: fetchExplorer,
    refetchLogs: fetchLogs,
    clearRealtimeLogs: () => setRealtimeLogs({}),
  }
}

export type { FileInfo, FolderInfo, FindingsExplorerResponse, FileContentResponse }
