package handlers

import (
        "log"
        "time"

        "performa-backend/brain"
        "performa-backend/config"

        "github.com/gofiber/fiber/v2"
)

var brainClient *brain.BrainClient
var brainAvailable bool = false

func InitBrainClient() {
        brainClient = brain.NewBrainClient(config.AppConfig.BrainServiceURL)
        
        go func() {
                log.Println("Waiting for Brain service to become available...")
                err := brainClient.WaitForHealthy(30, 2*time.Second)
                if err != nil {
                        log.Printf("Warning: Brain service not available: %v", err)
                        brainAvailable = false
                } else {
                        log.Println("Brain service is healthy and ready")
                        brainAvailable = true
                }
        }()
}

func checkBrainAvailable(c *fiber.Ctx) error {
        if brainClient == nil {
                return c.Status(500).JSON(fiber.Map{
                        "error": "Brain client not initialized",
                })
        }
        
        if !brainAvailable {
                if brainClient.IsHealthy() {
                        brainAvailable = true
                } else {
                        return c.Status(503).JSON(fiber.Map{
                                "error":   "Brain service temporarily unavailable",
                                "message": "The AI intelligence service is starting up or unavailable",
                        })
                }
        }
        return nil
}

func GetBrainStatus(c *fiber.Ctx) error {
        if err := checkBrainAvailable(c); err != nil {
                return err
        }

        status, err := brainClient.GetStatus()
        if err != nil {
                brainAvailable = false
                return c.Status(503).JSON(fiber.Map{
                        "error":   "Brain service unavailable",
                        "details": err.Error(),
                })
        }

        return c.JSON(status)
}

func BrainHealth(c *fiber.Ctx) error {
        if brainClient == nil {
                return c.Status(500).JSON(fiber.Map{
                        "error": "Brain client not initialized",
                })
        }

        health, err := brainClient.Health()
        if err != nil {
                brainAvailable = false
                return c.Status(503).JSON(fiber.Map{
                        "status":  "unhealthy",
                        "error":   err.Error(),
                })
        }

        brainAvailable = true
        return c.JSON(health)
}

func BrainThink(c *fiber.Ctx) error {
        if err := checkBrainAvailable(c); err != nil {
                return err
        }

        var req brain.ThinkRequest
        if err := c.BodyParser(&req); err != nil {
                return c.Status(400).JSON(fiber.Map{
                        "error": "Invalid request body",
                })
        }

        result, err := brainClient.Think(&req)
        if err != nil {
                brainAvailable = false
                return c.Status(500).JSON(fiber.Map{
                        "error":   "Brain thinking failed",
                        "details": err.Error(),
                })
        }

        return c.JSON(result)
}

func BrainClassify(c *fiber.Ctx) error {
        if err := checkBrainAvailable(c); err != nil {
                return err
        }

        var req brain.ClassifyRequest
        if err := c.BodyParser(&req); err != nil {
                return c.Status(400).JSON(fiber.Map{
                        "error": "Invalid request body",
                })
        }

        result, err := brainClient.ClassifyThreat(&req)
        if err != nil {
                return c.Status(500).JSON(fiber.Map{
                        "error":   "Classification failed",
                        "details": err.Error(),
                })
        }

        return c.JSON(result)
}

func BrainEvaluate(c *fiber.Ctx) error {
        if err := checkBrainAvailable(c); err != nil {
                return err
        }

        var req brain.EvaluateRequest
        if err := c.BodyParser(&req); err != nil {
                return c.Status(400).JSON(fiber.Map{
                        "error": "Invalid request body",
                })
        }

        result, err := brainClient.EvaluateAction(&req)
        if err != nil {
                return c.Status(500).JSON(fiber.Map{
                        "error":   "Evaluation failed",
                        "details": err.Error(),
                })
        }

        return c.JSON(result)
}

func BrainStrategy(c *fiber.Ctx) error {
        if err := checkBrainAvailable(c); err != nil {
                return err
        }

        var req brain.StrategyRequest
        if err := c.BodyParser(&req); err != nil {
                return c.Status(400).JSON(fiber.Map{
                        "error": "Invalid request body",
                })
        }

        result, err := brainClient.GenerateStrategy(&req)
        if err != nil {
                return c.Status(500).JSON(fiber.Map{
                        "error":   "Strategy generation failed",
                        "details": err.Error(),
                })
        }

        return c.JSON(result)
}

func BrainModels(c *fiber.Ctx) error {
        if err := checkBrainAvailable(c); err != nil {
                return err
        }

        models, err := brainClient.GetModels()
        if err != nil {
                return c.Status(500).JSON(fiber.Map{
                        "error":   "Failed to get models",
                        "details": err.Error(),
                })
        }

        return c.JSON(fiber.Map{
                "models": models,
        })
}

func BrainLearn(c *fiber.Ctx) error {
        if err := checkBrainAvailable(c); err != nil {
                return err
        }

        var req struct {
                Action  map[string]interface{} `json:"action"`
                Outcome map[string]interface{} `json:"outcome"`
        }
        if err := c.BodyParser(&req); err != nil {
                return c.Status(400).JSON(fiber.Map{
                        "error": "Invalid request body",
                })
        }

        err := brainClient.Learn(req.Action, req.Outcome)
        if err != nil {
                return c.Status(500).JSON(fiber.Map{
                        "error":   "Learning failed",
                        "details": err.Error(),
                })
        }

        return c.JSON(fiber.Map{
                "status": "learned",
        })
}

func BrainReset(c *fiber.Ctx) error {
        if err := checkBrainAvailable(c); err != nil {
                return err
        }

        err := brainClient.Reset()
        if err != nil {
                return c.Status(500).JSON(fiber.Map{
                        "error":   "Reset failed",
                        "details": err.Error(),
                })
        }

        return c.JSON(fiber.Map{
                "status": "reset",
        })
}
