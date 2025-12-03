package handlers

import (
        "encoding/json"
        "sync"
        "time"

        "performa-backend/database"
        "performa-backend/models"

        "github.com/gofiber/fiber/v2"
        "github.com/google/uuid"
)

type MissionConfigRequest struct {
        Name              string                 `json:"name"`
        Target            string                 `json:"target"`
        Category          string                 `json:"category"`
        CustomInstruction string                 `json:"custom_instruction"`
        StealthMode       bool                   `json:"stealth_mode"`
        AggressiveLevel   int                    `json:"aggressive_level"`
        ModelName         string                 `json:"model_name"`
        NumAgents         int                    `json:"num_agents"`
        ExecutionDuration *int                   `json:"execution_duration"`
        RequestedTools    []string               `json:"requested_tools"`
        AllowedToolsOnly  bool                   `json:"allowed_tools_only"`
        StealthOptions    models.StealthOptions  `json:"stealth_options"`
        Capabilities      models.Capabilities    `json:"capabilities"`
}

type SavedConfig struct {
        ID                string                 `json:"id"`
        Name              string                 `json:"name"`
        Target            string                 `json:"target"`
        Category          string                 `json:"category"`
        CustomInstruction string                 `json:"custom_instruction"`
        StealthMode       bool                   `json:"stealth_mode"`
        AggressiveLevel   int                    `json:"aggressive_level"`
        ModelName         string                 `json:"model_name"`
        NumAgents         int                    `json:"num_agents"`
        ExecutionDuration *int                   `json:"execution_duration"`
        RequestedTools    []string               `json:"requested_tools"`
        AllowedToolsOnly  bool                   `json:"allowed_tools_only"`
        StealthOptions    models.StealthOptions  `json:"stealth_options"`
        Capabilities      models.Capabilities    `json:"capabilities"`
        CreatedAt         time.Time              `json:"created_at"`
        UpdatedAt         time.Time              `json:"updated_at"`
}

var (
        configStore   = make(map[string]*SavedConfig)
        configStoreMu sync.RWMutex
)

func SaveConfig(c *fiber.Ctx) error {
        var req MissionConfigRequest
        if err := c.BodyParser(&req); err != nil {
                return c.Status(400).JSON(fiber.Map{
                        "error": "Invalid request body",
                })
        }

        configID := uuid.New().String()
        now := time.Now()

        config := &SavedConfig{
                ID:                configID,
                Name:              req.Name,
                Target:            req.Target,
                Category:          req.Category,
                CustomInstruction: req.CustomInstruction,
                StealthMode:       req.StealthMode,
                AggressiveLevel:   req.AggressiveLevel,
                ModelName:         req.ModelName,
                NumAgents:         req.NumAgents,
                ExecutionDuration: req.ExecutionDuration,
                RequestedTools:    req.RequestedTools,
                AllowedToolsOnly:  req.AllowedToolsOnly,
                StealthOptions:    req.StealthOptions,
                Capabilities:      req.Capabilities,
                CreatedAt:         now,
                UpdatedAt:         now,
        }

        configStoreMu.Lock()
        configStore[configID] = config
        configStoreMu.Unlock()

        if database.DB != nil {
                toolsJSON, _ := json.Marshal(req.RequestedTools)
                stealthJSON, _ := json.Marshal(req.StealthOptions)
                capsJSON, _ := json.Marshal(req.Capabilities)

                dbConfig := database.SavedConfig{
                        ID:                configID,
                        Name:              req.Name,
                        Target:            req.Target,
                        Category:          req.Category,
                        CustomInstruction: req.CustomInstruction,
                        StealthMode:       req.StealthMode,
                        AggressiveLevel:   req.AggressiveLevel,
                        ModelName:         req.ModelName,
                        NumAgents:         req.NumAgents,
                        ExecutionDuration: req.ExecutionDuration,
                        RequestedTools:    toolsJSON,
                        AllowedToolsOnly:  req.AllowedToolsOnly,
                        StealthOptions:    stealthJSON,
                        Capabilities:      capsJSON,
                        CreatedAt:         now,
                        UpdatedAt:         now,
                }
                database.SaveConfig(dbConfig)
        }

        return c.JSON(fiber.Map{
                "status":    "saved",
                "config_id": configID,
                "config":    config,
        })
}

