"use client"

import { useState, useEffect, useRef } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import {
  FolderOpen, FileJson, FileText, File, FileCode, 
  ChevronRight, ChevronDown, Download, X, RefreshCw,
  Clock, HardDrive, Eye, Terminal, Activity, Zap
} from "lucide-react"
import { useFindingsExplorer, type FileInfo, type FolderInfo } from "@/hooks/use-findings-explorer"
import type { AgentLogEntry } from "@/lib/api"

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleString([], { 
    month: 'short', 
    day: 'numeric', 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

function getFileIcon(type: string) {
  switch (type) {
    case 'json':
      return <FileJson className="w-4 h-4 text-yellow-500" />
    case 'text':
    case 'log':
      return <FileText className="w-4 h-4 text-blue-500" />
    case 'html':
      return <FileCode className="w-4 h-4 text-orange-500" />
    case 'pdf':
      return <File className="w-4 h-4 text-red-500" />
    default:
      return <File className="w-4 h-4 text-muted-foreground" />
  }
}

function FileItem({ file, onClick }: { file: FileInfo; onClick: () => void }) {
  return (
    <div 
      className="flex items-center gap-2 p-2 rounded-md hover:bg-muted/50 cursor-pointer transition-colors group"
      onClick={onClick}
    >
      {getFileIcon(file.type)}
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium truncate">{file.name}</p>
        <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
          <span className="flex items-center gap-0.5">
            <HardDrive className="w-3 h-3" />
            {formatFileSize(file.size)}
          </span>
          <span className="flex items-center gap-0.5">
            <Clock className="w-3 h-3" />
            {formatDate(file.modified)}
          </span>
        </div>
      </div>
      <Button variant="ghost" size="icon" className="h-6 w-6 opacity-0 group-hover:opacity-100">
        <Eye className="w-3 h-3" />
      </Button>
    </div>
  )
}

function FolderItem({ folder, onFileClick }: { folder: FolderInfo; onFileClick: (file: FileInfo) => void }) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <CollapsibleTrigger className="w-full flex items-center gap-2 p-2 rounded-md hover:bg-muted/50 transition-colors">
        {isOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        <FolderOpen className="w-4 h-4 text-primary" />
        <span className="text-xs font-medium flex-1 text-left truncate">{folder.name}</span>
        <Badge variant="secondary" className="text-[10px] h-4">{folder.file_count}</Badge>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="ml-6 pl-2 border-l border-border/50 mt-1 space-y-0.5">
          {folder.files.map((file) => (
            <FileItem key={file.path} file={file} onClick={() => onFileClick(file)} />
          ))}
        </div>
      </CollapsibleContent>
    </Collapsible>
  )
}

function FileViewer({ file, content, loading, onClose }: { 
  file: FileInfo | null
  content: { type: string; content: any; filename: string } | null
  loading: boolean
  onClose: () => void 
}) {
  if (!file) return null

  const renderContent = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-6 h-6 animate-spin text-muted-foreground" />
        </div>
      )
    }

    if (!content) {
      return (
        <div className="text-center py-8 text-muted-foreground">
          <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">Unable to load file content</p>
        </div>
      )
    }

    switch (content.type) {
      case 'json':
        return (
          <ScrollArea className="h-full">
            <pre className="text-xs sm:text-sm font-mono p-4 sm:p-6 bg-muted/30 rounded-lg whitespace-pre-wrap break-words overflow-x-auto">
              {typeof content.content === 'string' 
                ? content.content 
                : JSON.stringify(content.content, null, 2)}
            </pre>
          </ScrollArea>
        )
      case 'html':
        return (
          <ScrollArea className="h-full">
            <div 
              className="prose prose-sm dark:prose-invert max-w-none p-4 sm:p-6 break-words [&>*]:max-w-full [&_pre]:overflow-x-auto [&_code]:break-words"
              dangerouslySetInnerHTML={{ __html: content.content }}
            />
          </ScrollArea>
        )
      case 'text':
      case 'log':
      case 'csv':
      case 'xml':
        return (
          <ScrollArea className="h-full">
            <pre className="text-xs sm:text-sm font-mono p-4 sm:p-6 bg-muted/30 rounded-lg whitespace-pre-wrap break-words overflow-x-auto">
              {content.content}
            </pre>
          </ScrollArea>
        )
      case 'pdf':
        return (
          <div className="text-center py-8">
            <File className="w-12 h-12 mx-auto mb-3 text-red-500" />
            <p className="text-sm text-muted-foreground mb-3">PDF files are downloaded automatically</p>
            <Button variant="outline" size="sm" asChild>
              <a href={`/api/findings/file/${encodeURIComponent(file.path)}`} download>
                <Download className="w-4 h-4 mr-2" />
                Download PDF
              </a>
            </Button>
          </div>
        )
      default:
        return (
          <div className="text-center py-8 text-muted-foreground">
            <File className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">Preview not available for this file type</p>
          </div>
        )
    }
  }

  return (
    <Dialog open={!!file} onOpenChange={() => onClose()}>
      <DialogContent className="w-[98vw] max-w-[1100px] h-[90vh] max-h-[90vh] flex flex-col overflow-hidden p-4 sm:p-6">
        <DialogHeader className="shrink-0 pb-3">
          <DialogTitle className="flex items-center gap-3 pr-8 text-base sm:text-lg">
            {getFileIcon(file.type)}
            <span className="truncate flex-1 min-w-0 text-sm sm:text-base font-semibold">{file.name}</span>
            <Badge variant="outline" className="text-xs uppercase shrink-0 px-2 py-1">{file.type}</Badge>
          </DialogTitle>
        </DialogHeader>
        <div className="flex items-center gap-3 text-xs text-muted-foreground pb-3 border-b shrink-0 flex-wrap">
          <span className="flex items-center gap-1.5 bg-muted/50 px-2 py-1 rounded">
            <HardDrive className="w-3.5 h-3.5" />
            {formatFileSize(file.size)}
          </span>
          <span className="flex items-center gap-1.5 bg-muted/50 px-2 py-1 rounded">
            <Clock className="w-3.5 h-3.5" />
            {formatDate(file.modified)}
          </span>
          {file.target && (
            <Badge variant="secondary" className="text-xs px-2 py-1">Target: {file.target}</Badge>
          )}
        </div>
        <div className="flex-1 overflow-auto min-h-0 mt-3">
          {renderContent()}
        </div>
      </DialogContent>
    </Dialog>
  )
}

