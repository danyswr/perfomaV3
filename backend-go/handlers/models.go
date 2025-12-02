package handlers

import (
	"performa-backend/models"

	"github.com/gofiber/fiber/v2"
)

func GetModels(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{
		"models": models.AvailableModels,
	})
}
