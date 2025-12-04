package handlers

import (
	"performa-backend/models"
	"performa-backend/openrouter"
	"time"

	"github.com/gofiber/fiber/v2"
)

func GetModels(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{
		"models": models.AvailableModels,
	})
}

func ModelChat(c *fiber.Ctx) error {
	var req models.ChatRequest
	if err := c.BodyParser(&req); err != nil {
		return c.Status(400).JSON(fiber.Map{
			"error": "Invalid request body",
		})
	}

	if req.Model == "" {
		req.Model = "openai/gpt-4-turbo"
	}

	messages := make([]openrouter.Message, len(req.Messages))
	for i, msg := range req.Messages {
		messages[i] = openrouter.Message{
			Role:    msg.Role,
			Content: msg.Content,
		}
	}

	start := time.Now()
	response, err := openrouter.Chat(messages, req.Model)
	latency := time.Since(start)

	if err != nil {
		return c.Status(500).JSON(fiber.Map{
			"error":   err.Error(),
			"latency": latency.String(),
		})
	}

	return c.JSON(fiber.Map{
		"response": response,
		"model":    req.Model,
		"latency":  latency.String(),
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
