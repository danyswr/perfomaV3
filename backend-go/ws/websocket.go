package ws

import (
        "encoding/json"
        "log"
        "sync"

        "github.com/gofiber/fiber/v2"
        "github.com/gofiber/websocket/v2"
)

type Client struct {
        Conn *websocket.Conn
        ID   string
}

type WSMessage struct {
        Type    string      `json:"type"`
        Message string      `json:"message,omitempty"`
        Data    interface{} `json:"data,omitempty"`
        AgentID string      `json:"agent_id,omitempty"`
        Status  string      `json:"status,omitempty"`
        CPU     float64     `json:"cpu_usage,omitempty"`
        Memory  float64     `json:"memory_usage,omitempty"`
        Disk    float64     `json:"disk_usage,omitempty"`
        Network float64     `json:"network_usage,omitempty"`
}

type Hub struct {
        clients    map[*Client]bool
        broadcast  chan WSMessage
        register   chan *Client
        unregister chan *Client
        mu         sync.RWMutex
}

var MainHub = &Hub{
        clients:    make(map[*Client]bool),
        broadcast:  make(chan WSMessage, 256),
        register:   make(chan *Client),
        unregister: make(chan *Client),
}

func (h *Hub) Run() {
        for {
                select {
                case client := <-h.register:
                        h.mu.Lock()
                        h.clients[client] = true
                        h.mu.Unlock()
                        log.Printf("Client connected: %s", client.ID)

                case client := <-h.unregister:
                        h.mu.Lock()
                        if _, ok := h.clients[client]; ok {
                                delete(h.clients, client)
                                client.Conn.Close()
                        }
                        h.mu.Unlock()
                        log.Printf("Client disconnected: %s", client.ID)

                case message := <-h.broadcast:
                        h.mu.RLock()
                        data, _ := json.Marshal(message)
                        for client := range h.clients {
                                if err := client.Conn.WriteMessage(websocket.TextMessage, data); err != nil {
                                        log.Printf("Error sending message to client %s: %v", client.ID, err)
                                }
                        }
                        h.mu.RUnlock()
                }
        }
}

func BroadcastMessage(msgType string, content string) {
        MainHub.broadcast <- WSMessage{
                Type:    msgType,
                Message: content,
        }
}

func BroadcastAgentUpdate(agentID string, status string, message string) {
        MainHub.broadcast <- WSMessage{
                Type:    "agent_update",
                AgentID: agentID,
                Status:  status,
                Message: message,
        }
}

func BroadcastResources(cpu, memory, disk, network float64) {
        MainHub.broadcast <- WSMessage{
                Type:    "resources",
                CPU:     cpu,
                Memory:  memory,
                Disk:    disk,
                Network: network,
        }
}

func WebSocketUpgrade(c *fiber.Ctx) error {
        if websocket.IsWebSocketUpgrade(c) {
                return c.Next()
        }
        return fiber.ErrUpgradeRequired
}

func HandleWebSocket(c *websocket.Conn) {
        client := &Client{
                Conn: c,
                ID:   c.Query("id", "anonymous"),
        }

        MainHub.register <- client

        defer func() {
                MainHub.unregister <- client
        }()

        BroadcastMessage("system", "Client connected")

        for {
                _, msg, err := c.ReadMessage()
                if err != nil {
                        break
                }

                var wsMsg WSMessage
                if err := json.Unmarshal(msg, &wsMsg); err != nil {
                        continue
                }

                switch wsMsg.Type {
                case "ping":
                        c.WriteJSON(WSMessage{Type: "pong"})
                case "chat":
                        BroadcastMessage("chat", wsMsg.Message)
                case "get_updates":
                        c.WriteJSON(WSMessage{Type: "system", Message: "Updates sent"})
                }
        }
}
