package handlers

import (
        "performa-backend/models"

        "github.com/gofiber/fiber/v2"
)

type CreateAgentRequest struct {
        Target            string `json:"target"`
        Category          string `json:"category"`
        CustomInstruction string `json:"custom_instruction"`
        StealthMode       bool   `json:"stealth_mode"`
        AggressiveMode    bool   `json:"aggressive_mode"`
        ModelName         string `json:"model_name"`
}

func CreateAgent(c *fiber.Ctx) error {
        var req CreateAgentRequest
        if err := c.BodyParser(&req); err != nil {
                req = CreateAgentRequest{}
        }

        modelName := req.ModelName
        if modelName == "" {
                modelName = "openai/gpt-4-turbo"
        }

        agent := models.Manager.CreateAgent(
                "Agent",
                "security-scanner",
                req.Target,
                modelName,
        )

        if req.Target != "" {
                models.Manager.UpdateAgentStatus(agent.ID, models.AgentStatusRunning)
        }

        return c.JSON(fiber.Map{
                "status":   "created",
                "agent_id": agent.ID,
                "agent":    agent,
        })
}

func GetAgents(c *fiber.Ctx) error {
        agents := models.Manager.GetAllAgents()
        return c.JSON(fiber.Map{
                "agents": agents,
                "total":  len(agents),
        })
}

func GetAgent(c *fiber.Ctx) error {
        id := c.Params("id")
        agent := models.Manager.GetAgent(id)

        if agent == nil {
                return c.Status(404).JSON(fiber.Map{
                        "error": "Agent not found",
                })
        }

        messages := models.Manager.GetMessages(id)
        return c.JSON(fiber.Map{
                "agent":    agent,
                "messages": messages,
        })
}

func DeleteAgent(c *fiber.Ctx) error {
        id := c.Params("id")
        if models.Manager.DeleteAgent(id) {
                return c.JSON(fiber.Map{
                        "message": "Agent deleted successfully",
                })
        }

        return c.Status(404).JSON(fiber.Map{
                "error": "Agent not found",
        })
}

func PauseAgent(c *fiber.Ctx) error {
        id := c.Params("id")
        if models.Manager.PauseAgent(id) {
                return c.JSON(fiber.Map{
                        "message": "Agent paused successfully",
                })
        }

        return c.Status(400).JSON(fiber.Map{
                "error": "Cannot pause agent",
        })
}

func ResumeAgent(c *fiber.Ctx) error {
        id := c.Params("id")
        if models.Manager.ResumeAgent(id) {
                return c.JSON(fiber.Map{
                        "message": "Agent resumed successfully",
                })
        }

        return c.Status(400).JSON(fiber.Map{
                "error": "Cannot resume agent",
        })
}