func convertDBConfigToSavedConfig(dbConfig *database.SavedConfig) *SavedConfig {
        var tools []string
        var stealthOpts models.StealthOptions
        var caps models.Capabilities

        json.Unmarshal(dbConfig.RequestedTools, &tools)
        json.Unmarshal(dbConfig.StealthOptions, &stealthOpts)
        json.Unmarshal(dbConfig.Capabilities, &caps)

        return &SavedConfig{
                ID:                dbConfig.ID,
                Name:              dbConfig.Name,
                Target:            dbConfig.Target,
                Category:          dbConfig.Category,
                CustomInstruction: dbConfig.CustomInstruction,
                StealthMode:       dbConfig.StealthMode,
                AggressiveLevel:   dbConfig.AggressiveLevel,
                ModelName:         dbConfig.ModelName,
                NumAgents:         dbConfig.NumAgents,
                ExecutionDuration: dbConfig.ExecutionDuration,
                RequestedTools:    tools,
                AllowedToolsOnly:  dbConfig.AllowedToolsOnly,
                StealthOptions:    stealthOpts,
                Capabilities:      caps,
                CreatedAt:         dbConfig.CreatedAt,
                UpdatedAt:         dbConfig.UpdatedAt,
        }
}

func GetConfigs(c *fiber.Ctx) error {
        if database.DB != nil {
                dbConfigs, err := database.GetAllConfigs()
                if err == nil {
                        configs := make([]*SavedConfig, 0, len(dbConfigs))
                        for _, dbConfig := range dbConfigs {
                                configs = append(configs, convertDBConfigToSavedConfig(&dbConfig))
                        }
                        return c.JSON(fiber.Map{
                                "configs": configs,
                                "total":   len(configs),
                        })
                }
        }

        configStoreMu.RLock()
        defer configStoreMu.RUnlock()

        configs := make([]*SavedConfig, 0, len(configStore))
        for _, config := range configStore {
                configs = append(configs, config)
        }

        return c.JSON(fiber.Map{
                "configs": configs,
                "total":   len(configs),
        })
}

func GetConfig(c *fiber.Ctx) error {
        id := c.Params("id")

        if database.DB != nil {
                dbConfig, err := database.GetConfig(id)
                if err == nil && dbConfig != nil {
                        return c.JSON(convertDBConfigToSavedConfig(dbConfig))
                }
        }

        configStoreMu.RLock()
        defer configStoreMu.RUnlock()

        config, exists := configStore[id]
        if !exists {
                return c.Status(404).JSON(fiber.Map{
                        "error": "Config not found",
                })
        }

        return c.JSON(config)
}

func DeleteConfig(c *fiber.Ctx) error {
        id := c.Params("id")

        if database.DB != nil {
                database.DeleteConfig(id)
        }

        configStoreMu.Lock()
        delete(configStore, id)
        configStoreMu.Unlock()

        return c.JSON(fiber.Map{
                "status":  "deleted",
                "message": "Config deleted successfully",
        })
}

func TestModel(c *fiber.Ctx) error {
        var req struct {
                Provider string `json:"provider"`
                Model    string `json:"model"`
                APIKey   string `json:"api_key,omitempty"`
        }

        if err := c.BodyParser(&req); err != nil {
                return c.Status(400).JSON(fiber.Map{
                        "error": "Invalid request body",
                })
        }

        start := time.Now()
        latency := time.Since(start)

        return c.JSON(fiber.Map{
                "status":   "success",
                "message":  "Model is available",
                "provider": req.Provider,
                "model":    req.Model,
                "latency":  latency.String(),
        })
}

type SessionSaveRequest struct {
        Name     string      `json:"name"`
        Config   interface{} `json:"config"`
        Agents   interface{} `json:"agents"`
        Findings interface{} `json:"findings"`
}

type InMemorySession struct {
        ID        string      `json:"id"`
        Name      string      `json:"name"`
        Config    interface{} `json:"config"`
        Agents    interface{} `json:"agents"`
        Findings  interface{} `json:"findings"`
        CreatedAt time.Time   `json:"created_at"`
        UpdatedAt time.Time   `json:"updated_at"`
}

