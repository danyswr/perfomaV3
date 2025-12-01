"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "@/components/ui/resizable";
import {
  Bot,
  Play,
  Shield,
  Zap,
  Target,
  Globe,
  FolderOpen,
  MessageSquare,
  X,
  Download,
  FileJson,
  FileText,
  FileSpreadsheet,
  ChevronRight,
  AlertTriangle,
  Settings,
  Terminal,
  Clock,
  MoreVertical,
  Pause,
  Trash2,
  ExternalLink,
  Check,
  Network,
  Eye,
  EyeOff,
  RefreshCw,
  Send,
  User,
  ListOrdered,
  PanelLeft,
  Monitor,
  Brain,
  Timer,
  Cpu,
  MemoryStick,
  Activity,
  FileDown,
  Wrench,
  Plus,
  GripVertical,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { ResourceMonitor } from "@/components/dashboard/resource-monitor";
import { MissionTimer } from "@/components/dashboard/mission-timer";
import { ModelInstructions } from "@/components/dashboard/model-instructions";
import { FindingsExplorer } from "@/components/dashboard/findings-explorer";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useMission } from "@/hooks/use-mission";
import { useAgents } from "@/hooks/use-agents";
import { useResources } from "@/hooks/use-resources";
import { useFindings } from "@/hooks/use-findings";
import { useChat } from "@/hooks/use-chat";
import { useWebSocket } from "@/hooks/use-websocket";
import { checkBackendHealth, api } from "@/lib/api";
import type {
  MissionConfig,
  Agent,
  Finding,
  StealthOptions,
  CapabilityOptions,
} from "@/lib/types";
import {
  OPENROUTER_MODELS,
  DEFAULT_STEALTH_OPTIONS,
  DEFAULT_CAPABILITY_OPTIONS,
} from "@/lib/types";

import { toast } from "sonner";
import { Save, RotateCcw } from "lucide-react";

interface SaveSessionButtonProps {
  config?: MissionConfig;
}

