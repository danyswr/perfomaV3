package models

type AIModel struct {
	ID       string `json:"id"`
	Name     string `json:"name"`
	Provider string `json:"provider"`
	Context  int    `json:"context"`
	Pricing  string `json:"pricing"`
}

var AvailableModels = []AIModel{
	{ID: "anthropic/claude-3.5-sonnet", Name: "Claude 3.5 Sonnet", Provider: "Anthropic", Context: 200000, Pricing: "$3/$15"},
	{ID: "anthropic/claude-3-opus", Name: "Claude 3 Opus", Provider: "Anthropic", Context: 200000, Pricing: "$15/$75"},
	{ID: "anthropic/claude-3-haiku", Name: "Claude 3 Haiku", Provider: "Anthropic", Context: 200000, Pricing: "$0.25/$1.25"},
	{ID: "openai/gpt-4o", Name: "GPT-4o", Provider: "OpenAI", Context: 128000, Pricing: "$5/$15"},
	{ID: "openai/gpt-4o-mini", Name: "GPT-4o Mini", Provider: "OpenAI", Context: 128000, Pricing: "$0.15/$0.60"},
	{ID: "google/gemini-pro-1.5", Name: "Gemini Pro 1.5", Provider: "Google", Context: 2800000, Pricing: "$1.25/$5"},
	{ID: "meta-llama/llama-3.1-405b-instruct", Name: "Llama 3.1 405B", Provider: "Meta", Context: 131072, Pricing: "$3/$3"},
	{ID: "meta-llama/llama-3.1-70b-instruct", Name: "Llama 3.1 70B", Provider: "Meta", Context: 131072, Pricing: "$0.52/$0.75"},
	{ID: "mistralai/mistral-large", Name: "Mistral Large", Provider: "Mistral", Context: 128000, Pricing: "$2/$6"},
	{ID: "deepseek/deepseek-chat", Name: "DeepSeek Chat", Provider: "DeepSeek", Context: 128000, Pricing: "$0.14/$0.28"},
}

type StartRequest struct {
	Target       string `json:"target"`
	Category     string `json:"category"`
	Model        string `json:"model"`
	AgentCount   int    `json:"agent_count"`
	Instructions string `json:"instructions"`
	Mode         string `json:"mode"`
	Tools        string `json:"tools"`
	Stealth      string `json:"stealth"`
	Caps         string `json:"caps"`
}

type ChatMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type ChatRequest struct {
	Messages []ChatMessage `json:"messages"`
	Model    string        `json:"model"`
	Stream   bool          `json:"stream"`
}
