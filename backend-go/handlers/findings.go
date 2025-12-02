package handlers

import (
        "os"
        "path/filepath"
        "performa-backend/config"
        "performa-backend/models"
        "strings"
        "time"

        "github.com/gofiber/fiber/v2"
)

func GetFindings(c *fiber.Ctx) error {
        findings := models.Findings.GetAllFindings()

        severitySummary := map[string]int{
                "critical": 0,
                "high":     0,
                "medium":   0,
                "low":      0,
                "info":     0,
        }

        for _, f := range findings {
                severitySummary[string(f.Severity)]++
        }

        return c.JSON(fiber.Map{
                "findings":         findings,
                "total":            len(findings),
                "severity_summary": severitySummary,
        })
}

func GetFindingsLogs(c *fiber.Ctx) error {
        logDir := config.AppConfig.LogDir
        logs := make([]map[string]interface{}, 0)

        files, err := os.ReadDir(logDir)
        if err != nil {
                return c.JSON(fiber.Map{
                        "logs":  []interface{}{},
                        "count": 0,
                })
        }

        for _, file := range files {
                if !file.IsDir() && strings.HasSuffix(file.Name(), ".log") {
                        info, _ := file.Info()
                        logs = append(logs, map[string]interface{}{
                                "name":     file.Name(),
                                "size":     info.Size(),
                                "modified": info.ModTime(),
                        })
                }
        }

        return c.JSON(fiber.Map{
                "logs":  logs,
                "count": len(logs),
        })
}

func GetFindingsExplorer(c *fiber.Ctx) error {
        findingsDir := config.AppConfig.FindingsDir
        rootFiles := make([]map[string]interface{}, 0)
        folders := make([]map[string]interface{}, 0)
        totalFiles := 0

        files, err := os.ReadDir(findingsDir)
        if err != nil {
                return c.JSON(fiber.Map{
                        "folders":      make([]interface{}, 0),
                        "root_files":   make([]interface{}, 0),
                        "total_files":  0,
                        "last_updated": time.Now().Format(time.RFC3339),
                })
        }

        for _, file := range files {
                info, _ := file.Info()
                if file.IsDir() {
                        subFiles := make([]map[string]interface{}, 0)
                        subPath := filepath.Join(findingsDir, file.Name())
                        subEntries, _ := os.ReadDir(subPath)
                        for _, subFile := range subEntries {
                                if !subFile.IsDir() {
                                        subInfo, _ := subFile.Info()
                                        subFiles = append(subFiles, map[string]interface{}{
                                                "name":     subFile.Name(),
                                                "path":     filepath.Join(subPath, subFile.Name()),
                                                "size":     subInfo.Size(),
                                                "modified": subInfo.ModTime().Format(time.RFC3339),
                                                "type":     strings.TrimPrefix(filepath.Ext(subFile.Name()), "."),
                                        })
                                        totalFiles++
                                }
                        }
                        folders = append(folders, map[string]interface{}{
                                "name":       file.Name(),
                                "path":       subPath,
                                "files":      subFiles,
                                "file_count": len(subFiles),
                        })
                } else {
                        rootFiles = append(rootFiles, map[string]interface{}{
                                "name":     file.Name(),
                                "path":     filepath.Join(findingsDir, file.Name()),
                                "size":     info.Size(),
                                "modified": info.ModTime().Format(time.RFC3339),
                                "type":     strings.TrimPrefix(filepath.Ext(file.Name()), "."),
                        })
                        totalFiles++
                }
        }

        return c.JSON(fiber.Map{
                "folders":      folders,
                "root_files":   rootFiles,
                "total_files":  totalFiles,
                "last_updated": time.Now().Format(time.RFC3339),
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
