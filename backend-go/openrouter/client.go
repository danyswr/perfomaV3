package openrouter

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"performa-backend/config"
)

const BaseURL = "https://openrouter.ai/api/v1"

type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type ChatRequest struct {
	Model    string    `json:"model"`
	Messages []Message `json:"messages"`
}

type ChatResponse struct {
	ID      string `json:"id"`
	Choices []struct {
		Message struct {
			Role    string `json:"role"`
			Content string `json:"content"`
		} `json:"message"`
	} `json:"choices"`
	Error *struct {
		Message string `json:"message"`
	} `json:"error,omitempty"`
}

func Chat(messages []Message, model string) (string, error) {
	if config.AppConfig.OpenRouterAPIKey == "" || config.AppConfig.OpenRouterAPIKey == "your_key" {
		return simulateResponse(messages, model), nil
	}

	reqBody := ChatRequest{
		Model:    model,
		Messages: messages,
	}

	jsonBody, err := json.Marshal(reqBody)
	if err != nil {
		return "", fmt.Errorf("failed to marshal request: %w", err)
	}

	req, err := http.NewRequest("POST", BaseURL+"/chat/completions", bytes.NewBuffer(jsonBody))
	if err != nil {
		return "", fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+config.AppConfig.OpenRouterAPIKey)
	req.Header.Set("HTTP-Referer", "https://performa.ai")
	req.Header.Set("X-Title", "Performa AI Agent")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("failed to read response: %w", err)
	}

	var chatResp ChatResponse
	if err := json.Unmarshal(body, &chatResp); err != nil {
		return "", fmt.Errorf("failed to parse response: %w", err)
	}

	if chatResp.Error != nil {
		return "", fmt.Errorf("API error: %s", chatResp.Error.Message)
	}

	if len(chatResp.Choices) == 0 {
		return "", fmt.Errorf("no response from model")
	}

	return chatResp.Choices[0].Message.Content, nil
}

func simulateResponse(messages []Message, model string) string {
	return fmt.Sprintf(`## Security Analysis Report

**Model:** %s
**Status:** Simulation Mode (No API Key)

### Summary
This is a simulated response. To get real AI-powered security analysis, please configure your OpenRouter API key.

### Recommendations
1. Set up your OPENROUTER_API_KEY in the environment variables
2. Restart the application
3. Run the security scan again

### Note
The system is functioning correctly. This simulation demonstrates the expected output format.
`, model)
}
