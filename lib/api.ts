// Use relative API paths for Docker compatibility - rewrites handle routing to backend
const API_BASE = typeof window !== 'undefined' 
  ? (window.location.origin)
  : ""

export interface ApiResponse<T> {
  data?: T
  error?: string
  status?: number
}

async function handleResponse<T>(res: Response): Promise<ApiResponse<T>> {
  try {
    const data = await res.json()
    if (!res.ok) {
      return { error: data.detail || data.message || "Request failed", status: res.status }
    }
    return { data, status: res.status }
  } catch {
    if (!res.ok) {
      return { error: `HTTP ${res.status}: ${res.statusText}`, status: res.status }
    }
    return { error: "Failed to parse response" }
  }
}

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/agents`, {
      method: "GET",
      signal: AbortSignal.timeout(5000),
    })
    return res.ok
  } catch {
    return false
  }
}

export const api = {
  // Health Check
  async healthCheck() {
    try {
      const res = await fetch(`${API_BASE}/`)
      return handleResponse<{ message: string; version: string; status: string }>(res)
    } catch {
      return { error: "Cannot connect to backend server" }
    }
  },

  // Mission
  async startMission(config: {
    target: string
    category: string
    custom_instruction: string
    stealth_mode: boolean
    aggressive_mode: boolean
    model_name: string
    num_agents: number
    os_type?: string
    stealth_options?: Record<string, boolean>
    capabilities?: Record<string, boolean>
    batch_size?: number
    rate_limit_rps?: number
    execution_duration?: number | null
    requested_tools?: string[]
    allowed_tools_only?: boolean
    instruction_delay_ms?: number
    model_delay_ms?: number
  }) {
    try {
      const res = await fetch(`${API_BASE}/api/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      })
      return handleResponse<{ 
        status: string
        agent_ids: string[]
        timestamp: string
        config?: {
          batch_size: number
          rate_limit_rps: number
          execution_duration: number | null
          requested_tools: string[]
        }
      }>(res)
    } catch {
      return { error: "Cannot connect to backend server. Make sure it's running." }
    }
  },

  // Agents
  async getAgents() {
    try {
      const res = await fetch(`${API_BASE}/api/agents`)
      return handleResponse<{ agents: AgentResponse[]; total: number }>(res)
    } catch {
      return { error: "Cannot fetch agents", data: { agents: [], total: 0 } }
    }
  },

  async getAgent(agentId: string) {
    try {
      const res = await fetch(`${API_BASE}/api/agents/${agentId}`)
      return handleResponse<AgentResponse>(res)
    } catch {
      return { error: "Cannot fetch agent details" }
    }
  },

  async createAgent(config?: {
    target?: string
    category?: string
    custom_instruction?: string
    stealth_mode?: boolean
    aggressive_mode?: boolean
    model_name?: string
  }) {
    try {
      const res = await fetch(`${API_BASE}/api/agents`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config || {}),
      })
      return handleResponse<{ status: string; agent_id: string; agent: AgentResponse }>(res)
    } catch {
      return { error: "Cannot create agent" }
    }
  },

  async deleteAgent(agentId: string) {
    try {
      const res = await fetch(`${API_BASE}/api/agents/${agentId}`, {
        method: "DELETE",
      })
      return handleResponse<{ status: string; agent_id: string }>(res)
    } catch {
      return { error: "Cannot delete agent" }
    }
  },

  async pauseAgent(agentId: string) {
    try {
      const res = await fetch(`${API_BASE}/api/agents/${agentId}/pause`, {
        method: "POST",
      })
      return handleResponse<{ status: string; agent_id: string }>(res)
    } catch {
      return { error: "Cannot pause agent" }
    }
  },

  async resumeAgent(agentId: string) {
    try {
      const res = await fetch(`${API_BASE}/api/agents/${agentId}/resume`, {
        method: "POST",
      })
      return handleResponse<{ status: string; agent_id: string }>(res)
    } catch {
      return { error: "Cannot resume agent" }
    }
  },

  // Resources
  async getResources() {
    try {
      const res = await fetch(`${API_BASE}/api/resources`)
      return handleResponse<ResourcesResponse>(res)
    } catch {
      return {
        error: "Cannot fetch resources",
        data: { cpu: 0, memory: 0, disk: 0, network: 0, timestamp: new Date().toISOString() },
      }
    }
  },

  async getAgentResources() {
    try {
      const res = await fetch(`${API_BASE}/api/resources/agents`)
      return handleResponse<AgentResourcesResponse>(res)
    } catch {
      return { error: "Cannot fetch agent resources", data: {} }
    }
  },

  // Findings
  async getFindings() {
    try {
      const res = await fetch(`${API_BASE}/api/findings`)
      return handleResponse<FindingsResponse>(res)
    } catch {
      return {
        error: "Cannot fetch findings",
        data: { findings: [], total: 0, severity_summary: { critical: 0, high: 0, medium: 0, low: 0, info: 0 } },
      }
    }
  },

  // Models
  async getModels() {
    try {
      const res = await fetch(`${API_BASE}/api/models`)
      return handleResponse<{ models: ModelInfo[] }>(res)
    } catch {
      return { error: "Cannot fetch models", data: { models: [] } }
    }
  },

  async testModel(payload: { provider: string; model: string; api_key?: string }) {
    try {
      const res = await fetch(`${API_BASE}/api/models/test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
      return handleResponse<{ status: string; message: string; provider: string; model: string; latency?: string; response?: string }>(res)
    } catch {
      return { error: "Cannot connect to backend. Make sure the server is running." }
    }
  },

  // Instruction History
  async getAgentHistory(agentId: string) {
    try {
      const res = await fetch(`${API_BASE}/api/agents/${agentId}/history`)
      return handleResponse<{ agent_id: string; history: InstructionHistory[]; total: number }>(res)
    } catch {
      return { error: "Cannot fetch agent history", data: { agent_id: agentId, history: [], total: 0 } }
    }
  },

  async getAllHistory() {
    try {
      const res = await fetch(`${API_BASE}/api/history`)
      return handleResponse<{ history: InstructionHistory[]; total: number }>(res)
    } catch {
      return { error: "Cannot fetch history", data: { history: [], total: 0 } }
    }
  },

  async stopMission() {
    try {
      const res = await fetch(`${API_BASE}/api/stop`, {
        method: "POST",
      })
      return handleResponse<{ 
        status: string
        agents_stopped: number
        total_agents: number
        reports_generated_for: string[]
        summary?: {
          total_findings: number
          severity_breakdown: Record<string, number>
          duration: number
          agents_used: number
        }
      }>(res)
    } catch {
      return { error: "Cannot stop mission" }
    }
  },

  async getFindingsExplorer() {
    try {
      const res = await fetch(`${API_BASE}/api/findings/explorer`)
      return handleResponse<FindingsExplorerResponse>(res)
    } catch {
      return { error: "Cannot fetch findings explorer", data: { folders: [], root_files: [], total_files: 0, last_updated: new Date().toISOString() } }
    }
  },

  async getFileContent(filePath: string) {
    try {
      const res = await fetch(`${API_BASE}/api/findings/file/${encodeURIComponent(filePath)}`)
      return handleResponse<FileContentResponse>(res)
    } catch {
      return { error: "Cannot fetch file content" }
    }
  },

  async getAgentLogs() {
    try {
      const res = await fetch(`${API_BASE}/api/findings/logs`)
      return handleResponse<{ logs: FileInfo[]; total: number }>(res)
    } catch {
      return { error: "Cannot fetch logs", data: { logs: [], total: 0 } }
    }
  },

  async getLogContent(fileName: string, tail: number = 500) {
    try {
      const res = await fetch(`${API_BASE}/api/findings/logs/${encodeURIComponent(fileName)}?tail=${tail}`)
      return handleResponse<{ filename: string; content: string; total_lines: number }>(res)
    } catch {
      return { error: "Cannot fetch log content" }
    }
  },

  async saveSession() {
    try {
      const res = await fetch(`${API_BASE}/api/session/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      })
      return handleResponse<{ status: string; session_id: string; message: string }>(res)
    } catch {
      return { error: "Cannot save session" }
    }
  },

  async saveMissionConfig(config: {
    name?: string
    target?: string
    category?: string
    custom_instruction?: string
    stealth_mode?: boolean
    aggressive_mode?: boolean
    model_name?: string
    num_agents?: number
    execution_duration?: number | null
    requested_tools?: string[]
    allowed_tools_only?: boolean
  }) {
    try {
      const res = await fetch(`${API_BASE}/api/config/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      })
      return handleResponse<{ status: string; config_id: string; name: string; message: string }>(res)
    } catch {
      return { error: "Cannot save configuration" }
    }
  },

  async getSavedConfig() {
    try {
      const res = await fetch(`${API_BASE}/api/config/saved`)
      return handleResponse<{ config: any; status?: string; message?: string }>(res)
    } catch {
      return { error: "Cannot fetch saved configuration" }
    }
  },

  async listSavedConfigs() {
    try {
      const res = await fetch(`${API_BASE}/api/config/list`)
      return handleResponse<{ configs: any[]; count: number }>(res)
    } catch {
      return { error: "Cannot fetch saved configurations" }
    }
  },

  async getConfigById(configId: string) {
    try {
      const res = await fetch(`${API_BASE}/api/config/${configId}`)
      return handleResponse<{ config: any; status: string }>(res)
    } catch {
      return { error: "Cannot fetch configuration" }
    }
  },

  async deleteConfig(configId: string) {
    try {
      const res = await fetch(`${API_BASE}/api/config/${configId}`, {
        method: "DELETE",
      })
      return handleResponse<{ status: string; config_id: string }>(res)
    } catch {
      return { error: "Cannot delete configuration" }
    }
  },

  async generateMissionSummary(data: {
    agent_logs: any[]
    findings: any[]
    target: string
    execution_time: string
    reason: string
  }) {
    try {
      const res = await fetch(`${API_BASE}/api/mission/summary`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      })
      return handleResponse<{ status: string; summary: string }>(res)
    } catch {
      return { error: "Cannot generate summary" }
    }
  },

  async saveFindingsSummary(data: {
    summary: string
    target: string
    execution_time: string
  }) {
    try {
      const res = await fetch(`${API_BASE}/api/findings/summary`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      })
      return handleResponse<{ status: string; filename: string }>(res)
    } catch {
      return { error: "Cannot save summary" }
    }
  },

  async getSessions() {
    try {
      const res = await fetch(`${API_BASE}/api/sessions`)
      return handleResponse<{ sessions: SessionInfo[]; total: number }>(res)
    } catch {
      return { error: "Cannot fetch sessions", data: { sessions: [], total: 0 } }
    }
  },

  async resumeSession(sessionId: string) {
    try {
      const res = await fetch(`${API_BASE}/api/session/${sessionId}/resume`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      })
      return handleResponse<{ status: string; agent_ids: string[] }>(res)
    } catch {
      return { error: "Cannot resume session" }
    }
  },

  async getAgentRealtimeLogs(agentId: string) {
    try {
      const res = await fetch(`${API_BASE}/api/agents/${agentId}/logs/realtime`)
      return handleResponse<{ logs: AgentLogEntry[]; agent_id: string }>(res)
    } catch {
      return { error: "Cannot fetch agent logs" }
    }
  },
}

export interface SessionInfo {
  id: string
  target: string
  status: string
  created_at: string
  updated_at: string
}

export interface AgentLogEntry {
  timestamp: string
  type: string
  message: string
  metadata?: Record<string, any>
}

export interface AgentResponse {
  id: string
  status: "idle" | "running" | "paused" | "error"
  last_command: string
  execution_time: number
  last_execute_time?: string
  cpu_usage: number
  memory_usage: number
  progress: number
  target?: string
  category?: string
}

export interface ResourcesResponse {
  cpu: number
  memory: number
  disk: number
  network: number
  timestamp: string
}

export interface AgentResourcesResponse {
  [agentId: string]: {
    cpu: number
    memory: number
    network: number
  }
}

export interface FindingsResponse {
  findings: FindingResponse[]
  total: number
  severity_summary: {
    critical: number
    high: number
    medium: number
    low: number
    info: number
  }
}

export interface FindingResponse {
  id: string
  title: string
  description: string
  severity: "critical" | "high" | "medium" | "low" | "info"
  cve?: string
  cvss?: number
  agent_id: string
  timestamp: string
}

export interface ModelInfo {
  id: string
  name: string
  provider: string
}

export interface InstructionHistory {
  id: number
  instruction: string
  full_response?: string
  instruction_type: "analysis" | "command" | "decision"
  timestamp: string
  model_name: string
  agent_id?: string
}

export interface FileInfo {
  name: string
  path: string
  type: string
  size: number
  modified: string
  target?: string
}

export interface FolderInfo {
  name: string
  path: string
  files: FileInfo[]
  file_count: number
}

export interface FindingsExplorerResponse {
  folders: FolderInfo[]
  root_files: FileInfo[]
  total_files: number
  last_updated: string
}

export interface FileContentResponse {
  type: string
  content: any
  filename: string
}

export interface AgentLogEntry {
  timestamp: string
  type: string
  message: string
  metadata?: Record<string, any>
}
