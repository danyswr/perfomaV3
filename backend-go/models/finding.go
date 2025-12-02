package models

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sync"
	"time"

	"github.com/google/uuid"
)

type Severity string

const (
	SeverityCritical Severity = "critical"
	SeverityHigh     Severity = "high"
	SeverityMedium   Severity = "medium"
	SeverityLow      Severity = "low"
	SeverityInfo     Severity = "info"
)

type Finding struct {
	ID          string    `json:"id"`
	Title       string    `json:"title"`
	Description string    `json:"description"`
	Severity    Severity  `json:"severity"`
	Category    string    `json:"category"`
	Target      string    `json:"target"`
	Evidence    string    `json:"evidence"`
	AgentID     string    `json:"agent_id"`
	CreatedAt   time.Time `json:"created_at"`
	Status      string    `json:"status"`
}

type FindingsManager struct {
	findings    map[string]*Finding
	findingsDir string
	mu          sync.RWMutex
}

var Findings = &FindingsManager{
	findings:    make(map[string]*Finding),
	findingsDir: "./findings",
}

func (f *FindingsManager) SetFindingsDir(dir string) {
	f.findingsDir = dir
	os.MkdirAll(dir, 0755)
}

func (f *FindingsManager) AddFinding(title, description string, severity Severity, category, target, evidence, agentID string) *Finding {
	f.mu.Lock()
	defer f.mu.Unlock()

	finding := &Finding{
		ID:          uuid.New().String(),
		Title:       title,
		Description: description,
		Severity:    severity,
		Category:    category,
		Target:      target,
		Evidence:    evidence,
		AgentID:     agentID,
		CreatedAt:   time.Now(),
		Status:      "new",
	}

	f.findings[finding.ID] = finding
	f.saveFinding(finding)

	return finding
}

func (f *FindingsManager) GetAllFindings() []*Finding {
	f.mu.RLock()
	defer f.mu.RUnlock()

	findings := make([]*Finding, 0, len(f.findings))
	for _, finding := range f.findings {
		findings = append(findings, finding)
	}
	return findings
}

func (f *FindingsManager) GetFinding(id string) *Finding {
	f.mu.RLock()
	defer f.mu.RUnlock()
	return f.findings[id]
}

func (f *FindingsManager) saveFinding(finding *Finding) {
	data, _ := json.MarshalIndent(finding, "", "  ")
	filename := filepath.Join(f.findingsDir, finding.ID+".json")
	os.WriteFile(filename, data, 0644)
}

func (f *FindingsManager) LoadFindings() {
	files, err := filepath.Glob(filepath.Join(f.findingsDir, "*.json"))
	if err != nil {
		return
	}

	for _, file := range files {
		data, err := os.ReadFile(file)
		if err != nil {
			continue
		}

		var finding Finding
		if err := json.Unmarshal(data, &finding); err == nil {
			f.mu.Lock()
			f.findings[finding.ID] = &finding
			f.mu.Unlock()
		}
	}
}
