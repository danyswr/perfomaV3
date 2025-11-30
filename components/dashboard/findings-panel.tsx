"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { AlertTriangle, Shield, Download, ChevronRight, FileJson, FileText, RefreshCw, FileSpreadsheet, FileDown } from "lucide-react"
import { useFindings } from "@/hooks/use-findings"
import type { Finding } from "@/lib/types"

export function FindingsPanel() {
  const { findings, severitySummary, loading, exportFindings, exportCsv, exportPdf, refetch } = useFindings()

  return (
    <Card className="border-border">
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <div className="flex items-center gap-2">
          <Shield className="w-5 h-5 text-primary" />
          <CardTitle className="text-lg">Findings</CardTitle>
          <Badge variant="secondary">{findings.length}</Badge>
        </div>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="icon" onClick={refetch} disabled={loading} className="h-7 w-7">
            <RefreshCw className={`w-3 h-3 ${loading ? "animate-spin" : ""}`} />
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="gap-1.5 h-7 bg-transparent">
                <Download className="w-3 h-3" />
                Export
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={exportFindings}>
                <FileJson className="w-4 h-4 mr-2" />
                Export JSON
              </DropdownMenuItem>
              <DropdownMenuItem onClick={exportCsv}>
                <FileSpreadsheet className="w-4 h-4 mr-2" />
                Export CSV
              </DropdownMenuItem>
              <DropdownMenuItem onClick={exportPdf}>
                <FileDown className="w-4 h-4 mr-2" />
                Export PDF
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Severity Overview - use severitySummary from API */}
        <div className="flex gap-2 flex-wrap">
          <SeverityBadge severity="critical" count={severitySummary.critical} />
          <SeverityBadge severity="high" count={severitySummary.high} />
          <SeverityBadge severity="medium" count={severitySummary.medium} />
          <SeverityBadge severity="low" count={severitySummary.low} />
          <SeverityBadge severity="info" count={severitySummary.info} />
        </div>

        {/* Findings List */}
        <ScrollArea className="h-[250px]">
          <div className="space-y-2 pr-4">
            {findings.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <AlertTriangle className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No findings yet.</p>
                <p className="text-xs mt-1">Findings will appear as agents discover vulnerabilities.</p>
              </div>
            ) : (
              findings.map((finding) => <FindingItem key={finding.id} finding={finding} />)
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}

function SeverityBadge({ severity, count }: { severity: string; count: number }) {
  const colors: Record<string, string> = {
    critical: "bg-critical/20 text-critical border-critical/30",
    high: "bg-high/20 text-high border-high/30",
    medium: "bg-medium/20 text-medium border-medium/30",
    low: "bg-low/20 text-low border-low/30",
    info: "bg-info/20 text-info border-info/30",
  }

  return (
    <Badge variant="outline" className={`${colors[severity]} text-xs capitalize`}>
      {severity}: {count}
    </Badge>
  )
}

function FindingItem({ finding }: { finding: Finding }) {
  const severityColors: Record<string, string> = {
    critical: "border-l-critical",
    high: "border-l-high",
    medium: "border-l-medium",
    low: "border-l-low",
    info: "border-l-info",
  }

  return (
    <div
      className={`p-3 rounded-lg bg-muted/30 border-l-2 ${severityColors[finding.severity]} hover:bg-muted/50 transition-colors cursor-pointer`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="outline" className="text-xs capitalize">
              {finding.severity}
            </Badge>
            {finding.cve && (
              <Badge variant="secondary" className="text-xs font-mono">
                {finding.cve}
              </Badge>
            )}
          </div>
          <p className="text-sm font-medium truncate">{finding.title}</p>
          <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">{finding.description}</p>
        </div>
        <ChevronRight className="w-4 h-4 text-muted-foreground flex-shrink-0 mt-1" />
      </div>
      <div className="mt-2 flex items-center justify-between">
        {finding.cvss && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">CVSS:</span>
            <span
              className={`text-xs font-mono font-medium ${
                finding.cvss >= 9
                  ? "text-critical"
                  : finding.cvss >= 7
                    ? "text-high"
                    : finding.cvss >= 4
                      ? "text-medium"
                      : "text-low"
              }`}
            >
              {finding.cvss.toFixed(1)}
            </span>
          </div>
        )}
        <span className="text-xs text-muted-foreground">Agent {finding.agentId}</span>
      </div>
    </div>
  )
}
