package config

import (
        "os"
        "strconv"

        "github.com/joho/godotenv"
)

type Config struct {
        Host             string
        Port             int
        OpenRouterAPIKey string
        AnthropicAPIKey  string
        OpenAIAPIKey     string
        LogDir           string
        FindingsDir      string
        BrainServiceURL  string
}

var AppConfig *Config

func Load() {
        godotenv.Load()
        godotenv.Load("../.env")

        port, _ := strconv.Atoi(getEnv("PORT", "8000"))

        AppConfig = &Config{
                Host:             getEnv("HOST", "0.0.0.0"),
                Port:             port,
                OpenRouterAPIKey: getEnv("OPENROUTER_API_KEY", ""),
                AnthropicAPIKey:  getEnv("ANTHROPIC_API_KEY", ""),
                OpenAIAPIKey:     getEnv("OPENAI_API_KEY", ""),
                LogDir:           getEnv("LOG_DIR", "./logs"),
                FindingsDir:      getEnv("FINDINGS_DIR", "./findings"),
                BrainServiceURL:  getEnv("BRAIN_SERVICE_URL", "http://localhost:8001"),
        }
}

func getEnv(key, defaultValue string) string {
        if value := os.Getenv(key); value != "" {
                return value
        }
        return defaultValue
}
