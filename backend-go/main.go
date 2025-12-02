package main

import (
	"fmt"
	"log"
	"os"
	"time"

	"performa-backend/config"
	"performa-backend/handlers"
	"performa-backend/models"
	"performa-backend/ws"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/cors"
	"github.com/gofiber/fiber/v2/middleware/logger"
	"github.com/gofiber/fiber/v2/middleware/recover"
	"github.com/gofiber/websocket/v2"
	"github.com/shirou/gopsutil/v3/cpu"
	"github.com/shirou/gopsutil/v3/disk"
	"github.com/shirou/gopsutil/v3/mem"
	"github.com/shirou/gopsutil/v3/net"
)

func main() {
	printBanner()

	config.Load()

	os.MkdirAll(config.AppConfig.LogDir, 0755)
	os.MkdirAll(config.AppConfig.FindingsDir, 0755)

	models.Findings.SetFindingsDir(config.AppConfig.FindingsDir)
	models.Findings.LoadFindings()

	go ws.MainHub.Run()

	go startResourceMonitor()

	app := fiber.New(fiber.Config{
		AppName:       "Performa - Autonomous CyberSec AI Agent",
		ServerHeader:  "Performa",
		StrictRouting: false,
		CaseSensitive: false,
	})

	app.Use(recover.New())
	app.Use(logger.New(logger.Config{
		Format:     "${time} | ${status} | ${latency} | ${method} ${path}\n",
		TimeFormat: "2006-01-02 15:04:05",
	}))

	app.Use(cors.New(cors.Config{
		AllowOrigins: "*",
		AllowMethods: "GET,POST,PUT,DELETE,OPTIONS",
		AllowHeaders: "*",
	}))

	app.Get("/", func(c *fiber.Ctx) error {
		return c.JSON(fiber.Map{
			"message": "Autonomous CyberSec AI Agent System API",
			"version": "2.0.0-go",
			"status":  "running",
		})
	})

	api := app.Group("/api")
	{
		api.Post("/start", handlers.StartOperation)

		api.Get("/agents", handlers.GetAgents)
		api.Get("/agents/:id", handlers.GetAgent)
		api.Delete("/agents/:id", handlers.DeleteAgent)
		api.Post("/agents/:id/pause", handlers.PauseAgent)
		api.Post("/agents/:id/resume", handlers.ResumeAgent)

		api.Get("/resources", handlers.GetResources)

		api.Get("/findings", handlers.GetFindings)
		api.Get("/findings/:id", handlers.GetFinding)
		api.Post("/findings", handlers.CreateFinding)

		api.Get("/models", handlers.GetModels)
	}

	app.Use("/ws", ws.WebSocketUpgrade)
	app.Get("/ws/live", websocket.New(ws.HandleWebSocket))

	printStartupInfo()

	addr := fmt.Sprintf("%s:%d", config.AppConfig.Host, config.AppConfig.Port)
	log.Printf("🚀 Server starting on http://%s", addr)

	if err := app.Listen(addr); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}

func printBanner() {
	banner := `
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║   ██████╗ ███████╗██████╗ ███████╗ ██████╗ ██████╗ ███╗   ███╗ █████╗   ║
║   ██╔══██╗██╔════╝██╔══██╗██╔════╝██╔═══██╗██╔══██╗████╗ ████║██╔══██╗  ║
║   ██████╔╝█████╗  ██████╔╝█████╗  ██║   ██║██████╔╝██╔████╔██║███████║  ║
║   ██╔═══╝ ██╔══╝  ██╔══██╗██╔══╝  ██║   ██║██╔══██╗██║╚██╔╝██║██╔══██║  ║
║   ██║     ███████╗██║  ██║██║     ╚██████╔╝██║  ██║██║ ╚═╝ ██║██║  ██║  ║
║   ╚═╝     ╚══════╝╚═╝  ╚═╝╚═╝      ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝  ║
║                                                                ║
║           Autonomous CyberSec AI Agent System (Go)             ║
╚════════════════════════════════════════════════════════════════╝
`
	fmt.Println(banner)
}

func printStartupInfo() {
	fmt.Println("🚀 Autonomous CyberSec AI Agent System Starting...")
	fmt.Printf("📁 Log Directory: %s\n", config.AppConfig.LogDir)
	fmt.Printf("📁 Findings Directory: %s\n", config.AppConfig.FindingsDir)

	if config.AppConfig.OpenRouterAPIKey != "" && config.AppConfig.OpenRouterAPIKey != "your_key" {
		fmt.Println("🔑 OpenRouter API Key: ✓ Configured")
	} else {
		fmt.Println("🔑 OpenRouter API Key: ✗ Not configured (simulation mode)")
	}

	if config.AppConfig.AnthropicAPIKey != "" {
		fmt.Println("🔑 Anthropic API Key: ✓ Configured")
	} else {
		fmt.Println("🔑 Anthropic API Key: ✗ Not configured")
	}

	if config.AppConfig.OpenAIAPIKey != "" {
		fmt.Println("🔑 OpenAI API Key: ✓ Configured")
	} else {
		fmt.Println("🔑 OpenAI API Key: ✗ Not configured")
	}
}

func startResourceMonitor() {
	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		cpuPercent, _ := cpu.Percent(0, false)
		cpuUsage := 0.0
		if len(cpuPercent) > 0 {
			cpuUsage = cpuPercent[0]
		}

		memInfo, _ := mem.VirtualMemory()
		memUsage := 0.0
		if memInfo != nil {
			memUsage = memInfo.UsedPercent
		}

		diskInfo, _ := disk.Usage("/")
		diskUsage := 0.0
		if diskInfo != nil {
			diskUsage = diskInfo.UsedPercent
		}

		netIO, _ := net.IOCounters(false)
		networkUsage := 0.0
		if len(netIO) > 0 {
			networkUsage = float64(netIO[0].BytesSent+netIO[0].BytesRecv) / 1024 / 1024
		}

		ws.BroadcastResources(cpuUsage, memUsage, diskUsage, networkUsage)
	}
}