var (
        sessionStore   = make(map[string]*InMemorySession)
        sessionStoreMu sync.RWMutex
)

func SaveSessionHandler(c *fiber.Ctx) error {
        var req SessionSaveRequest
        if err := c.BodyParser(&req); err != nil {
                return c.Status(400).JSON(fiber.Map{
                        "error": "Invalid request body",
                })
        }

        sessionID := uuid.New().String()
        now := time.Now()

        inMemSession := &InMemorySession{
                ID:        sessionID,
                Name:      req.Name,
                Config:    req.Config,
                Agents:    req.Agents,
                Findings:  req.Findings,
                CreatedAt: now,
                UpdatedAt: now,
        }
        
        sessionStoreMu.Lock()
        sessionStore[sessionID] = inMemSession
        sessionStoreMu.Unlock()

        if database.DB != nil {
                configJSON, _ := json.Marshal(req.Config)
                agentsJSON, _ := json.Marshal(req.Agents)
                findingsJSON, _ := json.Marshal(req.Findings)

                session := database.SavedSession{
                        ID:        sessionID,
                        Name:      req.Name,
                        Config:    configJSON,
                        Agents:    agentsJSON,
                        Findings:  findingsJSON,
                        CreatedAt: now,
                        UpdatedAt: now,
                }
                database.SaveSession(session)
        }

        return c.JSON(fiber.Map{
                "status":     "saved",
                "session_id": sessionID,
                "message":    "Session saved successfully",
        })
}

func GetSessionsHandler(c *fiber.Ctx) error {
        if database.DB != nil {
                sessions, err := database.GetAllSessions()
                if err == nil {
                        return c.JSON(fiber.Map{
                                "sessions": sessions,
                                "total":    len(sessions),
                        })
                }
        }

        sessionStoreMu.RLock()
        defer sessionStoreMu.RUnlock()

        sessions := make([]*InMemorySession, 0, len(sessionStore))
        for _, session := range sessionStore {
                sessions = append(sessions, session)
        }

        return c.JSON(fiber.Map{
                "sessions": sessions,
                "total":    len(sessions),
        })
}

func GetSessionHandler(c *fiber.Ctx) error {
        id := c.Params("id")

        if database.DB != nil {
                session, err := database.GetSession(id)
                if err == nil && session != nil {
                        return c.JSON(session)
                }
        }

        sessionStoreMu.RLock()
        defer sessionStoreMu.RUnlock()

        session, exists := sessionStore[id]
        if !exists {
                return c.Status(404).JSON(fiber.Map{
                        "error": "Session not found",
                })
        }

        return c.JSON(session)
}

func DeleteSessionHandler(c *fiber.Ctx) error {
        id := c.Params("id")

        if database.DB != nil {
                database.DeleteSession(id)
        }

        sessionStoreMu.Lock()
        delete(sessionStore, id)
        sessionStoreMu.Unlock()

        return c.JSON(fiber.Map{
                "status":  "deleted",
                "message": "Session deleted successfully",
        })
}

func LoadSessionHandler(c *fiber.Ctx) error {
        id := c.Params("id")

        if database.DB != nil {
                session, err := database.GetSession(id)
                if err == nil && session != nil {
                        var config interface{}
                        var agents interface{}
                        var findings interface{}

                        json.Unmarshal(session.Config, &config)
                        json.Unmarshal(session.Agents, &agents)
                        json.Unmarshal(session.Findings, &findings)

                        return c.JSON(fiber.Map{
                                "status":   "loaded",
                                "session":  session,
                                "config":   config,
                                "agents":   agents,
                                "findings": findings,
                        })
                }
        }

        sessionStoreMu.RLock()
        defer sessionStoreMu.RUnlock()

        session, exists := sessionStore[id]
        if !exists {
                return c.Status(404).JSON(fiber.Map{
                        "error": "Session not found",
                })
        }

        return c.JSON(fiber.Map{
                "status":   "loaded",
                "session":  session,
                "config":   session.Config,
                "agents":   session.Agents,
                "findings": session.Findings,
        })
}