function RealtimeLogEntry({ log, agentId }: { log: AgentLogEntry; agentId: string }) {
  const getLogTypeColor = (type: string) => {
    switch (type) {
      case 'error':
      case 'security_violation':
        return 'text-red-500'
      case 'warning':
      case 'tool_restriction':
        return 'text-yellow-500'
      case 'command':
        return 'text-blue-500'
      case 'coordination':
        return 'text-purple-500'
      default:
        return 'text-muted-foreground'
    }
  }

  return (
    <div className="flex items-start gap-2 py-1 px-2 text-[11px] hover:bg-muted/30 rounded font-mono">
      <span className="text-muted-foreground whitespace-nowrap">
        {new Date(log.timestamp).toLocaleTimeString()}
      </span>
      <Badge variant="outline" className="text-[9px] px-1 py-0 h-4">
        {agentId.substring(0, 8)}
      </Badge>
      <span className={`${getLogTypeColor(log.type)} uppercase text-[9px] font-bold`}>
        [{log.type}]
      </span>
      <span className="flex-1 text-foreground/80 break-all">
        {log.message}
      </span>
    </div>
  )
}

interface AgentRealtimeLogsProps {
  realtimeLogs: { [agentId: string]: AgentLogEntry[] }
  allRealtimeLogs: (AgentLogEntry & { agentId: string })[]
  clearRealtimeLogs: () => void
  scrollRef: React.RefObject<HTMLDivElement | null>
}

