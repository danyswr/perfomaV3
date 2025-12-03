package database

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"time"

	_ "github.com/lib/pq"
)

var DB *sql.DB

type SavedConfig struct {
	ID                string          `json:"id"`
	Name              string          `json:"name"`
	Target            string          `json:"target"`
	Category          string          `json:"category"`
	CustomInstruction string          `json:"custom_instruction"`
	StealthMode       bool            `json:"stealth_mode"`
	AggressiveLevel   int             `json:"aggressive_level"`
	ModelName         string          `json:"model_name"`
	NumAgents         int             `json:"num_agents"`
	ExecutionDuration *int            `json:"execution_duration"`
	RequestedTools    json.RawMessage `json:"requested_tools"`
	AllowedToolsOnly  bool            `json:"allowed_tools_only"`
	StealthOptions    json.RawMessage `json:"stealth_options"`
	Capabilities      json.RawMessage `json:"capabilities"`
	CreatedAt         time.Time       `json:"created_at"`
	UpdatedAt         time.Time       `json:"updated_at"`
}

type SavedSession struct {
	ID        string          `json:"id"`
	Name      string          `json:"name"`
	Config    json.RawMessage `json:"config"`
	Agents    json.RawMessage `json:"agents"`
	Findings  json.RawMessage `json:"findings"`
	CreatedAt time.Time       `json:"created_at"`
	UpdatedAt time.Time       `json:"updated_at"`
}

func Init() error {
	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		log.Println("DATABASE_URL not set, using in-memory storage")
		return nil
	}

	var err error
	DB, err = sql.Open("postgres", dbURL)
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}

	if err = DB.Ping(); err != nil {
		return fmt.Errorf("failed to ping database: %w", err)
	}

	if err = createTables(); err != nil {
		return fmt.Errorf("failed to create tables: %w", err)
	}

	log.Println("Database connected successfully")
	return nil
}

func createTables() error {
	queries := []string{
		`CREATE TABLE IF NOT EXISTS configs (
			id VARCHAR(255) PRIMARY KEY,
			name VARCHAR(255) NOT NULL,
			target VARCHAR(500),
			category VARCHAR(100),
			custom_instruction TEXT,
			stealth_mode BOOLEAN DEFAULT false,
			aggressive_level INTEGER DEFAULT 1,
			model_name VARCHAR(255),
			num_agents INTEGER DEFAULT 3,
			execution_duration INTEGER,
			requested_tools JSONB DEFAULT '[]',
			allowed_tools_only BOOLEAN DEFAULT false,
			stealth_options JSONB DEFAULT '{}',
			capabilities JSONB DEFAULT '{}',
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)`,
		`CREATE TABLE IF NOT EXISTS sessions (
			id VARCHAR(255) PRIMARY KEY,
			name VARCHAR(255) NOT NULL,
			config JSONB,
			agents JSONB DEFAULT '[]',
			findings JSONB DEFAULT '[]',
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)`,
		`CREATE TABLE IF NOT EXISTS findings (
			id VARCHAR(255) PRIMARY KEY,
			session_id VARCHAR(255),
			agent_id VARCHAR(255),
			title VARCHAR(500) NOT NULL,
			description TEXT,
			severity VARCHAR(50),
			category VARCHAR(100),
			target VARCHAR(500),
			evidence TEXT,
			remediation TEXT,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
		)`,
	}

	for _, query := range queries {
		if _, err := DB.Exec(query); err != nil {
			return err
		}
	}

	return nil
}

func SaveConfig(config SavedConfig) error {
	if DB == nil {
		return nil
	}

	query := `
		INSERT INTO configs (id, name, target, category, custom_instruction, stealth_mode, 
			aggressive_level, model_name, num_agents, execution_duration, requested_tools,
			allowed_tools_only, stealth_options, capabilities, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
		ON CONFLICT (id) DO UPDATE SET
			name = EXCLUDED.name,
			target = EXCLUDED.target,
			category = EXCLUDED.category,
			custom_instruction = EXCLUDED.custom_instruction,
			stealth_mode = EXCLUDED.stealth_mode,
			aggressive_level = EXCLUDED.aggressive_level,
			model_name = EXCLUDED.model_name,
			num_agents = EXCLUDED.num_agents,
			execution_duration = EXCLUDED.execution_duration,
			requested_tools = EXCLUDED.requested_tools,
			allowed_tools_only = EXCLUDED.allowed_tools_only,
			stealth_options = EXCLUDED.stealth_options,
			capabilities = EXCLUDED.capabilities,
			updated_at = EXCLUDED.updated_at
	`

	_, err := DB.Exec(query, config.ID, config.Name, config.Target, config.Category,
		config.CustomInstruction, config.StealthMode, config.AggressiveLevel, config.ModelName,
		config.NumAgents, config.ExecutionDuration, config.RequestedTools, config.AllowedToolsOnly,
		config.StealthOptions, config.Capabilities, config.CreatedAt, config.UpdatedAt)

	return err
}

