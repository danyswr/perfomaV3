"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import { api, type FindingResponse } from "@/lib/api"
import type { Finding } from "@/lib/types"
import { useWebSocket } from "./use-websocket"

function transformFinding(f: FindingResponse): Finding {
  return {
    id: f.id,
    title: f.title,
    description: f.description,
    severity: f.severity,
    cve: f.cve,
    cvss: f.cvss,
    agentId: f.agent_id,
    timestamp: new Date(f.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
  }
}

export function useFindings() {
  const [findings, setFindings] = useState<Finding[]>([])
  const [severitySummary, setSeveritySummary] = useState({
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
    info: 0,
  })
  const [loading, setLoading] = useState(false)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  const { lastMessage } = useWebSocket()

  const fetchFindings = useCallback(async () => {
    try {
      const response = await api.getFindings()
      if (response.data) {
        setFindings(response.data.findings.map(transformFinding))
        setSeveritySummary(response.data.severity_summary)
      }
    } catch {
    }
  }, [])

  useEffect(() => {
    if (!lastMessage) return
    
    if (lastMessage.type === "finding_update" && lastMessage.finding) {
      const newFinding = transformFinding(lastMessage.finding as FindingResponse)
      setFindings((prev) => {
        const exists = prev.some((f) => f.id === newFinding.id)
        if (exists) return prev
        return [newFinding, ...prev]
      })
      
      const severity = newFinding.severity as keyof typeof severitySummary
      setSeveritySummary((prev) => ({
        ...prev,
        [severity]: (prev[severity] || 0) + 1,
      }))
    }
  }, [lastMessage])

  useEffect(() => {
    setLoading(true)
    fetchFindings().finally(() => setLoading(false))

    intervalRef.current = setInterval(fetchFindings, 10000)

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [fetchFindings])

  const exportFindings = useCallback(() => {
    const data = JSON.stringify(findings, null, 2)
    const blob = new Blob([data], { type: "application/json" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `findings-${new Date().toISOString().split("T")[0]}.json`
    a.click()
    URL.revokeObjectURL(url)
  }, [findings])

  const exportCsv = useCallback(() => {
    const headers = ["ID", "Title", "Description", "Severity", "CVE", "CVSS", "Agent ID", "Timestamp"]
    const rows = findings.map(f => [
      f.id,
      `"${f.title.replace(/"/g, '""')}"`,
      `"${f.description.replace(/"/g, '""')}"`,
      f.severity,
      f.cve || "",
      f.cvss?.toString() || "",
      f.agentId,
      f.timestamp
    ])
    
    const csvContent = [headers.join(","), ...rows.map(r => r.join(","))].join("\n")
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `findings-${new Date().toISOString().split("T")[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }, [findings])

  const generateTextReport = useCallback(() => {
    let report = "═══════════════════════════════════════════════════════════════\n"
    report += "                    SECURITY ASSESSMENT REPORT\n"
    report += "═══════════════════════════════════════════════════════════════\n\n"
    report += `Generated: ${new Date().toLocaleString()}\n\n`
    
    report += "SEVERITY SUMMARY\n"
    report += "───────────────────────────────────────────────────────────────\n"
    report += `  Critical: ${severitySummary.critical}\n`
    report += `  High:     ${severitySummary.high}\n`
    report += `  Medium:   ${severitySummary.medium}\n`
    report += `  Low:      ${severitySummary.low}\n`
    report += `  Info:     ${severitySummary.info}\n\n`
    
    report += "DETAILED FINDINGS\n"
    report += "═══════════════════════════════════════════════════════════════\n\n"
    
    findings.forEach((f, index) => {
      report += `[${index + 1}] ${f.severity.toUpperCase()} - ${f.title}\n`
      report += `───────────────────────────────────────────────────────────────\n`
      if (f.cve) report += `  CVE: ${f.cve}\n`
      if (f.cvss) report += `  CVSS Score: ${f.cvss}\n`
      report += `  Agent: ${f.agentId} | Time: ${f.timestamp}\n\n`
      report += `  Description:\n  ${f.description}\n\n`
    })
    
    return report
  }, [findings, severitySummary])

  const exportPdf = useCallback(async () => {
    try {
      const response = await fetch("/api/export-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ findings, severitySummary })
      })
      
      if (response.ok) {
        const blob = await response.blob()
        const url = URL.createObjectURL(blob)
        const a = document.createElement("a")
        a.href = url
        a.download = `security-report-${new Date().toISOString().split("T")[0]}.pdf`
        a.click()
        URL.revokeObjectURL(url)
      } else {
        const textContent = generateTextReport()
        const blob = new Blob([textContent], { type: "text/plain" })
        const url = URL.createObjectURL(blob)
        const a = document.createElement("a")
        a.href = url
        a.download = `security-report-${new Date().toISOString().split("T")[0]}.txt`
        a.click()
        URL.revokeObjectURL(url)
      }
    } catch {
      const textContent = generateTextReport()
      const blob = new Blob([textContent], { type: "text/plain" })
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `security-report-${new Date().toISOString().split("T")[0]}.txt`
      a.click()
      URL.revokeObjectURL(url)
    }
  }, [findings, severitySummary, generateTextReport])

  return {
    findings,
    severitySummary,
    loading,
    exportFindings,
    exportCsv,
    exportPdf,
    refetch: fetchFindings,
  }
}
