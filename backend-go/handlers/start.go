package handlers

import (
        "fmt"
        "math/rand"
        "performa-backend/models"
        "performa-backend/openrouter"
        "performa-backend/tools"
        "performa-backend/ws"
        "strings"
        "time"

        "github.com/gofiber/fiber/v2"
)

func StartOperation(c *fiber.Ctx) error {
        var req models.StartRequest
        if err := c.BodyParser(&req); err != nil {
                return c.Status(400).JSON(fiber.Map{
                        "error": "Invalid request body",
                })
        }

        if req.Target == "" {
                return c.Status(400).JSON(fiber.Map{
                        "error": "Target is required",
                })
        }

        if req.AgentCount <= 0 {
                req.AgentCount = 3
        }

        if req.Model == "" {
                req.Model = "anthropic/claude-3.5-sonnet"
        }

        if req.OSType == "" {
                req.OSType = "linux"
        }

        agentConfig := models.AgentConfig{
                StealthMode:      req.StealthMode,
                AggressiveLevel:  req.AggressiveLevel,
                RequestedTools:   req.RequestedTools,
                AllowedToolsOnly: req.AllowedToolsOnly,
                StealthOptions:   req.StealthOptions,
                Capabilities:     req.Capabilities,
                OSType:           req.OSType,
        }

        agents := make([]*models.Agent, 0)
        roles := []string{"Scanner", "Analyzer", "Reporter", "Exploiter", "Validator"}

        for i := 0; i < req.AgentCount && i < len(roles); i++ {
                agent := models.Manager.CreateAgentWithConfig(
                        fmt.Sprintf("Agent-%d", i+1),
                        roles[i],
                        req.Target,
                        req.Model,
                        agentConfig,
                )
                agents = append(agents, agent)

                models.Manager.UpdateAgentStatus(agent.ID, models.AgentStatusRunning)

                go runAgentTask(agent, req)
        }

        ws.BroadcastMessage("system", fmt.Sprintf("Started %d agents targeting %s", len(agents), req.Target))

        return c.JSON(fiber.Map{
                "message":       "Operation started successfully",
                "agents":        agents,
                "target":        req.Target,
                "model":         req.Model,
                "stealth_mode":  req.StealthMode,
                "tools_enabled": len(req.RequestedTools),
        })
}

