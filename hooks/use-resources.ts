"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { api } from "@/lib/api"
import type { Resources, ResourceHistory } from "@/lib/types"

export function useResources() {
  const [resources, setResources] = useState<Resources>({
    cpu: 0,
    memory: 0,
    disk: 0,
    network: 0,
  })

  const [history, setHistory] = useState<ResourceHistory[]>([])
  const [loading, setLoading] = useState(false)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  const fetchResources = useCallback(async () => {
    try {
      const response = await api.getResources()
      if (response.data) {
        const newResources = {
          // FIX: Menggunakan (as any) untuk mengatasi error TypeScript
          // karena tipe data di @/lib/types mungkin belum update
          cpu: (response.data.cpu as any)?.percent || response.data.cpu || 0,
          memory: (response.data.memory as any)?.percent || response.data.memory || 0,
          disk: (response.data.disk as any)?.percent || response.data.disk || 0,
          network: (response.data.network as any)?.bytes_sent || response.data.network || 0,
        }

        setResources(newResources)

        // Update history with new data point
        setHistory((prev) => {
          const now = new Date()
          const timeLabel = `${now.getMinutes()}:${now.getSeconds().toString().padStart(2, "0")}`
          const updated = [
            ...prev.slice(-10), // Keep last 10 entries
            {
              time: timeLabel,
              cpu: newResources.cpu,
              memory: newResources.memory,
            },
          ]
          return updated
        })
      }
    } catch (error) {
      console.error("Failed to fetch resources:", error)
      // Silent fail, will retry on next interval
    }
  }, [])

  useEffect(() => {
    // Initialize with empty history for chart placeholder
    const initialHistory: ResourceHistory[] = []
    for (let i = 10; i >= 0; i--) {
      initialHistory.push({
        time: `${i}m`,
        cpu: 0,
        memory: 0,
      })
    }
    setHistory(initialHistory)

    // Fetch initial data
    setLoading(true)
    fetchResources().finally(() => setLoading(false))

    // Set interval loop (3 seconds)
    intervalRef.current = setInterval(fetchResources, 3000)

    // Cleanup on unmount
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [fetchResources])

  return { resources, history, loading }
}