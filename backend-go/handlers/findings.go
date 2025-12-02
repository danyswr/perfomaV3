package handlers

import (
	"performa-backend/models"

	"github.com/gofiber/fiber/v2"
)

func GetFindings(c *fiber.Ctx) error {
	findings := models.Findings.GetAllFindings()
	return c.JSON(fiber.Map{
		"findings": findings,
		"count":    len(findings),
	})
}

func GetFinding(c *fiber.Ctx) error {
	id := c.Params("id")
	finding := models.Findings.GetFinding(id)

	if finding == nil {
		return c.Status(404).JSON(fiber.Map{
			"error": "Finding not found",
		})
	}

	return c.JSON(finding)
}

func CreateFinding(c *fiber.Ctx) error {
	var req struct {
		Title       string `json:"title"`
		Description string `json:"description"`
		Severity    string `json:"severity"`
		Category    string `json:"category"`
		Target      string `json:"target"`
		Evidence    string `json:"evidence"`
		AgentID     string `json:"agent_id"`
	}

	if err := c.BodyParser(&req); err != nil {
		return c.Status(400).JSON(fiber.Map{
			"error": "Invalid request body",
		})
	}

	finding := models.Findings.AddFinding(
		req.Title,
		req.Description,
		models.Severity(req.Severity),
		req.Category,
		req.Target,
		req.Evidence,
		req.AgentID,
	)

	return c.Status(201).JSON(finding)
}