func runAgentTask(agent *models.Agent, req models.StartRequest) {
        if req.AllowedToolsOnly && len(req.RequestedTools) > 0 {
                agent.Config.RequestedTools = req.RequestedTools
                agent.Config.AllowedToolsOnly = true
        }

        stealthInfo := ""
        if req.StealthMode {
                stealthInfo = "\nStealth Mode: ENABLED"
                if req.StealthOptions.ProxyChain {
                        stealthInfo += "\n- Proxy chaining active"
                }
                if req.StealthOptions.TorRouting {
                        stealthInfo += "\n- Tor routing enabled"
                }
                if req.StealthOptions.TimingJitter {
                        stealthInfo += "\n- Timing jitter applied"
                }
                if req.StealthOptions.UserAgentRot {
                        stealthInfo += "\n- User agent rotation active"
                }
        }

        capsInfo := ""
        if req.Capabilities.PacketInjection {
                capsInfo += "\n- Packet injection capability"
        }
        if req.Capabilities.MITMAttacks {
                capsInfo += "\n- MITM attack capability"
        }
        if req.Capabilities.WebSocketHijack {
                capsInfo += "\n- WebSocket hijacking capability"
        }
        if req.Capabilities.SSLStripping {
                capsInfo += "\n- SSL stripping capability"
        }
        if req.Capabilities.DNSSpoof {
                capsInfo += "\n- DNS spoofing capability"
        }

        toolsInfo := ""
        if req.AllowedToolsOnly && len(req.RequestedTools) > 0 {
                toolsInfo = fmt.Sprintf("\n\nALLOWED TOOLS ONLY: You may ONLY use these tools: %s\nDo NOT attempt to use any other tools.", strings.Join(req.RequestedTools, ", "))
        } else if len(req.RequestedTools) > 0 {
                toolsInfo = fmt.Sprintf("\n\nPreferred tools: %s", strings.Join(req.RequestedTools, ", "))
        }

        modeInfo := "balanced"
        if req.AggressiveLevel > 2 {
                modeInfo = "aggressive"
        } else if req.StealthMode {
                modeInfo = "stealth"
        }

        systemPrompt := fmt.Sprintf(`You are %s, a cybersecurity AI agent with the role of %s.
Your target is: %s
Category: %s
Operating Mode: %s
Aggressive Level: %d/5
Target OS: %s
%s%s%s

IMPORTANT RULES:
1. You must respect the tool restrictions. If AllowedToolsOnly is set, ONLY use the specified tools.
2. All commands must be verified against the allowed tools list before execution.
3. Dangerous commands (rm -rf, mkfs, chmod 777, etc.) are STRICTLY FORBIDDEN.
4. Report all findings with severity levels (critical, high, medium, low, info).

Your task is to analyze the target and provide security insights based on your role.
Be thorough but concise in your analysis.`, 
                agent.Name, agent.Role, req.Target, req.Category, modeInfo, 
                req.AggressiveLevel, req.OSType, stealthInfo, capsInfo, toolsInfo)

        userPrompt := fmt.Sprintf("Analyze the target %s and provide your findings as a %s.", req.Target, agent.Role)

        if req.Instructions != "" {
                userPrompt += "\n\nAdditional instructions: " + req.Instructions
        }

        messages := []openrouter.Message{
                {Role: "system", Content: systemPrompt},
                {Role: "user", Content: userPrompt},
        }

        models.Manager.UpdateAgentProgress(agent.ID, 10, "Initializing analysis")
        simulateResourceUsage(agent.ID)

        if req.StealthMode && req.StealthOptions.TimingJitter {
                jitter := rand.Intn(2000) + 500
                time.Sleep(time.Duration(jitter) * time.Millisecond)
        }

        models.Manager.UpdateAgentProgress(agent.ID, 30, "Connecting to AI model")
        response, err := openrouter.Chat(messages, req.Model)

        if err != nil {
                models.Manager.UpdateAgentStatus(agent.ID, models.AgentStatusError)
                models.Manager.AddMessage(agent.ID, "system", fmt.Sprintf("Error: %v", err))
                ws.BroadcastAgentUpdate(agent.ID, "error", err.Error())
                return
        }

        if req.AllowedToolsOnly && len(req.RequestedTools) > 0 {
                response = validateToolUsage(response, req.RequestedTools)
        }

        models.Manager.UpdateAgentProgress(agent.ID, 70, "Processing results")
        models.Manager.AddMessage(agent.ID, "assistant", response)
        models.Manager.IncrementTaskCount(agent.ID)

        if strings.Contains(strings.ToLower(response), "vulnerability") || 
           strings.Contains(strings.ToLower(response), "finding") {
                models.Manager.IncrementFindings(agent.ID)
        }

        models.Manager.UpdateAgentProgress(agent.ID, 100, "Analysis complete")
        models.Manager.UpdateAgentStatus(agent.ID, models.AgentStatusComplete)

        ws.BroadcastAgentUpdate(agent.ID, "complete", response)
}

func simulateResourceUsage(agentID string) {
        go func() {
                baseCPU := float64(rand.Intn(30) + 15)
                baseMem := float64(rand.Intn(150) + 80)
                
                for i := 0; i < 60; i++ {
                        cpuUsage := baseCPU + float64(rand.Intn(20)-10)
                        if cpuUsage < 5 {
                                cpuUsage = 5
                        }
                        if cpuUsage > 95 {
                                cpuUsage = 95
                        }
                        
                        memUsage := baseMem + float64(rand.Intn(40)-20)
                        if memUsage < 50 {
                                memUsage = 50
                        }
                        
                        resources := models.AgentResources{
                                CPUUsage:    cpuUsage,
                                MemoryUsage: memUsage,
                                DiskUsage:   float64(rand.Intn(20) + 5),
                                NetworkIO:   float64(rand.Intn(500) + 50),
                        }
                        models.Manager.UpdateAgentResources(agentID, resources)
                        
                        ws.BroadcastResourceUpdate(agentID, resources.CPUUsage, resources.MemoryUsage)
                        
                        time.Sleep(500 * time.Millisecond)
                        
                        agent := models.Manager.GetAgent(agentID)
                        if agent == nil || agent.Status == models.AgentStatusComplete || agent.Status == models.AgentStatusError {
                                ws.BroadcastResourceUpdate(agentID, 0, memUsage*0.3)
                                break
                        }
                }
        }()
}

func validateToolUsage(response string, allowedTools []string) string {
        for _, category := range []string{"network_recon", "web_scanning", "vuln_scanning", "exploitation", "osint", "system_info"} {
                categoryTools := tools.FilterToolsByCategory(category)
                for _, tool := range categoryTools {
                        if strings.Contains(response, tool) && !isInSlice(tool, allowedTools) {
                                response = strings.ReplaceAll(response, tool, fmt.Sprintf("[BLOCKED: %s not in allowed tools]", tool))
                        }
                }
        }
        return response
}

func isInSlice(item string, slice []string) bool {
        for _, s := range slice {
                if s == item {
                        return true
                }
        }
        return false
}
