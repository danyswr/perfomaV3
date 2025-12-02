package models

import (
	"sync"
	"time"

	"github.com/google/uuid"
)

type AgentStatus string

const (
	AgentStatusIdle     AgentStatus = "idle"
	AgentStatusRunning  AgentStatus = "running"
	AgentStatusPaused   AgentStatus = "paused"
	AgentStatusComplete AgentStatus = "complete"
	AgentStatusError    AgentStatus = "error"
)

type Agent struct {
	ID          string      `json:"id"`
	Name        string      `json:"name"`
	Role        string      `json:"role"`
	Status      AgentStatus `json:"status"`
	Target      string      `json:"target"`
	Model       string      `json:"model"`
	CreatedAt   time.Time   `json:"created_at"`
	UpdatedAt   time.Time   `json:"updated_at"`
	TaskCount   int         `json:"task_count"`
	Findings    int         `json:"findings"`
	CurrentTask string      `json:"current_task"`
}

type AgentMessage struct {
	ID        string    `json:"id"`
	AgentID   string    `json:"agent_id"`
	Role      string    `json:"role"`
	Content   string    `json:"content"`
	Timestamp time.Time `json:"timestamp"`
}

type AgentManager struct {
	agents   map[string]*Agent
	messages map[string][]AgentMessage
	mu       sync.RWMutex
}

var Manager = &AgentManager{
	agents:   make(map[string]*Agent),
	messages: make(map[string][]AgentMessage),
}

func (m *AgentManager) CreateAgent(name, role, target, model string) *Agent {
	m.mu.Lock()
	defer m.mu.Unlock()

	agent := &Agent{
		ID:        uuid.New().String(),
		Name:      name,
		Role:      role,
		Status:    AgentStatusIdle,
		Target:    target,
		Model:     model,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	m.agents[agent.ID] = agent
	m.messages[agent.ID] = []AgentMessage{}

	return agent
}

func (m *AgentManager) GetAgent(id string) *Agent {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.agents[id]
}

func (m *AgentManager) GetAllAgents() []*Agent {
	m.mu.RLock()
	defer m.mu.RUnlock()

	agents := make([]*Agent, 0, len(m.agents))
	for _, agent := range m.agents {
		agents = append(agents, agent)
	}
	return agents
}

func (m *AgentManager) DeleteAgent(id string) bool {
	m.mu.Lock()
	defer m.mu.Unlock()

	if _, exists := m.agents[id]; exists {
		delete(m.agents, id)
		delete(m.messages, id)
		return true
	}
	return false
}

func (m *AgentManager) PauseAgent(id string) bool {
	m.mu.Lock()
	defer m.mu.Unlock()

	if agent, exists := m.agents[id]; exists {
		if agent.Status == AgentStatusRunning {
			agent.Status = AgentStatusPaused
			agent.UpdatedAt = time.Now()
			return true
		}
	}
	return false
}

func (m *AgentManager) ResumeAgent(id string) bool {
	m.mu.Lock()
	defer m.mu.Unlock()

	if agent, exists := m.agents[id]; exists {
		if agent.Status == AgentStatusPaused {
			agent.Status = AgentStatusRunning
			agent.UpdatedAt = time.Now()
			return true
		}
	}
	return false
}

func (m *AgentManager) UpdateAgentStatus(id string, status AgentStatus) bool {
	m.mu.Lock()
	defer m.mu.Unlock()

	if agent, exists := m.agents[id]; exists {
		agent.Status = status
		agent.UpdatedAt = time.Now()
		return true
	}
	return false
}

func (m *AgentManager) AddMessage(agentID string, role, content string) {
	m.mu.Lock()
	defer m.mu.Unlock()

	if _, exists := m.messages[agentID]; exists {
		msg := AgentMessage{
			ID:        uuid.New().String(),
			AgentID:   agentID,
			Role:      role,
			Content:   content,
			Timestamp: time.Now(),
		}
		m.messages[agentID] = append(m.messages[agentID], msg)
	}
}

func (m *AgentManager) GetMessages(agentID string) []AgentMessage {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.messages[agentID]
}