func GetConfig(id string) (*SavedConfig, error) {
	if DB == nil {
		return nil, fmt.Errorf("database not initialized")
	}

	query := `SELECT id, name, target, category, custom_instruction, stealth_mode,
		aggressive_level, model_name, num_agents, execution_duration, requested_tools,
		allowed_tools_only, stealth_options, capabilities, created_at, updated_at
		FROM configs WHERE id = $1`

	var config SavedConfig
	err := DB.QueryRow(query, id).Scan(&config.ID, &config.Name, &config.Target, &config.Category,
		&config.CustomInstruction, &config.StealthMode, &config.AggressiveLevel, &config.ModelName,
		&config.NumAgents, &config.ExecutionDuration, &config.RequestedTools, &config.AllowedToolsOnly,
		&config.StealthOptions, &config.Capabilities, &config.CreatedAt, &config.UpdatedAt)

	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}

	return &config, nil
}

func GetAllConfigs() ([]SavedConfig, error) {
	if DB == nil {
		return []SavedConfig{}, nil
	}

	query := `SELECT id, name, target, category, custom_instruction, stealth_mode,
		aggressive_level, model_name, num_agents, execution_duration, requested_tools,
		allowed_tools_only, stealth_options, capabilities, created_at, updated_at
		FROM configs ORDER BY updated_at DESC`

	rows, err := DB.Query(query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var configs []SavedConfig
	for rows.Next() {
		var config SavedConfig
		err := rows.Scan(&config.ID, &config.Name, &config.Target, &config.Category,
			&config.CustomInstruction, &config.StealthMode, &config.AggressiveLevel, &config.ModelName,
			&config.NumAgents, &config.ExecutionDuration, &config.RequestedTools, &config.AllowedToolsOnly,
			&config.StealthOptions, &config.Capabilities, &config.CreatedAt, &config.UpdatedAt)
		if err != nil {
			return nil, err
		}
		configs = append(configs, config)
	}

	return configs, nil
}

func DeleteConfig(id string) error {
	if DB == nil {
		return nil
	}

	_, err := DB.Exec("DELETE FROM configs WHERE id = $1", id)
	return err
}

func SaveSession(session SavedSession) error {
	if DB == nil {
		return nil
	}

	query := `
		INSERT INTO sessions (id, name, config, agents, findings, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
		ON CONFLICT (id) DO UPDATE SET
			name = EXCLUDED.name,
			config = EXCLUDED.config,
			agents = EXCLUDED.agents,
			findings = EXCLUDED.findings,
			updated_at = EXCLUDED.updated_at
	`

	_, err := DB.Exec(query, session.ID, session.Name, session.Config, session.Agents,
		session.Findings, session.CreatedAt, session.UpdatedAt)

	return err
}

func GetSession(id string) (*SavedSession, error) {
	if DB == nil {
		return nil, fmt.Errorf("database not initialized")
	}

	query := `SELECT id, name, config, agents, findings, created_at, updated_at FROM sessions WHERE id = $1`

	var session SavedSession
	err := DB.QueryRow(query, id).Scan(&session.ID, &session.Name, &session.Config,
		&session.Agents, &session.Findings, &session.CreatedAt, &session.UpdatedAt)

	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}

	return &session, nil
}

func GetAllSessions() ([]SavedSession, error) {
	if DB == nil {
		return []SavedSession{}, nil
	}

	query := `SELECT id, name, config, agents, findings, created_at, updated_at FROM sessions ORDER BY updated_at DESC`

	rows, err := DB.Query(query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var sessions []SavedSession
	for rows.Next() {
		var session SavedSession
		err := rows.Scan(&session.ID, &session.Name, &session.Config, &session.Agents,
			&session.Findings, &session.CreatedAt, &session.UpdatedAt)
		if err != nil {
			return nil, err
		}
		sessions = append(sessions, session)
	}

	return sessions, nil
}

func DeleteSession(id string) error {
	if DB == nil {
		return nil
	}

	_, err := DB.Exec("DELETE FROM sessions WHERE id = $1", id)
	return err
}

func Close() {
	if DB != nil {
		DB.Close()
	}
}
