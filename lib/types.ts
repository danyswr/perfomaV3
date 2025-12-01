export interface MissionConfig {
  target: string
  category: "domain" | "path" | "ip"
  customInstruction: string
  stealthMode: boolean
  aggressiveLevel: number
  modelName: string
  numAgents: number
  stealthOptions: StealthOptions
  capabilities: CapabilityOptions
  osType: "windows" | "linux"
  batchSize: number
  rateLimitRps: number
  rateLimitEnabled: boolean
  executionDuration: number | null
  customDurationMinutes?: number
  requestedTools: string[]
  allowedToolsOnly: boolean
  instructionDelayMs: number
  modelDelayMs: number
}

export type ExecutionDuration = 5 | 10 | 15 | 20 | 30 | 60 | 120 | "custom" | null

export const EXECUTION_DURATION_OPTIONS = [
  { value: 5, label: "5 minutes" },
  { value: 10, label: "10 minutes" },
  { value: 15, label: "15 minutes" },
  { value: 20, label: "20 minutes" },
  { value: 30, label: "30 minutes" },
  { value: 60, label: "60 minutes" },
  { value: 120, label: "120 minutes" },
  { value: "custom", label: "Custom" },
  { value: null, label: "Until stopped" },
] as const

export interface RateLimitConfig {
  enabled: boolean
  requestsPerSecond: number
}

export const DEFAULT_RATE_LIMIT_CONFIG: RateLimitConfig = {
  enabled: false,
  requestsPerSecond: 1
}

export interface StealthOptions {
  proxyChain: boolean
  torRouting: boolean
  vpnChaining: boolean
  macSpoofing: boolean
  timestampSpoofing: boolean
  logWiping: boolean
  memoryScrambling: boolean
  secureDelete: boolean
}

export interface CapabilityOptions {
  packetInjection: boolean
  arpSpoof: boolean
  mitm: boolean
  trafficHijack: boolean
  realtimeManipulation: boolean
  corsExploitation: boolean
  ssrfChaining: boolean
  deserializationExploit: boolean
  wafBypass: boolean
  bacTesting: boolean
  websocketHijack: boolean
}

export interface QuickMissionSummary {
  total_findings: number
  severity_breakdown: Record<string, number>
  duration: number
  agents_used: number
}

export interface Mission {
  active: boolean
  target: string
  category: string
  instruction: string
  duration: number
  progress: number
  activeAgents: number
  totalAgents: number
  completedTasks: number
  findings: number
  startTime?: number
  maxDuration?: number | null
  summary?: QuickMissionSummary | null
  reportsGenerated?: string[]
}

export interface Agent {
  id: string
  displayId: string
  status: "idle" | "running" | "paused" | "error" | "break"
  lastCommand: string
  executionTime: string
  lastExecuteTime?: string
  cpuUsage: number
  memoryUsage: number
  progress: number
  target?: string
  category?: string
  currentTask?: string
  tasksCompleted?: number
  findingsCount?: number
  cpuHistory?: ResourceDataPoint[]
  memoryHistory?: ResourceDataPoint[]
  breakReason?: string
}

export interface ResourceDataPoint {
  time: string
  value: number
}

export interface ChatMessage {
  id: string
  role: "user" | "assistant" | "system"
  content: string
  timestamp: string
}

export interface ModelInstruction {
  id: string
  agentId: string
  modelName: string
  instruction: string
  timestamp: string
  type: "command" | "found" | "execute" | "model_output" | "info" | "analysis" | "decision"
  severity?: "critical" | "high" | "medium" | "low" | "info"
}

export interface Finding {
  id: string
  title: string
  description: string
  severity: "critical" | "high" | "medium" | "low" | "info"
  cve?: string
  cvss?: number
  agentId: string
  timestamp: string
  details?: string
  remediation?: string
  ipAddress?: string
  port?: number
  protocol?: string
  service?: string
  toolUsed?: string
  commandExecuted?: string
  rawOutput?: string
}

export interface MissionSummary {
  id: string
  missionId: string
  totalFindings: number
  criticalCount: number
  highCount: number
  mediumCount: number
  lowCount: number
  infoCount: number
  openPorts: PortInfo[]
  servicesFound: string[]
  vulnerabilities: VulnerabilityInfo[]
  targetsScanned: string[]
  agentsUsed: number
  totalCommands: number
  durationSeconds: number
  summaryText?: string
  recommendations: string[]
  createdAt: string
}

export interface PortInfo {
  port: number
  protocol: string
  service: string
  state: string
}

export interface VulnerabilityInfo {
  title: string
  severity: string
  cve?: string
  description: string
}

export interface SavedProgress {
  id: string
  name: string
  description?: string
  missionConfig: MissionConfig
  canResume: boolean
  createdAt: string
}

export interface Resources {
  cpu: number
  memory: number
  disk: number
  network: number
  wifiSpeed?: number
}

export interface ResourceHistory {
  time: string
  cpu: number
  memory: number
}

export const OPENROUTER_MODELS = [
  { id: "anthropic/claude-sonnet-4", name: "Claude Sonnet 4", provider: "Anthropic" },
  { id: "anthropic/claude-3.5-sonnet", name: "Claude 3.5 Sonnet", provider: "Anthropic" },
  { id: "anthropic/claude-3-opus", name: "Claude 3 Opus", provider: "Anthropic" },
  { id: "openai/gpt-4-turbo", name: "GPT-4 Turbo", provider: "OpenAI" },
  { id: "openai/gpt-4o", name: "GPT-4o", provider: "OpenAI" },
  { id: "google/gemini-pro-1.5", name: "Gemini Pro 1.5", provider: "Google" },
  { id: "meta-llama/llama-3.1-405b-instruct", name: "Llama 3.1 405B", provider: "Meta" },
  { id: "ollama", name: "Ollama (Local)", provider: "Ollama" },
  { id: "custom", name: "Custom Model", provider: "OpenRouter" },
]

export const DEFAULT_STEALTH_OPTIONS: StealthOptions = {
  proxyChain: false,
  torRouting: false,
  vpnChaining: false,
  macSpoofing: false,
  timestampSpoofing: false,
  logWiping: false,
  memoryScrambling: false,
  secureDelete: false,
}

export const DEFAULT_CAPABILITY_OPTIONS: CapabilityOptions = {
  packetInjection: false,
  arpSpoof: false,
  mitm: false,
  trafficHijack: false,
  realtimeManipulation: false,
  corsExploitation: false,
  ssrfChaining: false,
  deserializationExploit: false,
  wafBypass: false,
  bacTesting: false,
  websocketHijack: false,
}
