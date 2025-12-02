package handlers

import (
        "time"

        "github.com/gofiber/fiber/v2"
        "github.com/shirou/gopsutil/v3/cpu"
        "github.com/shirou/gopsutil/v3/disk"
        "github.com/shirou/gopsutil/v3/mem"
        "github.com/shirou/gopsutil/v3/net"
)

type ResourceStats struct {
        CPU       float64 `json:"cpu"`
        Memory    float64 `json:"memory"`
        Disk      float64 `json:"disk"`
        Network   float64 `json:"network"`
        Timestamp string  `json:"timestamp"`
}

func GetResources(c *fiber.Ctx) error {
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

        return c.JSON(ResourceStats{
                CPU:       cpuUsage,
                Memory:    memUsage,
                Disk:      diskUsage,
                Network:   networkUsage,
                Timestamp: time.Now().Format(time.RFC3339),
        })
}