function SaveSessionButton({ config }: SaveSessionButtonProps) {
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [saveName, setSaveName] = useState("");

  const { mission } = useMission();

  const handleSave = async () => {
    if (!saveName.trim()) {
      toast.error("Please enter a name for this configuration");
      return;
    }
    
    setSaving(true);
    try {
      if (config) {
        const configResponse = await api.saveMissionConfig({
          name: saveName.trim(),
          target: config.target,
          category: config.category,
          custom_instruction: config.customInstruction,
          stealth_mode: config.stealthMode,
          aggressive_mode: config.aggressiveLevel > 2,
          model_name: config.modelName,
          num_agents: config.numAgents,
          execution_duration: config.executionDuration,
          requested_tools: config.requestedTools,
          allowed_tools_only: config.allowedToolsOnly,
        });
        
        if (configResponse.error) {
          toast.error("Config save failed", { description: configResponse.error });
          setSaving(false);
          return;
        }
      }
      
      if (mission.active) {
        const response = await api.saveSession();
        if (response.data) {
          setSaved(true);
          toast.success(`"${saveName}" saved!`, {
            description: `Session ID: ${response.data.session_id.substring(0, 8)}...`,
          });
          setShowSaveDialog(false);
          setSaveName("");
          setTimeout(() => setSaved(false), 3000);
        } else if (response.error) {
          toast.error("Session save failed", { description: response.error });
        }
      } else {
        setSaved(true);
        toast.success(`"${saveName}" saved!`, {
          description: "Configuration saved successfully",
        });
        setShowSaveDialog(false);
        setSaveName("");
        setTimeout(() => setSaved(false), 3000);
      }
    } catch {
      toast.error("Failed to save");
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <Button
        variant={saved ? "default" : "outline"}
        size="sm"
        onClick={() => setShowSaveDialog(true)}
        disabled={saving}
        className={`gap-1.5 ${saved ? "bg-green-600 hover:bg-green-700" : ""}`}
      >
        {saving ? (
          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
        ) : saved ? (
          <Check className="w-3.5 h-3.5" />
        ) : (
          <Save className="w-3.5 h-3.5" />
        )}
        {saved ? "Saved" : "Save"}
      </Button>

      <Dialog open={showSaveDialog} onOpenChange={setShowSaveDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Save Configuration</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Configuration Name</Label>
              <Input
                placeholder="My Security Scan Config"
                value={saveName}
                onChange={(e) => setSaveName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSave()}
              />
            </div>
            {config && (
              <div className="text-xs text-muted-foreground space-y-1 p-3 bg-muted/50 rounded-lg">
                <p><strong>Target:</strong> {config.target || "Not set"}</p>
                <p><strong>Model:</strong> {config.modelName}</p>
                <p><strong>Tools:</strong> {config.requestedTools?.length || 0} selected</p>
                <p><strong>Agents:</strong> {config.numAgents}</p>
              </div>
            )}
            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={() => setShowSaveDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleSave} disabled={saving || !saveName.trim()}>
                {saving ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Save className="w-4 h-4 mr-2" />
                )}
                Save
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

interface MissionSummaryDialogProps {
  open: boolean;
  onClose: () => void;
  target: string;
  executionTime: string;
  reason: string;
  agentLogs: any[];
  findings: any[];
}

function MissionSummaryDialog({ 
  open, 
  onClose, 
  target, 
  executionTime, 
  reason, 
  agentLogs, 
  findings 
}: MissionSummaryDialogProps) {
  const [generating, setGenerating] = useState(false);
  const [summary, setSummary] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [progressStage, setProgressStage] = useState("");
  const [savingToFindings, setSavingToFindings] = useState(false);

  useEffect(() => {
    if (open && !summary) {
      generateSummary();
    }
  }, [open]);

  const generateSummary = async () => {
    setGenerating(true);
    setProgress(0);
    
    const stages = [
      { progress: 15, text: "Collecting agent logs..." },
      { progress: 30, text: "Analyzing execution history..." },
      { progress: 50, text: "Processing findings data..." },
      { progress: 70, text: "Generating AI summary..." },
      { progress: 85, text: "Formatting report..." },
      { progress: 95, text: "Finalizing..." },
    ];
    
    let stageIndex = 0;
    const progressInterval = setInterval(() => {
      if (stageIndex < stages.length) {
        setProgress(stages[stageIndex].progress);
        setProgressStage(stages[stageIndex].text);
        stageIndex++;
      }
    }, 600);

    try {
      const response = await api.generateMissionSummary({
        agent_logs: agentLogs,
        findings: findings,
        target: target,
        execution_time: executionTime,
        reason: reason,
      });

      clearInterval(progressInterval);
      setProgress(100);
      setProgressStage("Complete!");

      if (response.data?.summary) {
        setSummary(response.data.summary);
      } else {
        const severityCounts = {
          critical: findings.filter((f: any) => f.severity === 'critical').length,
          high: findings.filter((f: any) => f.severity === 'high').length,
          medium: findings.filter((f: any) => f.severity === 'medium').length,
          low: findings.filter((f: any) => f.severity === 'low').length,
          info: findings.filter((f: any) => f.severity === 'info').length,
        };
        
        setSummary(`# Mission Summary Report

## Overview
- **Target:** ${target}
- **Duration:** ${executionTime}
- **Status:** ${reason === 'user_stopped' ? 'Stopped by user' : reason === 'completed' ? 'Completed' : reason}
- **Total Findings:** ${findings.length}

## Severity Breakdown
- Critical: ${severityCounts.critical}
- High: ${severityCounts.high}
- Medium: ${severityCounts.medium}
- Low: ${severityCounts.low}
- Info: ${severityCounts.info}

## Agent Activity
- Total log entries processed: ${agentLogs.length}

## Recommendations
Please review the Findings Explorer for detailed vulnerability information and remediation steps.`);
      }
    } catch {
      clearInterval(progressInterval);
      setProgress(100);
      setProgressStage("Complete!");
      setSummary(`# Mission Summary

Unable to generate detailed AI summary. 

**Target:** ${target}
**Duration:** ${executionTime}
**Findings:** ${findings.length}

Please review the Findings Explorer for detailed results.`);
    } finally {
      setGenerating(false);
    }
  };

  const handleSaveToFindings = async () => {
    if (!summary) return;
    
    setSavingToFindings(true);
    try {
      await api.saveFindingsSummary({
        summary: summary,
        target: target,
        execution_time: executionTime,
      });
      toast.success("Summary saved to findings!");
    } catch {
      toast.error("Failed to save summary");
    } finally {
      setSavingToFindings(false);
    }
  };

  const handleClose = () => {
    setSummary(null);
    setProgress(0);
    setProgressStage("");
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="w-[95vw] max-w-3xl max-h-[90vh] flex flex-col p-4 sm:p-6">
        <DialogHeader className="shrink-0">
          <DialogTitle className="flex items-center gap-2 text-base sm:text-lg">
            <Activity className="w-4 h-4 sm:w-5 sm:h-5 text-primary" />
            Mission Summary
          </DialogTitle>
        </DialogHeader>
        
        <div className="flex-1 overflow-hidden min-h-0">
          {generating ? (
            <div className="space-y-4 py-6 sm:py-8">
              <div className="text-center">
                <div className="relative w-16 h-16 sm:w-20 sm:h-20 mx-auto mb-4">
                  <Brain className="w-full h-full text-primary animate-pulse" />
                  <div className="absolute inset-0 border-4 border-primary/20 rounded-full animate-ping" />
                </div>
                <p className="text-sm font-medium mb-2">
                  Analyzing Mission Data
                </p>
                <p className="text-xs text-muted-foreground mb-4">
                  {progressStage || "Initializing..."}
                </p>
              </div>
              <div className="space-y-2">
                <Progress value={progress} className="w-full h-3" />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>{progress}%</span>
                  <span>Processing {findings.length} findings</span>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-2 sm:gap-4 pt-4">
                <div className="text-center p-2 sm:p-3 bg-muted/30 rounded-lg">
                  <p className="text-lg sm:text-xl font-bold text-primary">{findings.length}</p>
                  <p className="text-[10px] sm:text-xs text-muted-foreground">Findings</p>
                </div>
                <div className="text-center p-2 sm:p-3 bg-muted/30 rounded-lg">
                  <p className="text-lg sm:text-xl font-bold text-cyan-500">{agentLogs.length}</p>
                  <p className="text-[10px] sm:text-xs text-muted-foreground">Log Entries</p>
                </div>
                <div className="text-center p-2 sm:p-3 bg-muted/30 rounded-lg">
                  <p className="text-lg sm:text-xl font-bold text-yellow-500">{executionTime}</p>
                  <p className="text-[10px] sm:text-xs text-muted-foreground">Duration</p>
                </div>
              </div>
            </div>
          ) : summary ? (
            <ScrollArea className="h-[50vh] sm:h-[400px]">
              <div className="prose prose-sm dark:prose-invert max-w-none p-3 sm:p-4 bg-muted/30 rounded-lg">
                <pre className="whitespace-pre-wrap text-xs sm:text-sm font-sans leading-relaxed">{summary}</pre>
              </div>
            </ScrollArea>
          ) : null}
        </div>

        <div className="flex flex-col sm:flex-row justify-end gap-2 pt-4 border-t shrink-0">
          <Button variant="outline" onClick={handleClose} className="w-full sm:w-auto">
            Close
          </Button>
          {summary && (
            <>
              <Button 
                variant="outline"
                onClick={handleSaveToFindings}
                disabled={savingToFindings}
                className="w-full sm:w-auto"
              >
                {savingToFindings ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <FileText className="w-4 h-4 mr-2" />
                )}
                Save to Findings
              </Button>
              <Button 
                onClick={() => {
                  navigator.clipboard.writeText(summary);
                  toast.success("Summary copied to clipboard");
                }}
                className="w-full sm:w-auto"
              >
                Copy Summary
              </Button>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

interface RestoreButtonProps {
  onLoadConfig?: (config: any) => void;
}

function RestoreSessionButton({ onLoadConfig }: RestoreButtonProps) {
  const [showDialog, setShowDialog] = useState(false);
  const [activeTab, setActiveTab] = useState<"configs" | "sessions">("configs");
  const [configs, setConfigs] = useState<any[]>([]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingId, setLoadingId] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [configsRes, sessionsRes] = await Promise.all([
        api.listSavedConfigs(),
        api.getSessions()
      ]);
      if (configsRes.data) setConfigs(configsRes.data.configs || []);
      if (sessionsRes.data) setSessions(sessionsRes.data.sessions || []);
    } catch {
      toast.error("Failed to load saved data");
    } finally {
      setLoading(false);
    }
  };

  const handleLoadConfig = async (configId: string) => {
    setLoadingId(configId);
    try {
      const response = await api.getConfigById(configId);
      if (response.data?.config && onLoadConfig) {
        onLoadConfig(response.data.config);
        toast.success("Configuration loaded!");
        setShowDialog(false);
      } else if (response.error) {
        toast.error("Failed to load config", { description: response.error });
      }
    } catch {
      toast.error("Failed to load configuration");
    } finally {
      setLoadingId(null);
    }
  };

  const handleResumeSession = async (sessionId: string) => {
    setLoadingId(sessionId);
    try {
      const response = await api.resumeSession(sessionId);
      if (response.data) {
        toast.success("Session restored!", {
          description: `${response.data.agent_ids.length} agents resumed`,
        });
        setShowDialog(false);
      } else if (response.error) {
        toast.error("Restore failed", { description: response.error });
      }
    } catch {
      toast.error("Failed to restore session");
    } finally {
      setLoadingId(null);
    }
  };

  const handleDeleteConfig = async (configId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.deleteConfig(configId);
      setConfigs(configs.filter(c => c.id !== configId));
      toast.success("Configuration deleted");
    } catch {
      toast.error("Failed to delete");
    }
  };

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        onClick={() => {
          setShowDialog(true);
          loadData();
        }}
        className="gap-1.5"
      >
        <RotateCcw className="w-3.5 h-3.5" />
        Load
      </Button>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Load Saved Configuration</DialogTitle>
          </DialogHeader>
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="configs">Configurations</TabsTrigger>
              <TabsTrigger value="sessions">Sessions</TabsTrigger>
            </TabsList>
            
            <TabsContent value="configs" className="mt-4">
              {loading ? (
                <div className="flex justify-center py-8">
                  <RefreshCw className="w-5 h-5 animate-spin text-muted-foreground" />
                </div>
              ) : configs.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-8">
                  No saved configurations
                </p>
              ) : (
                <ScrollArea className="h-72">
                  <div className="space-y-2">
                    {configs.map((config) => (
                      <div
                        key={config.id}
                        className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 cursor-pointer"
                        onClick={() => handleLoadConfig(config.id)}
                      >
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-sm truncate">{config.name}</p>
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <span className="truncate">{config.target || "No target"}</span>
                            {config.tools_count > 0 && (
                              <Badge variant="secondary" className="text-[10px]">
                                {config.tools_count} tools
                              </Badge>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-1">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={(e) => handleDeleteConfig(config.id, e)}
                            className="h-7 w-7 p-0 text-destructive hover:text-destructive"
                          >
                            <Trash2 className="w-3 h-3" />
                          </Button>
                          {loadingId === config.id ? (
                            <RefreshCw className="w-4 h-4 animate-spin" />
                          ) : (
                            <ChevronRight className="w-4 h-4 text-muted-foreground" />
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              )}
            </TabsContent>
            
            <TabsContent value="sessions" className="mt-4">
              {loading ? (
                <div className="flex justify-center py-8">
                  <RefreshCw className="w-5 h-5 animate-spin text-muted-foreground" />
                </div>
              ) : sessions.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-8">
                  No saved sessions
                </p>
              ) : (
                <ScrollArea className="h-72">
                  <div className="space-y-2">
                    {sessions.map((session) => (
                      <div
                        key={session.id}
                        className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50"
                      >
                        <div className="flex-1">
                          <p className="font-medium text-sm">{session.target}</p>
                          <p className="text-xs text-muted-foreground">
                            {new Date(session.created_at).toLocaleString()}
                          </p>
                        </div>
                        <Button
                          size="sm"
                          onClick={() => handleResumeSession(session.id)}
                          disabled={loadingId === session.id}
                        >
                          {loadingId === session.id ? (
                            <RefreshCw className="w-3 h-3 animate-spin" />
                          ) : (
                            "Resume"
                          )}
                        </Button>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              )}
            </TabsContent>
          </Tabs>
        </DialogContent>
      </Dialog>
    </>
  );
}

export default function Dashboard() {
  const [backendStatus, setBackendStatus] = useState<
    "checking" | "online" | "offline"
  >("checking");
  const [chatOpen, setChatOpen] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [configTab, setConfigTab] = useState("target");
  const [showSummary, setShowSummary] = useState(false);
  const [summaryData, setSummaryData] = useState<{
    target: string;
    executionTime: string;
    reason: string;
    agentLogs: any[];
    findings: any[];
  } | null>(null);

  const { mission, startMission, stopMission } = useMission();
  const { agents, syncAgents, pauseAgent, resumeAgent, removeAgent, addAgent } =
    useAgents();
  const { resources } = useResources();
  const { findings, severitySummary, exportFindings, exportCsv, exportPdf } =
    useFindings();

  const [config, setConfig] = useState<MissionConfig>({
    target: "",
    category: "domain",
    customInstruction: "",
    stealthMode: true,
    aggressiveLevel: 1,
    modelName: "anthropic/claude-3.5-sonnet",
    numAgents: 3,
    stealthOptions: DEFAULT_STEALTH_OPTIONS,
    capabilities: DEFAULT_CAPABILITY_OPTIONS,
    osType: "linux",
    batchSize: 20,
    rateLimitRps: 1.0,
    rateLimitEnabled: false,
    executionDuration: null,
    requestedTools: [],
    allowedToolsOnly: false,
    instructionDelayMs: 0,
    modelDelayMs: 0,
  });
  const [customModelId, setCustomModelId] = useState("");
  const [testingApi, setTestingApi] = useState(false);
  const [apiTestResult, setApiTestResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);
  const [apiTestPassed, setApiTestPassed] = useState(false);
  const [toolInput, setToolInput] = useState("");
  const [agentViewMode, setAgentViewMode] = useState<"list" | "grid">("list");

  useEffect(() => {
    let isMounted = true;
    let isFirstCheck = true;

    const checkHealth = async () => {
      if (!isMounted) return;

      if (isFirstCheck) {
        setBackendStatus("checking");
        isFirstCheck = false;
      }

      const isHealthy = await checkBackendHealth();
      if (isMounted) {
        setBackendStatus(isHealthy ? "online" : "offline");
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 10000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleStartMission = useCallback(async () => {
    if (config.target) {
      const finalConfig = {
        ...config,
        modelName:
          config.modelName === "custom" ? customModelId : config.modelName,
      };
      const agentIds = await startMission(finalConfig);
      if (agentIds) syncAgents(agentIds);
    }
  }, [config, customModelId, startMission, syncAgents]);

  const handleStopMission = useCallback(async () => {
    const duration = mission.duration || 0;
    const mins = Math.floor(duration / 60);
    const secs = duration % 60;
    const executionTime = `${mins}:${secs.toString().padStart(2, '0')}`;
    
    setSummaryData({
      target: config.target || "Unknown",
      executionTime,
      reason: "user_stopped",
      agentLogs: [],
      findings: findings || [],
    });
    setShowSummary(true);
    
    await stopMission();
  }, [config.target, mission.duration, findings, stopMission]);

  const handleLoadConfig = useCallback((savedConfig: any) => {
    setConfig({
      target: savedConfig.target || "",
      category: savedConfig.category || "domain",
      customInstruction: savedConfig.custom_instruction || "",
      stealthMode: savedConfig.stealth_mode ?? true,
      aggressiveLevel: savedConfig.aggressive_mode ? 3 : 1,
      modelName: savedConfig.model_name || "anthropic/claude-3.5-sonnet",
      numAgents: savedConfig.num_agents || 3,
      stealthOptions: DEFAULT_STEALTH_OPTIONS,
      capabilities: DEFAULT_CAPABILITY_OPTIONS,
      osType: "linux",
      batchSize: 20,
      rateLimitRps: 1.0,
      rateLimitEnabled: false,
      executionDuration: savedConfig.execution_duration || null,
      requestedTools: savedConfig.requested_tools || [],
      allowedToolsOnly: savedConfig.allowed_tools_only ?? false,
      instructionDelayMs: savedConfig.instruction_delay_ms || 0,
      modelDelayMs: savedConfig.model_delay_ms || 0,
    });
  }, []);

  const handleTestApi = async () => {
    const isCustomModel = config.modelName === "custom";
    const modelId = isCustomModel ? customModelId : config.modelName;

    if (!modelId || !modelId.trim()) {
      setApiTestResult({
        success: false,
        message: isCustomModel
          ? "Please enter a custom model ID"
          : "Please select a model",
      });
      setApiTestPassed(false);
      return;
    }

    setTestingApi(true);
    setApiTestResult(null);
    setApiTestPassed(false);
    try {
      const selectedModel = OPENROUTER_MODELS.find(
        (m) => m.id === config.modelName,
      );
      const providerName = isCustomModel
        ? "custom"
        : selectedModel?.provider || "OpenRouter";

      const response = await api.testModel({
        provider: providerName,
        model: modelId,
      });

      if (response.error) {
        setApiTestResult({ success: false, message: String(response.error) });
        setApiTestPassed(false);
      } else if (response.data?.status === "error") {
        setApiTestResult({
          success: false,
          message: response.data.message || "API test failed",
        });
        setApiTestPassed(false);
      } else {
        const latencyInfo = response.data?.latency
          ? ` (${response.data.latency})`
          : "";
        setApiTestResult({
          success: true,
          message: `Connected to ${modelId}${latencyInfo}`,
        });
        setApiTestPassed(true);
      }
    } catch {
      setApiTestResult({ success: false, message: "Failed to connect to API" });
      setApiTestPassed(false);
    } finally {
      setTestingApi(false);
    }
  };

  const updateStealthOption = (key: keyof StealthOptions, value: boolean) => {
    setConfig((prev) => ({
      ...prev,
      stealthOptions: { ...prev.stealthOptions, [key]: value },
    }));
  };

  const updateCapability = (key: keyof CapabilityOptions, value: boolean) => {
    setConfig((prev) => ({
      ...prev,
      capabilities: { ...prev.capabilities, [key]: value },
    }));
  };

  const selectAllStealth = (value: boolean) => {
    setConfig((prev) => ({
      ...prev,
      stealthOptions: {
        proxyChain: value,
        torRouting: value,
        vpnChaining: value,
        macSpoofing: value,
        timestampSpoofing: value,
        logWiping: value,
        memoryScrambling: value,
        secureDelete: value,
      },
    }));
  };

  const selectAllCapabilities = (value: boolean) => {
    setConfig((prev) => ({
      ...prev,
      capabilities: {
        packetInjection: value,
        arpSpoof: value,
        mitm: value,
        trafficHijack: value,
        realtimeManipulation: value,
        corsExploitation: value,
        ssrfChaining: value,
        deserializationExploit: value,
        wafBypass: value,
        bacTesting: value,
        websocketHijack: value,
      },
    }));
  };

  const isAllStealthSelected = Object.values(config.stealthOptions).every(
    (v) => v,
  );
  const isAllCapabilitiesSelected = Object.values(config.capabilities).every(
    (v) => v,
  );

  return (
    <div className="h-screen w-screen overflow-hidden bg-background flex flex-col">
      <header className="h-14 border-b border-border flex items-center justify-between px-4 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg overflow-hidden">
            <img
              src="/performa-logo.png"
              alt="Performa"
              className="w-full h-full object-cover"
            />
          </div>
          <div>
            <h1 className="font-bold text-lg">Perfoma</h1>
            <p className="text-xs text-muted-foreground">
              Autonomous Security Agent
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Badge
            variant={
              backendStatus === "online"
                ? "default"
                : backendStatus === "offline"
                  ? "destructive"
                  : "secondary"
            }
          >
            {backendStatus === "online"
              ? "Online"
              : backendStatus === "offline"
                ? "Offline"
                : "Connecting..."}
          </Badge>
          {mission.active && (
            <MissionTimer
              active={mission.active}
              startTime={mission.startTime}
              duration={mission.duration}
              maxDuration={mission.maxDuration}
            />
          )}
          <SaveSessionButton config={config} />
          <RestoreSessionButton onLoadConfig={handleLoadConfig} />
          {mission.active && (
            <Button variant="destructive" size="sm" onClick={handleStopMission}>
              Stop Mission
            </Button>
          )}
        </div>
      </header>

      {summaryData && (
        <MissionSummaryDialog
          open={showSummary}
          onClose={() => {
            setShowSummary(false);
            setSummaryData(null);
          }}
          target={summaryData.target}
          executionTime={summaryData.executionTime}
          reason={summaryData.reason}
          agentLogs={summaryData.agentLogs}
          findings={summaryData.findings}
        />
      )}

      <div className="flex-1 flex overflow-hidden">
        <ChatSidebar open={chatOpen} onToggle={() => setChatOpen(!chatOpen)} />

        <div className="flex-1 p-4 flex flex-col gap-4 overflow-hidden">
          <ResourceMonitor />

          <div className="flex-1 flex gap-4 overflow-hidden">
            <Card className="flex-1 flex flex-col overflow-hidden">
              <CardHeader className="py-3 px-4 shrink-0">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Bot className="w-5 h-5 text-primary" />
                    <CardTitle className="text-base">Active Agents</CardTitle>
                    <Badge variant="secondary">{agents.length}/10</Badge>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex border border-border rounded-md overflow-hidden">
                      <Button
                        variant={
                          agentViewMode === "list" ? "secondary" : "ghost"
                        }
                        size="sm"
                        onClick={() => setAgentViewMode("list")}
                        className="h-7 px-2 rounded-none"
                      >
                        <ListOrdered className="w-3 h-3" />
                      </Button>
                      <Button
                        variant={
                          agentViewMode === "grid" ? "secondary" : "ghost"
                        }
                        size="sm"
                        onClick={() => setAgentViewMode("grid")}
                        className="h-7 px-2 rounded-none"
                      >
                        <Network className="w-3 h-3" />
                      </Button>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        addAgent({
                          target: config.target,
                          category: config.category,
                          model_name: config.modelName,
                          stealth_mode: config.stealthMode,
                          aggressive_mode: config.aggressiveLevel > 2,
                        })
                      }
                      disabled={
                        agents.length >= 10 || backendStatus !== "online"
                      }
                      className="h-7 text-xs"
                    >
                      <Plus className="w-3 h-3 mr-1" />
                      Add
                    </Button>
                    {agents.length > 0 && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => agents.forEach((a) => removeAgent(a.id))}
                        className="h-7 text-xs text-destructive hover:text-destructive"
                      >
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="flex-1 overflow-hidden p-2">
                {agents.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-muted-foreground">
                    <Bot className="w-12 h-12 mb-2 opacity-20" />
                    <p className="text-sm">No agents deployed</p>
                    <p className="text-xs">
                      Configure and start a mission or add agents manually
                    </p>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        addAgent({
                          target: config.target,
                          category: config.category,
                          model_name: config.modelName,
                        })
                      }
                      disabled={backendStatus !== "online"}
                      className="mt-3"
                    >
                      <Bot className="w-4 h-4 mr-2" />
                      Add First Agent
                    </Button>
                  </div>
                ) : (
                  <ScrollArea className="h-full">
                    <div
                      className={
                        agentViewMode === "grid"
                          ? "grid grid-cols-2 gap-2 p-2"
                          : "flex flex-col gap-2 p-2"
                      }
                    >
                      {agents.map((agent) => (
                        <AgentCard
                          key={agent.id}
                          agent={agent}
                          viewMode={agentViewMode}
                          onDetail={() => setSelectedAgent(agent)}
                          onPause={() => pauseAgent(agent.id)}
                          onResume={() => resumeAgent(agent.id)}
                          onRemove={() => removeAgent(agent.id)}
                        />
                      ))}
                    </div>
                  </ScrollArea>
                )}
              </CardContent>
            </Card>

            <div className="w-96 shrink-0">
              <FindingsExplorer />
            </div>
          </div>
        </div>

        <div className="w-96 border-l border-border flex flex-col overflow-hidden shrink-0">
          <div className="p-4 border-b border-border shrink-0">
            <div className="flex items-center gap-2 mb-3">
              <Settings className="w-5 h-5 text-primary" />
              <h2 className="font-semibold">Mission Config</h2>
            </div>
            <Tabs
              value={configTab}
              onValueChange={setConfigTab}
              className="w-full"
            >
              <TabsList className="grid w-full grid-cols-5 h-8">
                <TabsTrigger value="target" className="text-xs">
                  Target
                </TabsTrigger>
                <TabsTrigger value="mode" className="text-xs">
                  Mode
                </TabsTrigger>
                <TabsTrigger value="tools" className="text-xs">
                  Tools
                </TabsTrigger>
                <TabsTrigger value="stealth" className="text-xs">
                  Stealth
                </TabsTrigger>
                <TabsTrigger value="caps" className="text-xs">
                  Caps
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </div>

          <ScrollArea className="flex-1">
            <div className="p-4 space-y-4">
              {configTab === "target" && (
                <>
                  <div className="space-y-2">
                    <Label className="text-xs font-medium">Target</Label>
                    <Input
                      placeholder="example.com or /path/to/file"
                      value={config.target}
                      onChange={(e) =>
                        setConfig({ ...config, target: e.target.value })
                      }
                      className="h-9"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label className="text-xs font-medium">Category</Label>
                    <div className="grid grid-cols-2 gap-2">
                      <Button
                        variant={
                          config.category === "domain" ? "default" : "outline"
                        }
                        size="sm"
                        onClick={() =>
                          setConfig({ ...config, category: "domain" })
                        }
                        className="h-9"
                      >
                        <Globe className="w-4 h-4 mr-2" />
                        URL/Domain
                      </Button>
                      <Button
                        variant={
                          config.category === "path" ? "default" : "outline"
                        }
                        size="sm"
                        onClick={() =>
                          setConfig({ ...config, category: "path" })
                        }
                        className="h-9"
                      >
                        <FolderOpen className="w-4 h-4 mr-2" />
                        Path (File)
                      </Button>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-xs font-medium">AI Model</Label>
                    <Select
                      value={config.modelName}
                      onValueChange={(v) =>
                        setConfig({ ...config, modelName: v })
                      }
                    >
                      <SelectTrigger className="h-9">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {OPENROUTER_MODELS.map((m) => (
                          <SelectItem key={m.id} value={m.id}>
                            <span className="flex items-center gap-2">
                              {m.name}
                              <Badge variant="outline" className="text-xs">
                                {m.provider}
                              </Badge>
                            </span>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {(config.modelName === "custom" ||
                      config.modelName === "ollama") && (
                      <div className="space-y-2 mt-2 p-3 rounded-lg bg-muted/30 border border-border">
                        <Label className="text-xs font-medium">
                          {config.modelName === "ollama"
                            ? "Ollama Model Name"
                            : "Custom Model ID"}
                        </Label>
                        <Input
                          placeholder={
                            config.modelName === "ollama"
                              ? "llama3.2, codellama, mistral..."
                              : "openai/gpt-4-turbo-preview"
                          }
                          value={customModelId}
                          onChange={(e) => setCustomModelId(e.target.value)}
                          className="h-9"
                        />
                        {config.modelName === "ollama" && (
                          <p className="text-xs text-muted-foreground">
                            Enter your locally installed Ollama model name
                          </p>
                        )}
                      </div>
                    )}
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleTestApi}
                        disabled={
                          testingApi ||
                          ((config.modelName === "custom" ||
                            config.modelName === "ollama") &&
                            !customModelId.trim())
                        }
                        className="flex-1 h-8"
                      >
                        {testingApi ? "Testing..." : "Test API"}
                      </Button>
                      <Button variant="ghost" size="sm" asChild className="h-8">
                        <a
                          href="https://openrouter.ai/models"
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      </Button>
                    </div>
                    {apiTestResult && (
                      <div
                        className={`text-xs p-2 rounded ${apiTestResult.success ? "bg-emerald-500/10 text-emerald-500" : "bg-red-500/10 text-red-500"}`}
                      >
                        {apiTestResult.success ? (
                          <Check className="w-3 h-3 inline mr-1" />
                        ) : (
                          <X className="w-3 h-3 inline mr-1" />
                        )}
                        {apiTestResult.message}
                      </div>
                    )}
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label className="text-xs font-medium">Agents</Label>
                      <Badge variant="secondary">{config.numAgents}</Badge>
                    </div>
                    <Slider
                      value={[config.numAgents]}
                      onValueChange={(v) =>
                        setConfig({ ...config, numAgents: v[0] })
                      }
                      min={1}
                      max={10}
                      step={1}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label className="text-xs font-medium">
                      Custom Instructions
                    </Label>
                    <Textarea
                      placeholder="Specific objectives, constraints..."
                      value={config.customInstruction}
                      onChange={(e) =>
                        setConfig({
                          ...config,
                          customInstruction: e.target.value,
                        })
                      }
                      className="min-h-[80px] resize-none"
                    />
                  </div>
                </>
              )}

              {configTab === "mode" && (
                <>
                  <div className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
                    <div className="flex items-center gap-3">
                      <Shield className="w-4 h-4 text-primary" />
                      <div>
                        <p className="text-sm font-medium">Stealth Mode</p>
                        <p className="text-xs text-muted-foreground">
                          Evasive scanning
                        </p>
                      </div>
                    </div>
                    <Switch
                      checked={config.stealthMode}
                      onCheckedChange={(v) =>
                        setConfig({ ...config, stealthMode: v })
                      }
                    />
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label className="text-xs font-medium flex items-center gap-2">
                        <Zap className="w-4 h-4 text-yellow-500" />
                        Aggressive Level
                      </Label>
                      <Badge variant="secondary">
                        {config.aggressiveLevel}
                      </Badge>
                    </div>
                    <Slider
                      value={[config.aggressiveLevel]}
                      onValueChange={(v) =>
                        setConfig({ ...config, aggressiveLevel: v[0] })
                      }
                      min={1}
                      max={5}
                      step={1}
                    />
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>1 - Minimal</span>
                      <span>5 - Maximum</span>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-xs font-medium flex items-center gap-2">
                      <Monitor className="w-4 h-4 text-blue-500" />
                      Operating System
                    </Label>
                    <p className="text-xs text-muted-foreground mb-2">
                      Select the target OS for command execution
                    </p>
                    <div className="grid grid-cols-2 gap-2">
                      <Button
                        variant={
                          config.osType === "linux" ? "default" : "outline"
                        }
                        size="sm"
                        onClick={() =>
                          setConfig({ ...config, osType: "linux" })
                        }
                        className="h-10 gap-2"
                      >
                        <Terminal className="w-4 h-4" />
                        Linux
                      </Button>
                      <Button
                        variant={
                          config.osType === "windows" ? "default" : "outline"
                        }
                        size="sm"
                        onClick={() =>
                          setConfig({ ...config, osType: "windows" })
                        }
                        className="h-10 gap-2"
                      >
                        <Monitor className="w-4 h-4" />
                        Windows
                      </Button>
                    </div>
                    <p className="text-[10px] text-muted-foreground">
                      {config.osType === "linux"
                        ? "Commands will execute via Bash shell"
                        : "Commands will execute via PowerShell"}
                    </p>
                  </div>
                </>
              )}

              {configTab === "tools" && (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label className="text-xs font-medium flex items-center gap-2">
                        <Timer className="w-4 h-4 text-orange-500" />
                        Execution Duration
                      </Label>
                      <Badge variant="secondary">
                        {config.executionDuration
                          ? `${config.executionDuration} min`
                          : "Until stopped"}
                      </Badge>
                    </div>
                    <Select
                      value={
                        config.executionDuration?.toString() || "unlimited"
                      }
                      onValueChange={(v) =>
                        setConfig({
                          ...config,
                          executionDuration:
                            v === "unlimited" ? null : parseInt(v),
                        })
                      }
                    >
                      <SelectTrigger className="h-9">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="10">10 minutes</SelectItem>
                        <SelectItem value="20">20 minutes</SelectItem>
                        <SelectItem value="30">30 minutes</SelectItem>
                        <SelectItem value="60">60 minutes</SelectItem>
                        <SelectItem value="unlimited">Until stopped</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label className="text-xs font-medium flex items-center gap-2">
                        <Activity className="w-4 h-4 text-blue-500" />
                        Rate Limit (req/sec)
                      </Label>
                      <Badge variant="secondary">
                        {config.rateLimitRps} RPS
                      </Badge>
                    </div>
                    <Slider
                      value={[config.rateLimitRps * 10]}
                      onValueChange={(v) =>
                        setConfig({ ...config, rateLimitRps: v[0] / 10 })
                      }
                      min={1}
                      max={50}
                      step={1}
                    />
                    <div className="flex justify-between text-[10px] text-muted-foreground">
                      <span>0.1 - Slow</span>
                      <span>5.0 - Fast</span>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label className="text-xs font-medium flex items-center gap-2">
                        <Brain className="w-4 h-4 text-purple-500" />
                        Batch Size (predictions)
                      </Label>
                      <Badge variant="secondary">{config.batchSize}</Badge>
                    </div>
                    <Slider
                      value={[config.batchSize]}
                      onValueChange={(v) =>
                        setConfig({ ...config, batchSize: v[0] })
                      }
                      min={5}
                      max={30}
                      step={5}
                    />
                    <p className="text-[10px] text-muted-foreground">
                      Higher batch size = fewer API calls, more tokens per call
                    </p>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label className="text-xs font-medium flex items-center gap-2">
                        <Clock className="w-4 h-4 text-cyan-500" />
                        Instruction Delay
                      </Label>
                      <Badge variant="secondary">
                        {config.instructionDelayMs === 0 
                          ? "No delay" 
                          : `${(config.instructionDelayMs / 1000).toFixed(1)}s`}
                      </Badge>
                    </div>
                    <Slider
                      value={[config.instructionDelayMs]}
                      onValueChange={(v) =>
                        setConfig({ ...config, instructionDelayMs: v[0] })
                      }
                      min={0}
                      max={10000}
                      step={500}
                    />
                    <p className="text-[10px] text-muted-foreground">
                      Delay between each agent instruction (0-10 seconds)
                    </p>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label className="text-xs font-medium flex items-center gap-2">
                        <Timer className="w-4 h-4 text-yellow-500" />
                        Model Response Delay
                      </Label>
                      <Badge variant="secondary">
                        {config.modelDelayMs === 0 
                          ? "No delay" 
                          : `${(config.modelDelayMs / 1000).toFixed(1)}s`}
                      </Badge>
                    </div>
                    <Slider
                      value={[config.modelDelayMs]}
                      onValueChange={(v) =>
                        setConfig({ ...config, modelDelayMs: v[0] })
                      }
                      min={0}
                      max={5000}
                      step={250}
                    />
                    <p className="text-[10px] text-muted-foreground">
                      Delay before model generates response (0-5 seconds)
                    </p>
                  </div>

                  <div className="border-t border-border pt-4 space-y-2">
                    <Label className="text-xs font-medium flex items-center gap-2">
                      <Wrench className="w-4 h-4 text-primary" />
                      Allowed Tools Configuration
                    </Label>
                    <p className="text-xs text-muted-foreground">
                      Specify which tools the AI agent is allowed to use.
                    </p>
                  </div>

                  <div className="flex items-center justify-between p-3 rounded-lg bg-destructive/10 border border-destructive/20">
                    <div className="space-y-1">
                      <Label className="text-xs font-medium flex items-center gap-2 text-destructive">
                        <Shield className="w-4 h-4" />
                        Strict Mode (ONLY Allowed Tools)
                      </Label>
                      <p className="text-[10px] text-muted-foreground">
                        When enabled, agent can ONLY use tools you specify below. All other tools will be blocked.
                      </p>
                    </div>
                    <Switch
                      checked={config.allowedToolsOnly}
                      onCheckedChange={(checked) =>
                        setConfig({ ...config, allowedToolsOnly: checked })
                      }
                    />
                  </div>

                  <div className="flex gap-2">
                    <Input
                      placeholder="e.g., nmap, sqlmap, nikto..."
                      value={toolInput}
                      onChange={(e) => setToolInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && toolInput.trim()) {
                          e.preventDefault();
                          if (
                            !config.requestedTools.includes(
                              toolInput.trim().toLowerCase(),
                            )
                          ) {
                            setConfig({
                              ...config,
                              requestedTools: [
                                ...config.requestedTools,
                                toolInput.trim().toLowerCase(),
                              ],
                            });
                          }
                          setToolInput("");
                        }
                      }}
                      className="h-9 flex-1"
                    />
                    <Button
                      size="sm"
                      className="h-9"
                      onClick={() => {
                        if (
                          toolInput.trim() &&
                          !config.requestedTools.includes(
                            toolInput.trim().toLowerCase(),
                          )
                        ) {
                          setConfig({
                            ...config,
                            requestedTools: [
                              ...config.requestedTools,
                              toolInput.trim().toLowerCase(),
                            ],
                          });
                          setToolInput("");
                        }
                      }}
                      disabled={!toolInput.trim()}
                    >
                      <Plus className="w-4 h-4 mr-1" />
                      Add
                    </Button>
                  </div>

                  {config.requestedTools.length > 0 ? (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-muted-foreground">
                          Priority Tools ({config.requestedTools.length})
                        </span>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 text-xs text-destructive hover:text-destructive"
                          onClick={() =>
                            setConfig({ ...config, requestedTools: [] })
                          }
                        >
                          Clear All
                        </Button>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {config.requestedTools.map((tool, index) => (
                          <div
                            key={tool}
                            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-primary/10 border border-primary/20 group"
                          >
                            <Badge
                              variant="secondary"
                              className="text-[10px] h-4 px-1"
                            >
                              {index + 1}
                            </Badge>
                            <Wrench className="w-3 h-3 text-primary" />
                            <span className="text-xs font-medium">{tool}</span>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-4 w-4 opacity-60 hover:opacity-100 hover:bg-destructive/20"
                              onClick={() =>
                                setConfig({
                                  ...config,
                                  requestedTools: config.requestedTools.filter(
                                    (t) => t !== tool,
                                  ),
                                })
                              }
                            >
                              <X className="w-3 h-3" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-4 border border-dashed border-border rounded-lg">
                      <Wrench className="w-6 h-6 mx-auto mb-1 text-muted-foreground opacity-30" />
                      <p className="text-xs text-muted-foreground">
                        No tools requested
                      </p>
                    </div>
                  )}

                  <div className="space-y-2">
                    <Label className="text-xs font-medium">
                      Quick Add Tools
                    </Label>
                    <div className="flex flex-wrap gap-1">
                      {[
                        "nmap",
                        "sqlmap",
                        "nikto",
                        "dirb",
                        "gobuster",
                        "wfuzz",
                        "hydra",
                        "ffuf",
                        "nuclei",
                        "subfinder",
                      ].map((tool) => (
                        <Button
                          key={tool}
                          variant="outline"
                          size="sm"
                          className="h-6 text-[10px]"
                          onClick={() => {
                            if (!config.requestedTools.includes(tool)) {
                              setConfig({
                                ...config,
                                requestedTools: [
                                  ...config.requestedTools,
                                  tool,
                                ],
                              });
                            }
                          }}
                          disabled={config.requestedTools.includes(tool)}
                        >
                          {config.requestedTools.includes(tool) ? (
                            <Check className="w-3 h-3 mr-1" />
                          ) : (
                            <Plus className="w-3 h-3 mr-1" />
                          )}
                          {tool}
                        </Button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {configTab === "stealth" && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-xs text-muted-foreground">
                      Advanced stealth capabilities
                    </p>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => selectAllStealth(!isAllStealthSelected)}
                      className="h-6 text-xs"
                    >
                      <Check className="w-3 h-3 mr-1" />
                      {isAllStealthSelected ? "Unselect All" : "Select All"}
                    </Button>
                  </div>
                  <StealthToggle
                    label="ProxyChain"
                    desc="Multi-hop proxy routing"
                    checked={config.stealthOptions.proxyChain}
                    onChange={(v) => updateStealthOption("proxyChain", v)}
                  />
                  <StealthToggle
                    label="Tor Routing"
                    desc="Onion network routing"
                    checked={config.stealthOptions.torRouting}
                    onChange={(v) => updateStealthOption("torRouting", v)}
                  />
                  <StealthToggle
                    label="VPN Chaining"
                    desc="Multi-VPN tunneling"
                    checked={config.stealthOptions.vpnChaining}
                    onChange={(v) => updateStealthOption("vpnChaining", v)}
                  />
                  <StealthToggle
                    label="MAC Spoofing"
                    desc="Hardware address masking"
                    checked={config.stealthOptions.macSpoofing}
                    onChange={(v) => updateStealthOption("macSpoofing", v)}
                  />
                  <StealthToggle
                    label="Timestamp Spoofing"
                    desc="Time manipulation"
                    checked={config.stealthOptions.timestampSpoofing}
                    onChange={(v) =>
                      updateStealthOption("timestampSpoofing", v)
                    }
                  />
                  <StealthToggle
                    label="Log Wiping"
                    desc="Evidence removal"
                    checked={config.stealthOptions.logWiping}
                    onChange={(v) => updateStealthOption("logWiping", v)}
                  />
                  <StealthToggle
                    label="Memory Scrambling"
                    desc="RAM obfuscation"
                    checked={config.stealthOptions.memoryScrambling}
                    onChange={(v) => updateStealthOption("memoryScrambling", v)}
                  />
                  <StealthToggle
                    label="Secure Delete"
                    desc="7-pass overwrite"
                    checked={config.stealthOptions.secureDelete}
                    onChange={(v) => updateStealthOption("secureDelete", v)}
                  />
                </div>
              )}

              {configTab === "caps" && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-xs text-muted-foreground">
                      Agent capabilities
                    </p>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        selectAllCapabilities(!isAllCapabilitiesSelected)
                      }
                      className="h-6 text-xs"
                    >
                      <Check className="w-3 h-3 mr-1" />
                      {isAllCapabilitiesSelected
                        ? "Unselect All"
                        : "Select All"}
                    </Button>
                  </div>
                  <CapToggle
                    label="Packet Injection"
                    checked={config.capabilities.packetInjection}
                    onChange={(v) => updateCapability("packetInjection", v)}
                  />
                  <CapToggle
                    label="ARP Spoof"
                    checked={config.capabilities.arpSpoof}
                    onChange={(v) => updateCapability("arpSpoof", v)}
                  />
                  <CapToggle
                    label="MITM Attack"
                    checked={config.capabilities.mitm}
                    onChange={(v) => updateCapability("mitm", v)}
                  />
                  <CapToggle
                    label="Traffic Hijack"
                    checked={config.capabilities.trafficHijack}
                    onChange={(v) => updateCapability("trafficHijack", v)}
                  />
                  <CapToggle
                    label="Realtime Manipulation"
                    checked={config.capabilities.realtimeManipulation}
                    onChange={(v) =>
                      updateCapability("realtimeManipulation", v)
                    }
                  />
                  <CapToggle
                    label="CORS Exploitation"
                    checked={config.capabilities.corsExploitation}
                    onChange={(v) => updateCapability("corsExploitation", v)}
                  />
                  <CapToggle
                    label="SSRF Chaining"
                    checked={config.capabilities.ssrfChaining}
                    onChange={(v) => updateCapability("ssrfChaining", v)}
                  />
                  <CapToggle
                    label="Deserialization Exploit"
                    checked={config.capabilities.deserializationExploit}
                    onChange={(v) =>
                      updateCapability("deserializationExploit", v)
                    }
                  />
                  <CapToggle
                    label="WAF Bypass"
                    checked={config.capabilities.wafBypass}
                    onChange={(v) => updateCapability("wafBypass", v)}
                  />
                  <CapToggle
                    label="BAC Testing"
                    checked={config.capabilities.bacTesting}
                    onChange={(v) => updateCapability("bacTesting", v)}
                  />
                  <CapToggle
                    label="WebSocket Hijack"
                    checked={config.capabilities.websocketHijack}
                    onChange={(v) => updateCapability("websocketHijack", v)}
                  />
                </div>
              )}
            </div>
          </ScrollArea>

          <div className="p-4 border-t border-border shrink-0 space-y-2">
            {!apiTestPassed && config.target.trim() && (
              <p className="text-xs text-yellow-500 text-center">
                Test API first before starting mission
              </p>
            )}
            {!config.target.trim() && (
              <p className="text-xs text-muted-foreground text-center">
                Enter a target to start mission
              </p>
            )}
            {backendStatus !== "online" && (
              <p className="text-xs text-red-500 text-center">
                Waiting for backend connection...
              </p>
            )}
            <Button
              onClick={handleStartMission}
              disabled={
                !config.target.trim() ||
                mission.active ||
                backendStatus !== "online"
              }
              className="w-full gap-2"
            >
              <Play className="w-4 h-4" />
              {mission.active ? "Mission Running..." : "Start Mission"}
            </Button>
          </div>
        </div>
      </div>

      <AgentDetailModal
        agent={selectedAgent}
        onClose={() => setSelectedAgent(null)}
      />
    </div>
  );
}

function formatExecutionTime(timeStr: string | undefined): string {
  if (!timeStr) return "00:00";
  const parts = timeStr.split(":").map((p) => {
    const num = parseInt(p, 10);
    return isNaN(num) ? 0 : num;
  });
  if (parts.length === 3) {
    const totalMins = parts[0] * 60 + parts[1];
    return `${totalMins.toString().padStart(2, "0")}:${parts[2].toString().padStart(2, "0")}`;
  } else if (parts.length === 2) {
    return `${parts[0].toString().padStart(2, "0")}:${parts[1].toString().padStart(2, "0")}`;
  }
  return "00:00";
}

function AgentDetailModal({
  agent,
  onClose,
}: {
  agent: Agent | null;
  onClose: () => void;
}) {
  const [cpuHistory, setCpuHistory] = useState<
    { value: number; time: string }[]
  >([]);
  const [memHistory, setMemHistory] = useState<
    { value: number; time: string }[]
  >([]);
  const [displayTime, setDisplayTime] = useState(
    formatExecutionTime(agent?.executionTime),
  );

  useEffect(() => {
    if (!agent) return;

    const generateData = () => {
      const now = new Date();
      const time = now.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });

      setCpuHistory((prev) => {
        const newData = [
          ...prev,
          {
            value: Math.max(
              0,
              Math.min(100, agent.cpuUsage + Math.random() * 10 - 5),
            ),
            time,
          },
        ];
        return newData.slice(-20);
      });

      setMemHistory((prev) => {
        const newData = [
          ...prev,
          {
            value: Math.max(0, agent.memoryUsage + Math.random() * 20 - 10),
            time,
          },
        ];
        return newData.slice(-20);
      });
    };

    generateData();
    const interval = setInterval(generateData, 2000);
    return () => clearInterval(interval);
  }, [agent]);

  useEffect(() => {
    if (agent) setDisplayTime(formatExecutionTime(agent.executionTime));
  }, [agent?.executionTime]);

  useEffect(() => {
    if (!agent || agent.status !== "running") return;

    const parseTime = (timeStr: string): number => {
      const parts = timeStr.split(":").map((p) => parseInt(p, 10) || 0);
      if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
      if (parts.length === 2) return parts[0] * 60 + parts[1];
      return 0;
    };

    const formatSeconds = (totalSeconds: number): string => {
      const mins = Math.floor(totalSeconds / 60);
      const secs = Math.floor(totalSeconds % 60);
      return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
    };

    let baseSeconds = parseTime(formatExecutionTime(agent.executionTime));
    const interval = setInterval(() => {
      baseSeconds += 1;
      setDisplayTime(formatSeconds(baseSeconds));
    }, 1000);

    return () => clearInterval(interval);
  }, [agent?.status, agent?.executionTime]);

  const getCpuColor = (value: number) => {
    if (value >= 80) return "text-red-500";
    if (value >= 60) return "text-yellow-500";
    return "text-emerald-500";
  };

  if (!agent) return null;

  return (
    <Dialog open={!!agent} onOpenChange={() => onClose()}>
      <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-primary" />
            Agent-{agent.displayId || agent.id} Details
            <Badge
              variant={
                agent.status === "running"
                  ? "default"
                  : agent.status === "paused"
                    ? "secondary"
                    : "outline"
              }
              className="ml-2 capitalize"
            >
              {agent.status}
            </Badge>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="p-3 rounded-lg bg-primary/10 border border-primary/20">
              <div className="flex items-center gap-2 mb-1">
                <Timer className="w-4 h-4 text-primary" />
                <span className="text-xs text-muted-foreground">
                  Execution Time
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xl font-mono font-bold text-primary">
                  {displayTime}
                </span>
                {agent.status === "running" && (
                  <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                )}
              </div>
            </div>

            <div className="p-3 rounded-lg bg-muted/30 border">
              <div className="flex items-center gap-2 mb-1">
                <Cpu className="w-4 h-4 text-muted-foreground" />
                <span className="text-xs text-muted-foreground">CPU Usage</span>
              </div>
              <span
                className={`text-lg font-mono font-semibold ${getCpuColor(agent.cpuUsage)}`}
              >
                {agent.cpuUsage}%
              </span>
              <Progress value={agent.cpuUsage} className="h-1.5 mt-1" />
            </div>

            <div
              className={`p-3 rounded-lg border ${agent.memoryUsage > 1024 ? "bg-red-500/10 border-red-500/30" : agent.memoryUsage > 512 ? "bg-yellow-500/10 border-yellow-500/30" : "bg-muted/30"}`}
            >
              <div className="flex items-center gap-2 mb-1">
                <MemoryStick
                  className={`w-4 h-4 ${agent.memoryUsage > 1024 ? "text-red-500" : agent.memoryUsage > 512 ? "text-yellow-500" : "text-muted-foreground"}`}
                />
                <span className="text-xs text-muted-foreground">
                  Memory Used
                </span>
              </div>
              <span
                className={`text-lg font-mono font-semibold ${agent.memoryUsage > 1024 ? "text-red-500" : agent.memoryUsage > 512 ? "text-yellow-500" : "text-blue-500"}`}
              >
                {agent.memoryUsage}MB
              </span>
              <Progress
                value={Math.min(agent.memoryUsage / 10, 100)}
                className="h-1.5 mt-1"
              />
            </div>
          </div>

          <div className="p-3 rounded-lg bg-black/80 font-mono text-sm text-green-400 border border-green-900/30">
            <div className="flex items-center gap-2 mb-2">
              <Terminal className="w-4 h-4 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">
                Last Command
              </span>
            </div>
            <p className="text-sm">
              {agent.lastCommand || "Waiting for command..."}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-lg border bg-card">
              <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
                <Cpu className="w-4 h-4 text-blue-500" />
                CPU Usage History
              </h4>
              <div className="h-32">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={cpuHistory}>
                    <defs>
                      <linearGradient
                        id="modalCpuGradient"
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                      >
                        <stop
                          offset="5%"
                          stopColor="#3b82f6"
                          stopOpacity={0.3}
                        />
                        <stop
                          offset="95%"
                          stopColor="#3b82f6"
                          stopOpacity={0}
                        />
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="time" hide />
                    <YAxis domain={[0, 100]} hide />
                    <Tooltip
                      contentStyle={{
                        background: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                        fontSize: "12px",
                      }}
                      formatter={(value: number) => [
                        `${value.toFixed(1)}%`,
                        "CPU",
                      ]}
                    />
                    <Area
                      type="monotone"
                      dataKey="value"
                      stroke="#3b82f6"
                      fill="url(#modalCpuGradient)"
                      strokeWidth={2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="p-4 rounded-lg border bg-card">
              <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
                <MemoryStick className="w-4 h-4 text-emerald-500" />
                Memory Usage History
              </h4>
              <div className="h-32">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={memHistory}>
                    <defs>
                      <linearGradient
                        id="modalMemGradient"
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                      >
                        <stop
                          offset="5%"
                          stopColor="#10b981"
                          stopOpacity={0.3}
                        />
                        <stop
                          offset="95%"
                          stopColor="#10b981"
                          stopOpacity={0}
                        />
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="time" hide />
                    <YAxis domain={[0, "auto"]} hide />
                    <Tooltip
                      contentStyle={{
                        background: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "8px",
                        fontSize: "12px",
                      }}
                      formatter={(value: number) => [
                        `${value.toFixed(1)}MB`,
                        "Memory",
                      ]}
                    />
                    <Area
                      type="monotone"
                      dataKey="value"
                      stroke="#10b981"
                      fill="url(#modalMemGradient)"
                      strokeWidth={2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function AgentCard({
  agent,
  viewMode = "list",
  onDetail,
  onPause,
  onResume,
  onRemove,
}: {
  agent: Agent;
  viewMode?: "list" | "grid";
  onDetail: () => void;
  onPause: () => void;
  onResume: () => void;
  onRemove: () => void;
}) {
  const [displayTime, setDisplayTime] = useState(
    formatExecutionTime(agent.executionTime),
  );

  useEffect(() => {
    setDisplayTime(formatExecutionTime(agent.executionTime));
  }, [agent.executionTime]);

  useEffect(() => {
    if (agent.status !== "running") return;

    const parseTime = (timeStr: string): number => {
      const parts = timeStr.split(":").map((p) => parseInt(p, 10) || 0);
      if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
      if (parts.length === 2) return parts[0] * 60 + parts[1];
      return 0;
    };

    const formatSeconds = (totalSeconds: number): string => {
      const mins = Math.floor(totalSeconds / 60);
      const secs = Math.floor(totalSeconds % 60);
      return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
    };

    let baseSeconds = parseTime(formatExecutionTime(agent.executionTime));
    const interval = setInterval(() => {
      baseSeconds += 1;
      setDisplayTime(formatSeconds(baseSeconds));
    }, 1000);

    return () => clearInterval(interval);
  }, [agent.status, agent.executionTime]);

  const getCardColors = () => {
    if (agent.memoryUsage > 1024) {
      return "border-red-500/50 bg-red-500/5";
    }
    const statusColors: Record<string, string> = {
      idle: "border-muted-foreground/20",
      running: "border-emerald-500/50 bg-emerald-500/5",
      paused: "border-yellow-500/50 bg-yellow-500/5",
      error: "border-red-500/50 bg-red-500/5",
      break: "border-blue-500/50 bg-blue-500/5",
    };
    return statusColors[agent.status] || "border-border";
  };

  const statusColors: Record<string, string> = {
    idle: "border-muted-foreground/20",
    running: "border-emerald-500/50 bg-emerald-500/5",
    paused: "border-yellow-500/50 bg-yellow-500/5",
    error: "border-red-500/50 bg-red-500/5",
    break: "border-blue-500/50 bg-blue-500/5",
  };

  const statusDot: Record<string, string> = {
    idle: "bg-muted-foreground",
    running: "bg-emerald-500",
    paused: "bg-yellow-500",
    error: "bg-red-500",
    break: "bg-blue-500",
  };

  if (viewMode === "grid") {
    return (
      <div
        className={`p-3 rounded-lg border ${getCardColors()} transition-all hover:shadow-md cursor-pointer group`}
        onClick={onDetail}
      >
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className="relative">
              <div
                className={`w-7 h-7 rounded-md flex items-center justify-center ${agent.status === "running" ? "bg-primary/10" : "bg-muted"}`}
              >
                <Bot
                  className={`w-3.5 h-3.5 ${agent.status === "running" ? "text-primary" : "text-muted-foreground"}`}
                />
              </div>
              <div
                className={`absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full border border-background ${statusDot[agent.status]}`}
              />
            </div>
            <span className="font-semibold text-xs">
              Agent-{agent.displayId || agent.id.slice(0, 4)}
            </span>
          </div>
          <Badge variant="outline" className="text-[9px] h-4 capitalize">
            {agent.status}
          </Badge>
        </div>
        <div className="p-1.5 rounded bg-black/80 font-mono text-[9px] text-green-400 truncate mb-2 border border-green-900/30">
          {agent.lastCommand?.slice(0, 30) || "Waiting..."}
        </div>
        <div className="flex items-center justify-center gap-1 text-primary">
          <Timer className="w-3 h-3" />
          <span className="text-sm font-mono font-bold">{displayTime}</span>
          {agent.status === "running" && (
            <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
          )}
        </div>
      </div>
    );
  }

  return (
    <div
      className={`p-3 rounded-lg border ${getCardColors()} transition-all hover:shadow-md cursor-pointer group`}
      onClick={onDetail}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="relative">
            <div
              className={`w-8 h-8 rounded-lg flex items-center justify-center ${agent.status === "running" ? "bg-primary/10" : "bg-muted"}`}
            >
              <Bot
                className={`w-4 h-4 ${agent.status === "running" ? "text-primary" : "text-muted-foreground"}`}
              />
            </div>
            <div
              className={`absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-background ${statusDot[agent.status]}`}
            />
          </div>
          <div>
            <span className="font-semibold text-sm">
              Agent-{agent.displayId || agent.id.slice(0, 4)}
            </span>
            <p className="text-[10px] text-muted-foreground capitalize">
              {agent.status}
            </p>
          </div>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <MoreVertical className="w-3.5 h-3.5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem
              onClick={(e) => {
                e.stopPropagation();
                onDetail();
              }}
            >
              <Eye className="w-3 h-3 mr-2" />
              View Details
            </DropdownMenuItem>
            {agent.status === "running" ? (
              <DropdownMenuItem
                onClick={(e) => {
                  e.stopPropagation();
                  onPause();
                }}
              >
                <Pause className="w-3 h-3 mr-2" />
                Pause
              </DropdownMenuItem>
            ) : agent.status === "paused" ? (
              <DropdownMenuItem
                onClick={(e) => {
                  e.stopPropagation();
                  onResume();
                }}
              >
                <Play className="w-3 h-3 mr-2" />
                Resume
              </DropdownMenuItem>
            ) : null}
            <DropdownMenuItem
              onClick={(e) => {
                e.stopPropagation();
                onRemove();
              }}
              className="text-destructive"
            >
              <Trash2 className="w-3 h-3 mr-2" />
              Terminate
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <div className="p-2 rounded-md bg-black/80 font-mono text-[10px] text-green-400 truncate mb-3 border border-green-900/30">
        <Terminal className="w-3 h-3 inline mr-1.5 opacity-60" />
        {agent.lastCommand || "Waiting for command..."}
      </div>

      <div className="flex items-center justify-between p-2.5 rounded-lg bg-primary/5 border border-primary/20">
        <div className="flex items-center gap-2">
          <Timer className="w-4 h-4 text-primary" />
          <span className="text-xs text-muted-foreground">Execution Time</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-lg font-mono font-bold text-primary">
            {displayTime}
          </span>
          {agent.status === "running" && (
            <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
          )}
        </div>
      </div>

      <div className="mt-2 text-center">
        <span className="text-[10px] text-muted-foreground">
          Click for CPU/Memory details
        </span>
      </div>
    </div>
  );
}

function FindingCard({ finding }: { finding: Finding }) {
  const [showDetails, setShowDetails] = useState(false);

  const colors = {
    critical: "border-l-red-500 bg-red-500/5",
    high: "border-l-orange-500 bg-orange-500/5",
    medium: "border-l-yellow-500 bg-yellow-500/5",
    low: "border-l-blue-500 bg-blue-500/5",
    info: "border-l-gray-500 bg-gray-500/5",
  };

  const badgeColors = {
    critical: "bg-red-500/20 text-red-400 border-red-500/30",
    high: "bg-orange-500/20 text-orange-400 border-orange-500/30",
    medium: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    low: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    info: "bg-gray-500/20 text-gray-400 border-gray-500/30",
  };

  return (
    <>
      <div
        className={`p-3 rounded-lg border-l-2 ${colors[finding.severity]} hover:bg-muted/50 transition-colors cursor-pointer border border-transparent hover:border-border/50`}
        onClick={() => setShowDetails(true)}
      >
        <div className="flex items-center justify-between gap-2 mb-2">
          <div className="flex items-center gap-1.5">
            <Badge
              variant="outline"
              className={`text-[10px] capitalize ${badgeColors[finding.severity]}`}
            >
              {finding.severity}
            </Badge>
            {finding.cvss && (
              <span className="text-[10px] font-mono text-muted-foreground">
                CVSS: {finding.cvss.toFixed(1)}
              </span>
            )}
          </div>
          {finding.cve && (
            <Badge
              variant="secondary"
              className="text-[9px] font-mono h-4 px-1.5"
            >
              {finding.cve}
            </Badge>
          )}
        </div>
        <p className="text-xs font-medium leading-tight mb-1">
          {finding.title}
        </p>
        <p className="text-[10px] text-muted-foreground line-clamp-2 leading-relaxed">
          {finding.description}
        </p>
        <div className="flex items-center justify-between mt-2 pt-2 border-t border-border/30">
          <span className="text-[9px] text-muted-foreground">
            Agent {finding.agentId}
          </span>
          <span className="text-[9px] text-muted-foreground">
            {finding.timestamp}
          </span>
        </div>
      </div>

      <Dialog open={showDetails} onOpenChange={setShowDetails}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle
                className={`w-5 h-5 ${
                  finding.severity === "critical"
                    ? "text-red-500"
                    : finding.severity === "high"
                      ? "text-orange-500"
                      : finding.severity === "medium"
                        ? "text-yellow-500"
                        : finding.severity === "low"
                          ? "text-blue-500"
                          : "text-gray-500"
                }`}
              />
              Security Finding Report
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <div className="flex items-center gap-2 flex-wrap">
              <Badge className={badgeColors[finding.severity]}>
                {finding.severity.toUpperCase()}
              </Badge>
              {finding.cvss && (
                <Badge variant="outline" className="font-mono">
                  CVSS: {finding.cvss.toFixed(1)}
                </Badge>
              )}
              {finding.cve && (
                <Badge variant="secondary" className="font-mono">
                  {finding.cve}
                </Badge>
              )}
            </div>

            <div>
              <h4 className="font-semibold text-lg mb-1">{finding.title}</h4>
              <p className="text-sm text-muted-foreground">
                {finding.description}
              </p>
            </div>

            {finding.details && (
              <div className="p-3 rounded-lg bg-muted/50 border">
                <h5 className="text-xs font-semibold mb-2 text-muted-foreground uppercase">
                  Technical Details
                </h5>
                <p className="text-sm font-mono whitespace-pre-wrap">
                  {finding.details}
                </p>
              </div>
            )}

            {finding.remediation && (
              <div className="p-3 rounded-lg bg-primary/5 border border-primary/20">
                <h5 className="text-xs font-semibold mb-2 text-primary uppercase">
                  Remediation
                </h5>
                <p className="text-sm">{finding.remediation}</p>
              </div>
            )}

            <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t">
              <span>Discovered by Agent {finding.agentId}</span>
              <span>{finding.timestamp}</span>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

function StealthToggle({
  label,
  desc,
  checked,
  onChange,
}: {
  label: string;
  desc: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between p-2 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors">
      <div>
        <p className="text-xs font-medium">{label}</p>
        <p className="text-[10px] text-muted-foreground">{desc}</p>
      </div>
      <Switch checked={checked} onCheckedChange={onChange} />
    </div>
  );
}

function CapToggle({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between p-2 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors">
      <p className="text-xs font-medium">{label}</p>
      <Switch checked={checked} onCheckedChange={onChange} />
    </div>
  );
}

function ChatSidebar({
  open,
  onToggle,
}: {
  open: boolean;
  onToggle: () => void;
}) {
  const [input, setInput] = useState("");
  const [sidebarTab, setSidebarTab] = useState<"chat" | "queue" | "history">(
    "chat",
  );
  const [queueState, setQueueState] = useState<{
    pending: any[];
    executing: any[];
    total_pending: number;
    total_executing: number;
  }>({ pending: [], executing: [], total_pending: 0, total_executing: 0 });
  const [sidebarWidth, setSidebarWidth] = useState(320);
  const [isResizing, setIsResizing] = useState(false);
  const sidebarRef = useRef<HTMLDivElement>(null);
  const {
    messages,
    sendMessage,
    sendQueueCommand,
    mode,
    setMode,
    connected,
    connecting,
    connectionError,
    reconnect,
  } = useChat();
  const { lastMessage } = useWebSocket();

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      const newWidth = e.clientX;
      if (newWidth >= 280 && newWidth <= 500) {
        setSidebarWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
    }

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isResizing]);

  useEffect(() => {
    if (lastMessage?.type === "queue_update" && lastMessage.queue) {
      const q = lastMessage.queue as any;
      if (q.pending !== undefined) {
        setQueueState(q);
      }
    }
  }, [lastMessage]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    if (input.startsWith("/queue")) {
      sendQueueCommand(input);
    } else if (input.startsWith("/chat")) {
      setMode("chat");
    } else {
      sendMessage(input, mode);
    }
    setInput("");
  };

  const handleTabChange = (tab: "chat" | "queue" | "history") => {
    setSidebarTab(tab);
    if (tab === "chat") setMode("chat");
    if (tab === "queue") setMode("queue");
  };

  return (
    <div
      ref={sidebarRef}
      className={`h-full border-r border-border flex flex-col relative ${open ? "" : "w-12"}`}
      style={
        open
          ? { width: `${sidebarWidth}px`, minWidth: "280px", maxWidth: "500px" }
          : {}
      }
    >
      <div className="p-2 border-b border-border flex items-center justify-between shrink-0">
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggle}
          className="h-8 w-8"
        >
          {open ? (
            <X className="w-4 h-4" />
          ) : (
            <MessageSquare className="w-4 h-4" />
          )}
        </Button>
        {open && (
          <div className="flex items-center gap-2">
            <span className="font-semibold text-sm truncate">
              {sidebarTab === "history"
                ? "History"
                : sidebarTab === "queue"
                  ? "Queue"
                  : "Chat"}
            </span>
            {connecting ? (
              <Badge
                variant="secondary"
                className="text-xs shrink-0 animate-pulse"
              >
                Connecting...
              </Badge>
            ) : connected ? (
              <Badge variant="default" className="text-xs shrink-0">
                Online
              </Badge>
            ) : (
              <Badge
                variant="destructive"
                className="text-xs shrink-0 cursor-pointer hover:bg-destructive/80"
                onClick={reconnect}
                title="Click to reconnect"
              >
                Offline
              </Badge>
            )}
          </div>
        )}
      </div>
      {open && (
        <div
          className={`absolute top-0 right-0 w-1.5 h-full cursor-col-resize hover:bg-primary/20 transition-colors z-10 ${isResizing ? "bg-primary/30" : ""}`}
          onMouseDown={handleMouseDown}
        >
          <div className="absolute top-1/2 -translate-y-1/2 right-0 w-1.5 h-8 flex items-center justify-center">
            <GripVertical className="w-3 h-3 text-muted-foreground" />
          </div>
        </div>
      )}

      {open ? (
        <>
          <div className="px-1.5 py-1 border-b border-border flex gap-0.5 shrink-0">
            <Button
              variant={sidebarTab === "chat" ? "default" : "ghost"}
              size="sm"
              onClick={() => handleTabChange("chat")}
              className="h-7 text-xs flex-1 gap-1 px-2"
            >
              <MessageSquare className="w-3 h-3" />
              Chat
            </Button>
            <Button
              variant={sidebarTab === "queue" ? "default" : "ghost"}
              size="sm"
              onClick={() => handleTabChange("queue")}
              className="h-7 text-xs flex-1 gap-1 px-2"
            >
              <ListOrdered className="w-3 h-3" />
              Queue
              {queueState.total_pending > 0 && (
                <Badge
                  variant="secondary"
                  className="text-[10px] h-4 px-1 ml-0.5"
                >
                  {queueState.total_pending}
                </Badge>
              )}
            </Button>
            <Button
              variant={sidebarTab === "history" ? "default" : "ghost"}
              size="sm"
              onClick={() => handleTabChange("history")}
              className="h-7 text-xs flex-1 gap-1 px-2"
            >
              <Brain className="w-3 h-3" />
              History
            </Button>
          </div>

          {sidebarTab === "history" ? (
            <div className="flex-1 min-h-0">
              <ModelInstructions />
            </div>
          ) : sidebarTab === "queue" ? (
            <div className="flex-1 flex flex-col overflow-hidden">
              <div className="p-2 border-b border-border shrink-0">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium">Shared Queue</span>
                  <div className="flex gap-1">
                    <Badge variant="outline" className="text-[10px]">
                      Pending: {queueState.total_pending}
                    </Badge>
                    <Badge variant="secondary" className="text-[10px]">
                      Running: {queueState.total_executing}
                    </Badge>
                  </div>
                </div>
                <div className="flex gap-1">
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-6 text-[10px] flex-1"
                    onClick={() => sendQueueCommand("/queue list")}
                  >
                    Refresh
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-6 text-[10px] flex-1"
                    onClick={() => sendQueueCommand("/queue clear")}
                  >
                    Clear
                  </Button>
                </div>
              </div>

              <ScrollArea className="flex-1 p-2">
                <div className="space-y-2">
                  {queueState.executing.length > 0 && (
                    <div>
                      <p className="text-[10px] font-medium text-yellow-500 mb-1">
                        Executing
                      </p>
                      {queueState.executing.map((inst: any) => (
                        <div
                          key={inst.id}
                          className="p-2 rounded-md bg-yellow-500/10 border border-yellow-500/30 mb-1"
                        >
                          <div className="flex items-center justify-between mb-1">
                            <Badge variant="outline" className="text-[9px] h-4">
                              #{inst.id}
                            </Badge>
                            <span className="text-[9px] text-muted-foreground">
                              {inst.claimed_by?.slice(0, 8) || "agent"}
                            </span>
                          </div>
                          <p className="text-[10px] font-mono text-yellow-500 truncate">
                            {inst.command}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}

                  {queueState.pending.length > 0 && (
                    <div>
                      <p className="text-[10px] font-medium text-muted-foreground mb-1">
                        Pending ({queueState.pending.length})
                      </p>
                      {queueState.pending.map((inst: any, idx: number) => (
                        <div
                          key={inst.id}
                          className="p-2 rounded-md bg-muted/30 border border-border mb-1 group"
                        >
                          <div className="flex items-center justify-between mb-1">
                            <Badge variant="outline" className="text-[9px] h-4">
                              #{inst.id}
                            </Badge>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-4 w-4 opacity-0 group-hover:opacity-100"
                              onClick={() =>
                                sendQueueCommand(`/queue rm ${inst.id}`)
                              }
                            >
                              <Trash2 className="w-2.5 h-2.5 text-destructive" />
                            </Button>
                          </div>
                          <p className="text-[10px] font-mono text-muted-foreground truncate">
                            {inst.command}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}

                  {queueState.pending.length === 0 &&
                    queueState.executing.length === 0 && (
                      <div className="text-center py-6 text-muted-foreground">
                        <ListOrdered className="w-8 h-8 mx-auto mb-2 opacity-20" />
                        <p className="text-xs">Queue is empty</p>
                        <p className="text-[10px]">
                          Commands will appear here when the AI predicts them
                        </p>
                      </div>
                    )}
                </div>
              </ScrollArea>

              <div className="p-2 border-t border-border shrink-0">
                <p className="text-[10px] text-muted-foreground mb-1">
                  Add Command
                </p>
                <div className="flex gap-1">
                  <Input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder='{"1": "RUN nmap..."}'
                    className="h-7 text-xs flex-1"
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        sendQueueCommand(`/queue add ${input}`);
                        setInput("");
                      }
                    }}
                  />
                  <Button
                    size="sm"
                    className="h-7 px-2"
                    onClick={() => {
                      sendQueueCommand(`/queue add ${input}`);
                      setInput("");
                    }}
                  >
                    <Send className="w-3 h-3" />
                  </Button>
                </div>
              </div>
            </div>
          ) : (
            <ScrollArea className="flex-1 p-3">
              {messages.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Bot className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">Start a conversation</p>
                  <div className="mt-4 text-left text-xs space-y-1">
                    <p className="text-muted-foreground">
                      Chat with the AI assistant to get help with security
                      analysis
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  {messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`flex gap-2 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
                    >
                      <div
                        className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${msg.role === "user" ? "bg-primary/20" : "bg-muted"}`}
                      >
                        {msg.role === "user" ? (
                          <User className="w-3 h-3 text-primary" />
                        ) : (
                          <Bot className="w-3 h-3" />
                        )}
                      </div>
                      <div
                        className={`max-w-[80%] rounded-lg px-3 py-2 ${msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"}`}
                      >
                        <p className="text-xs whitespace-pre-wrap">
                          {msg.content}
                        </p>
                        <p className="text-[10px] opacity-70 mt-1">
                          {msg.timestamp}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          )}

          {sidebarTab === "chat" && (
            <form
              onSubmit={handleSubmit}
              className="p-3 border-t border-border shrink-0"
            >
              <div className="flex gap-2">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Type a message..."
                  className="flex-1 h-9"
                />
                <Button
                  type="submit"
                  size="icon"
                  disabled={!connected}
                  className="h-9 w-9"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </form>
          )}
        </>
      ) : (
        <div className="flex-1 flex flex-col items-center py-4 gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggle}
            className="h-8 w-8"
            title="Open Chat"
          >
            <Terminal className="w-4 h-4" />
          </Button>
          {connected && (
            <div
              className="w-2 h-2 rounded-full bg-emerald-500"
              title="Connected"
            />
          )}
        </div>
      )}
    </div>
  );
}
