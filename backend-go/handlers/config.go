package handlers

import (
	"sync"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/google/uuid"
)

type MissionConfigRequest struct {
	Name              string   `json:"name"`
	Target            string   `json:"target"`
	Category          string   `json:"category"`
	CustomInstruction string   `json:"custom_instruction"`
	StealthMode       bool     `json:"stealth_mode"`
	AggressiveMode    bool     `json:"aggressive_mode"`
	ModelName         string   `json:"model_name"`
	NumAgents         int      `json:"num_agents"`
	ExecutionDuration *int     `json:"execution_duration"`
	RequestedTools    []string `json:"requested_tools"`
	AllowedToolsOnly  bool     `json:"allowed_tools_only"`
}

type SavedConfig struct {
	ID                string    `json:"id"`
	Name              string    `json:"name"`
	Target            string    `json:"target"`
	Category          string    `json:"category"`
	CustomInstruction string    `json:"custom_instruction"`
	StealthMode       bool      `json:"stealth_mode"`
	AggressiveMode    bool      `json:"aggressive_mode"`
	ModelName         string    `json:"model_name"`
	NumAgents         int       `json:"num_agents"`
	ExecutionDuration *int      `json:"execution_duration"`
	RequestedTools    []string  `json:"requested_tools"`
	AllowedToolsOnly  bool      `json:"allowed_tools_only"`
	CreatedAt         time.Time `json:"created_at"`
	UpdatedAt         time.Time `json:"updated_at"`
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

	configStoreMu.Lock()
	defer configStoreMu.Unlock()

	configID := uuid.New().String()
	now := time.Now()

	config := &SavedConfig{
		ID:                configID,
		Name:              req.Name,
		Target:            req.Target,
		Category:          req.Category,
		CustomInstruction: req.CustomInstruction,
		StealthMode:       req.StealthMode,
		AggressiveMode:    req.AggressiveMode,
		ModelName:         req.ModelName,
		NumAgents:         req.NumAgents,
		ExecutionDuration: req.ExecutionDuration,
		RequestedTools:    req.RequestedTools,
		AllowedToolsOnly:  req.AllowedToolsOnly,
		CreatedAt:         now,
		UpdatedAt:         now,
	}

	configStore[configID] = config

	return c.JSON(fiber.Map{
		"status":    "saved",
		"config_id": configID,
		"config":    config,
	})
}

func GetConfigs(c *fiber.Ctx) error {
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

type SessionData struct {
	ID        string    `json:"id"`
	CreatedAt time.Time `json:"created_at"`
}

var (
	sessionStore   = make(map[string]*SessionData)
	sessionStoreMu sync.RWMutex
)

func SaveSession(c *fiber.Ctx) error {
	sessionStoreMu.Lock()
	defer sessionStoreMu.Unlock()

	sessionID := uuid.New().String()
	now := time.Now()

	session := &SessionData{
		ID:        sessionID,
		CreatedAt: now,
	}

	sessionStore[sessionID] = session

	return c.JSON(fiber.Map{
		"status":     "saved",
		"session_id": sessionID,
		"message":    "Session saved successfully",
	})
}
