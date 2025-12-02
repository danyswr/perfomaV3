package handlers

import (
	"performa-backend/models"

	"github.com/gofiber/fiber/v2"
)

func GetAgents(c *fiber.Ctx) error {
	agents := models.Manager.GetAllAgents()
	return c.JSON(fiber.Map{
		"agents": agents,
		"count":  len(agents),
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
