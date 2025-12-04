package main

import (
        "fmt"
        "log"
        "os"
        "time"

        "performa-backend/config"
        "performa-backend/database"
        "performa-backend/handlers"
        "performa-backend/models"
        "performa-backend/ws"

        "github.com/gofiber/fiber/v2"
        "github.com/gofiber/fiber/v2/middleware/cors"
        "github.com/gofiber/fiber/v2/middleware/logger"
        "github.com/gofiber/fiber/v2/middleware/proxy"
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

        if err := database.Init(); err != nil {
                log.Printf("Warning: Database initialization failed: %v", err)
        }
        defer database.Close()

        os.MkdirAll(config.AppConfig.LogDir, 0755)
        os.MkdirAll(config.AppConfig.FindingsDir, 0755)

        models.Findings.SetFindingsDir(config.AppConfig.FindingsDir)
        models.Findings.LoadFindings()

        handlers.InitBrainClient()

        go ws.MainHub.Run()

        go startResourceMonitor()

        app := fiber.New(fiber.Config{
                AppName:       "Performa - Backend Infrastructure",
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
                        "message": "Performa Backend Infrastructure",
                        "version": "2.0.0",
                        "status":  "running",
                        "services": fiber.Map{
                                "resources":    "System resource monitoring",
                                "models":       "AI model connections",
                                "findings":     "Security findings management",
                                "websocket":    "Real-time updates",
                                "brain_proxy":  "Proxy to Agent Brain service",
                        },
                })
        })

        app.Get("/api/health", func(c *fiber.Ctx) error {
                return c.JSON(fiber.Map{
                        "status":  "healthy",
                        "service": "backend-go",
                })
        })

        api := app.Group("/api")
        {
                api.Get("/resources", handlers.GetResources)

                api.Get("/models", handlers.GetModels)
                api.Post("/models/chat", handlers.ModelChat)
                api.Post("/models/test", handlers.TestModel)

                api.Get("/findings", handlers.GetFindings)
                api.Get("/findings/logs", handlers.GetFindingsLogs)
                api.Get("/findings/explorer", handlers.GetFindingsExplorer)
                api.Get("/findings/:id", handlers.GetFinding)
                api.Post("/findings", handlers.CreateFinding)

                brain := api.Group("/brain")
                {
                        brain.Get("/health", handlers.BrainHealth)
                        brain.Get("/status", handlers.GetBrainStatus)
                        brain.Post("/think", handlers.BrainThink)
                        brain.Post("/classify", handlers.BrainClassify)
                        brain.Post("/evaluate", handlers.BrainEvaluate)
                        brain.Post("/strategy", handlers.BrainStrategy)
                        brain.Get("/models", handlers.BrainModels)
                        brain.Post("/learn", handlers.BrainLearn)
                        brain.Post("/reset", handlers.BrainReset)
                }
        }

        brainURL := config.AppConfig.BrainServiceURL
        
        app.All("/api/config", func(c *fiber.Ctx) error {
                return proxy.Do(c, brainURL+"/api/config")
        })
        app.All("/api/config/*", func(c *fiber.Ctx) error {
                return proxy.Do(c, brainURL+"/api/config/"+c.Params("*"))
        })
        
        app.All("/api/agents", func(c *fiber.Ctx) error {
                return proxy.Do(c, brainURL+"/api/agents")
        })
        app.All("/api/agents/*", func(c *fiber.Ctx) error {
                return proxy.Do(c, brainURL+"/api/agents/"+c.Params("*"))
        })
        
        app.All("/api/mission", func(c *fiber.Ctx) error {
                return proxy.Do(c, brainURL+"/api/mission")
        })
        app.All("/api/mission/*", func(c *fiber.Ctx) error {
                return proxy.Do(c, brainURL+"/api/mission/"+c.Params("*"))
        })
        
        app.All("/api/session", func(c *fiber.Ctx) error {
                return proxy.Do(c, brainURL+"/api/session")
        })
        app.All("/api/session/*", func(c *fiber.Ctx) error {
                return proxy.Do(c, brainURL+"/api/session/"+c.Params("*"))
        })

        app.All("/api/start", func(c *fiber.Ctx) error {
                return proxy.Do(c, brainURL+"/api/start")
        })

        app.All("/api/stop", func(c *fiber.Ctx) error {
                return proxy.Do(c, brainURL+"/api/stop")
        })

        app.Use("/ws", ws.WebSocketUpgrade)
        app.Get("/ws/live", websocket.New(ws.HandleWebSocket))

        printStartupInfo()

        addr := fmt.Sprintf("%s:%d", config.AppConfig.Host, config.AppConfig.Port)
        log.Printf("Server starting on http://%s", addr)

        if err := app.Listen(addr); err != nil {
                log.Fatalf("Failed to start server: %v", err)
        }
}

func printBanner() {
        banner := `
====================================================
   PERFORMA - Backend Infrastructure Service
====================================================
   Handles: Resources, Models, Findings, WebSocket
   Proxies: Config, Agents, Mission to Brain Service
====================================================
`
        fmt.Println(banner)
}

func printStartupInfo() {
        fmt.Println("Performa Backend Infrastructure Starting...")
        fmt.Printf("Log Directory: %s\n", config.AppConfig.LogDir)
        fmt.Printf("Findings Directory: %s\n", config.AppConfig.FindingsDir)

        if config.AppConfig.OpenRouterAPIKey != "" && config.AppConfig.OpenRouterAPIKey != "your_key" {
                fmt.Println("OpenRouter API Key: Configured")
        } else {
                fmt.Println("OpenRouter API Key: Not configured (simulation mode)")
        }

        if config.AppConfig.AnthropicAPIKey != "" {
                fmt.Println("Anthropic API Key: Configured")
        }

        if config.AppConfig.OpenAIAPIKey != "" {
                fmt.Println("OpenAI API Key: Configured")
        }

        fmt.Printf("Brain Service URL: %s\n", config.AppConfig.BrainServiceURL)
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