function AgentRealtimeLogs({ realtimeLogs, allRealtimeLogs, clearRealtimeLogs, scrollRef }: AgentRealtimeLogsProps) {
  const [selectedAgent, setSelectedAgent] = useState<string>("all")
  const agentIds = Object.keys(realtimeLogs)
  
  const displayLogs = selectedAgent === "all" 
    ? allRealtimeLogs 
    : (realtimeLogs[selectedAgent] || []).map(log => ({ ...log, agentId: selectedAgent }))
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between px-2 pb-2 border-b border-border/50 mb-2">
        <div className="flex items-center gap-2">
          <Activity className="w-3 h-3 text-green-500 animate-pulse" />
          <span className="text-xs text-muted-foreground">
            {displayLogs.length} live events
          </span>
        </div>
        <div className="flex items-center gap-2">
          {agentIds.length > 0 && (
            <select 
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value)}
              className="h-6 text-xs bg-sidebar border border-sidebar-border rounded px-2 text-foreground"
            >
              <option value="all">All Agents ({agentIds.length})</option>
              {agentIds.map(agentId => (
                <option key={agentId} value={agentId}>
                  Agent {agentId.substring(0, 8)} ({realtimeLogs[agentId]?.length || 0})
                </option>
              ))}
            </select>
          )}
          {allRealtimeLogs.length > 0 && (
            <Button 
              variant="ghost" 
              size="sm" 
              className="h-6 text-xs"
              onClick={clearRealtimeLogs}
            >
              Clear
            </Button>
          )}
        </div>
      </div>
      
      {agentIds.length > 1 && selectedAgent === "all" && (
        <div className="flex gap-1 px-2 pb-2 flex-wrap">
          {agentIds.map(agentId => (
            <Badge 
              key={agentId}
              variant="outline" 
              className="text-[9px] cursor-pointer hover:bg-primary/10"
              onClick={() => setSelectedAgent(agentId)}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-green-500 mr-1 animate-pulse" />
              {agentId.substring(0, 8)}
              <span className="ml-1 text-muted-foreground">({realtimeLogs[agentId]?.length || 0})</span>
            </Badge>
          ))}
        </div>
      )}
      
      <ScrollArea className="flex-1">
        <div ref={scrollRef} className="space-y-0.5">
          {displayLogs.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Zap className="w-10 h-10 mx-auto mb-2 opacity-20" />
              <p className="text-sm">No live logs yet</p>
              <p className="text-xs">Real-time agent events appear here</p>
            </div>
          ) : (
            displayLogs.slice(0, 100).map((log, idx) => (
              <RealtimeLogEntry 
                key={`${log.agentId}-${log.timestamp}-${idx}`} 
                log={log} 
                agentId={log.agentId}
              />
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  )
}

export function FindingsExplorer() {
  const { 
    explorer, 
    logs,
    realtimeLogs,
    loading, 
    selectedFile, 
    fileContent, 
    fileLoading,
    openFile, 
    closeFile,
    refetch,
    refetchLogs,
    clearRealtimeLogs
  } = useFindingsExplorer()
  const [activeTab, setActiveTab] = useState<"findings" | "logs" | "realtime">("findings")
  const scrollRef = useRef<HTMLDivElement>(null)
  
  const allRealtimeLogs = Object.entries(realtimeLogs).flatMap(([agentId, logs]) => 
    logs.map(log => ({ ...log, agentId }))
  ).sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
  
  useEffect(() => {
    if (scrollRef.current && activeTab === "realtime") {
      scrollRef.current.scrollTop = 0
    }
  }, [allRealtimeLogs.length, activeTab])

  return (
    <>
      <Card className="flex-1 flex flex-col overflow-hidden">
        <CardHeader className="py-3 px-4 shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FolderOpen className="w-5 h-5 text-primary" />
              <CardTitle className="text-base">Findings Explorer</CardTitle>
              <Badge variant="secondary">{explorer.total_files} files</Badge>
            </div>
            <Button 
              variant="ghost" 
              size="sm" 
              className="h-7"
              onClick={() => { refetch(); refetchLogs(); }}
              disabled={loading}
            >
              <RefreshCw className={`w-3 h-3 mr-1 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent className="flex-1 overflow-hidden p-0">
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "findings" | "logs" | "realtime")} className="h-full flex flex-col">
            <TabsList className="mx-4 mt-2 grid grid-cols-3 h-8">
              <TabsTrigger value="findings" className="text-xs gap-1">
                <FolderOpen className="w-3 h-3" />
                Findings
              </TabsTrigger>
              <TabsTrigger value="realtime" className="text-xs gap-1 relative">
                <Zap className="w-3 h-3" />
                Agents
                {allRealtimeLogs.length > 0 && (
                  <span className="absolute -top-1 -right-1 w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                )}
              </TabsTrigger>
              <TabsTrigger value="logs" className="text-xs gap-1">
                <Terminal className="w-3 h-3" />
                Files
              </TabsTrigger>
            </TabsList>
            
            <TabsContent value="findings" className="flex-1 overflow-hidden m-0 p-2">
              <ScrollArea className="h-full">
                <div className="space-y-1 p-2">
                  {explorer.folders.length === 0 && explorer.root_files.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <FolderOpen className="w-10 h-10 mx-auto mb-2 opacity-20" />
                      <p className="text-sm">No findings yet</p>
                      <p className="text-xs">Start a mission to generate findings</p>
                    </div>
                  ) : (
                    <>
                      {explorer.folders.map((folder) => (
                        <FolderItem 
                          key={folder.path} 
                          folder={folder} 
                          onFileClick={(file) => openFile(file, false)}
                        />
                      ))}
                      {explorer.root_files.length > 0 && (
                        <div className="pt-2 border-t border-border/50 mt-2">
                          <p className="text-[10px] text-muted-foreground mb-1 px-2">Root Files</p>
                          {explorer.root_files.map((file) => (
                            <FileItem 
                              key={file.path} 
                              file={file} 
                              onClick={() => openFile(file, false)}
                            />
                          ))}
                        </div>
                      )}
                    </>
                  )}
                </div>
              </ScrollArea>
            </TabsContent>
            
            <TabsContent value="realtime" className="flex-1 overflow-hidden m-0 p-2">
              <AgentRealtimeLogs 
                realtimeLogs={realtimeLogs}
                allRealtimeLogs={allRealtimeLogs}
                clearRealtimeLogs={clearRealtimeLogs}
                scrollRef={scrollRef}
              />
            </TabsContent>
            
            <TabsContent value="logs" className="flex-1 overflow-hidden m-0 p-2">
              <ScrollArea className="h-full">
                <div className="space-y-1 p-2">
                  {logs.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <Terminal className="w-10 h-10 mx-auto mb-2 opacity-20" />
                      <p className="text-sm">No log files</p>
                      <p className="text-xs">Agent log files will appear here</p>
                    </div>
                  ) : (
                    logs.map((log) => (
                      <FileItem 
                        key={log.path} 
                        file={log} 
                        onClick={() => openFile(log, true)}
                      />
                    ))
                  )}
                </div>
              </ScrollArea>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      <FileViewer 
        file={selectedFile} 
        content={fileContent} 
        loading={fileLoading}
        onClose={closeFile} 
      />
    </>
  )
}
