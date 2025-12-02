package brain

import (
        "bytes"
        "encoding/json"
        "fmt"
        "io"
        "net/http"
        "time"
)

type BrainClient struct {
        baseURL    string
        httpClient *http.Client
}

type ThinkRequest struct {
        Task        string                 `json:"task"`
        Context     map[string]interface{} `json:"context,omitempty"`
        Constraints []string               `json:"constraints,omitempty"`
        History     []map[string]interface{} `json:"history,omitempty"`
}

type ThinkResponse struct {
        ID                 string                   `json:"id"`
        Timestamp          string                   `json:"timestamp"`
        InputTask          string                   `json:"input_task"`
        Analysis           map[string]interface{}   `json:"analysis"`
        Decision           map[string]interface{}   `json:"decision"`
        Confidence         float64                  `json:"confidence"`
        RecommendedActions []interface{}            `json:"recommended_actions"`
        Reasoning          string                   `json:"reasoning"`
}

type ClassifyRequest struct {
        Description       string                 `json:"description"`
        Type              string                 `json:"type,omitempty"`
        AdditionalContext map[string]interface{} `json:"additional_context,omitempty"`
}

type ClassifyResponse struct {
        PredictedSeverity string                 `json:"predicted_severity"`
        Confidence        float64                `json:"confidence"`
        SeverityScores    map[string]float64     `json:"severity_scores"`
        VulnerabilityType string                 `json:"vulnerability_type"`
        ModelUsed         string                 `json:"model_used"`
}

type EvaluateRequest struct {
        Action  map[string]interface{} `json:"action"`
        Context map[string]interface{} `json:"context"`
}

type EvaluateResponse struct {
        Action          string  `json:"action"`
        ShouldExecute   bool    `json:"should_execute"`
        Score           float64 `json:"score"`
        RiskLevel       float64 `json:"risk_level"`
        RewardPotential float64 `json:"reward_potential"`
        Feasibility     float64 `json:"feasibility"`
        Reasoning       string  `json:"reasoning"`
}

type StrategyRequest struct {
        Target map[string]interface{} `json:"target"`
        Mode   string                 `json:"mode,omitempty"`
}

type StrategyResponse struct {
        Name                   string                   `json:"name"`
        Mode                   string                   `json:"mode"`
        Target                 map[string]interface{}   `json:"target"`
        Phases                 []map[string]interface{} `json:"phases"`
        NoiseLevel             string                   `json:"noise_level"`
        TimingMultiplier       float64                  `json:"timing_multiplier"`
        TotalEstimatedDuration int                      `json:"total_estimated_duration"`
        CreatedAt              string                   `json:"created_at"`
}

type BrainStatus struct {
        Active               bool                     `json:"active"`
        ModelsLoaded         []map[string]interface{} `json:"models_loaded"`
        ThinkingHistoryCount int                      `json:"thinking_history_count"`
        ContextSize          int                      `json:"context_size"`
}

func NewBrainClient(brainURL string) *BrainClient {
        client := &BrainClient{
                baseURL: brainURL,
                httpClient: &http.Client{
                        Timeout: 30 * time.Second,
                },
        }
        return client
}

func (c *BrainClient) WaitForHealthy(maxRetries int, retryDelay time.Duration) error {
        for i := 0; i < maxRetries; i++ {
                _, err := c.Health()
                if err == nil {
                        return nil
                }
                time.Sleep(retryDelay)
        }
        return fmt.Errorf("brain service not healthy after %d retries", maxRetries)
}

func (c *BrainClient) IsHealthy() bool {
        _, err := c.Health()
        return err == nil
}

func (c *BrainClient) doRequest(method, endpoint string, body interface{}, result interface{}) error {
        var reqBody io.Reader
        if body != nil {
                jsonData, err := json.Marshal(body)
                if err != nil {
                        return fmt.Errorf("failed to marshal request: %w", err)
                }
                reqBody = bytes.NewBuffer(jsonData)
        }

        req, err := http.NewRequest(method, c.baseURL+endpoint, reqBody)
        if err != nil {
                return fmt.Errorf("failed to create request: %w", err)
        }

        req.Header.Set("Content-Type", "application/json")

        resp, err := c.httpClient.Do(req)
        if err != nil {
                return fmt.Errorf("request failed: %w", err)
        }
        defer resp.Body.Close()

        if resp.StatusCode >= 400 {
                bodyBytes, _ := io.ReadAll(resp.Body)
                return fmt.Errorf("request failed with status %d: %s", resp.StatusCode, string(bodyBytes))
        }

        if result != nil {
                if err := json.NewDecoder(resp.Body).Decode(result); err != nil {
                        return fmt.Errorf("failed to decode response: %w", err)
                }
        }

        return nil
}

func (c *BrainClient) Health() (map[string]string, error) {
        var result map[string]string
        err := c.doRequest("GET", "/brain/health", nil, &result)
        return result, err
}

func (c *BrainClient) GetStatus() (*BrainStatus, error) {
        var result BrainStatus
        err := c.doRequest("GET", "/brain/status", nil, &result)
        return &result, err
}

func (c *BrainClient) Initialize() (map[string]interface{}, error) {
        var result map[string]interface{}
        err := c.doRequest("POST", "/brain/initialize", nil, &result)
        return result, err
}

func (c *BrainClient) Think(req *ThinkRequest) (*ThinkResponse, error) {
        var result ThinkResponse
        err := c.doRequest("POST", "/brain/think", req, &result)
        return &result, err
}

func (c *BrainClient) ClassifyThreat(req *ClassifyRequest) (*ClassifyResponse, error) {
        var result ClassifyResponse
        err := c.doRequest("POST", "/brain/classify", req, &result)
        return &result, err
}

func (c *BrainClient) EvaluateAction(req *EvaluateRequest) (*EvaluateResponse, error) {
        var result EvaluateResponse
        err := c.doRequest("POST", "/brain/evaluate", req, &result)
        return &result, err
}

func (c *BrainClient) GenerateStrategy(req *StrategyRequest) (*StrategyResponse, error) {
        var result StrategyResponse
        err := c.doRequest("POST", "/brain/strategy", req, &result)
        return &result, err
}

func (c *BrainClient) GetModels() ([]map[string]interface{}, error) {
        var result []map[string]interface{}
        err := c.doRequest("GET", "/brain/models", nil, &result)
        return result, err
}

func (c *BrainClient) Learn(action, outcome map[string]interface{}) error {
        req := map[string]interface{}{
                "action":  action,
                "outcome": outcome,
        }
        var result map[string]interface{}
        return c.doRequest("POST", "/brain/learn", req, &result)
}

func (c *BrainClient) Reset() error {
        var result map[string]interface{}
        return c.doRequest("POST", "/brain/reset", nil, &result)
}
