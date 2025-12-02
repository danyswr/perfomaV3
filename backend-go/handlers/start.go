package handlers

import (
	"fmt"
	"performa-backend/models"
	"performa-backend/openrouter"
	"performa-backend/ws"

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

	agents := make([]*models.Agent, 0)
	roles := []string{"Scanner", "Analyzer", "Reporter", "Exploiter", "Validator"}

	for i := 0; i < req.AgentCount && i < len(roles); i++ {
		agent := models.Manager.CreateAgent(
			fmt.Sprintf("Agent-%d", i+1),
			roles[i],
			req.Target,
			req.Model,
		)
		agents = append(agents, agent)

		models.Manager.UpdateAgentStatus(agent.ID, models.AgentStatusRunning)

		go runAgentTask(agent, req)
	}

	ws.BroadcastMessage("system", fmt.Sprintf("Started %d agents targeting %s", len(agents), req.Target))

	return c.JSON(fiber.Map{
		"message": "Operation started successfully",
		"agents":  agents,
		"target":  req.Target,
		"model":   req.Model,
	})
}

func runAgentTask(agent *models.Agent, req models.StartRequest) {
	systemPrompt := fmt.Sprintf(`You are %s, a cybersecurity AI agent with the role of %s.
Your target is: %s
Category: %s
Mode: %s

Your task is to analyze the target and provide security insights based on your role.
Be thorough but concise in your analysis.`, agent.Name, agent.Role, req.Target, req.Category, req.Mode)

	userPrompt := fmt.Sprintf("Analyze the target %s and provide your findings as a %s.", req.Target, agent.Role)

	if req.Instructions != "" {
		userPrompt += "\n\nAdditional instructions: " + req.Instructions
	}

	messages := []openrouter.Message{
		{Role: "system", Content: systemPrompt},
		{Role: "user", Content: userPrompt},
	}

	response, err := openrouter.Chat(messages, req.Model)

	if err != nil {
		models.Manager.UpdateAgentStatus(agent.ID, models.AgentStatusError)
		models.Manager.AddMessage(agent.ID, "system", fmt.Sprintf("Error: %v", err))
		ws.BroadcastAgentUpdate(agent.ID, "error", err.Error())
		return
	}

	models.Manager.AddMessage(agent.ID, "assistant", response)
	models.Manager.UpdateAgentStatus(agent.ID, models.AgentStatusComplete)

	ws.BroadcastAgentUpdate(agent.ID, "complete", response)
}
