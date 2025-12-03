package stealth

import (
	"crypto/md5"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"math/rand"
	"time"
)

type StealthOptions struct {
	ProxyChain    bool `json:"proxy_chain"`
	TorRouting    bool `json:"tor_routing"`
	MacSpoofing   bool `json:"mac_spoofing"`
	TimingJitter  bool `json:"timing_jitter"`
	UserAgentRot  bool `json:"user_agent_rotation"`
	HeaderRandom  bool `json:"header_randomization"`
	DNSOverHTTPS  bool `json:"dns_over_https"`
	TrafficPadding bool `json:"traffic_padding"`
}

type Capabilities struct {
	PacketInjection   bool `json:"packet_injection"`
	MITMAttacks       bool `json:"mitm_attacks"`
	WebSocketHijack   bool `json:"websocket_hijack"`
	SSLStripping      bool `json:"ssl_stripping"`
	DNSSpoof          bool `json:"dns_spoof"`
	ARPSpoof          bool `json:"arp_spoof"`
	SessionHijack     bool `json:"session_hijack"`
	CredentialCapture bool `json:"credential_capture"`
}

type BrowserProfile struct {
	Platform    string
	UserAgents  []string
	Resolutions [][2]int
	Languages   []string
}

type Fingerprint struct {
	SessionID         string  `json:"session_id"`
	UserAgent         string  `json:"user_agent"`
	ScreenWidth       int     `json:"screen_width"`
	ScreenHeight      int     `json:"screen_height"`
	ColorDepth        int     `json:"color_depth"`
	TimezoneOffset    int     `json:"timezone_offset"`
	Language          string  `json:"language"`
	Platform          string  `json:"platform"`
	HardwareConcurrency int   `json:"hardware_concurrency"`
	DeviceMemory      int     `json:"device_memory"`
	DoNotTrack        string  `json:"do_not_track"`
	MaxTouchPoints    int     `json:"max_touch_points"`
	PixelRatio        float64 `json:"pixel_ratio"`
	WebDriver         bool    `json:"webdriver"`
	CanvasHash        string  `json:"canvas_hash"`
	WebGLVendor       string  `json:"webgl_vendor"`
	WebGLRenderer     string  `json:"webgl_renderer"`
	AudioFingerprint  string  `json:"audio_fingerprint"`
}

var browserProfiles = []BrowserProfile{
	{
		Platform: "Win32",
		UserAgents: []string{
			"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
			"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
		},
		Resolutions: [][2]int{{1920, 1080}, {1366, 768}, {1600, 900}},
		Languages:   []string{"en-US", "en-GB", "de-DE"},
	},
	{
		Platform: "MacIntel",
		UserAgents: []string{
			"Mozilla/5.0 (Macintosh; Intel Mac OS X 13_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
			"Mozilla/5.0 (Macintosh; Intel Mac OS X 12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
		},
		Resolutions: [][2]int{{2560, 1440}, {1440, 900}},
		Languages:   []string{"en-US", "fr-FR", "es-ES"},
	},
	{
		Platform: "Linux x86_64",
		UserAgents: []string{
			"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
			"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
		},
		Resolutions: [][2]int{{1920, 1080}, {1280, 720}, {1600, 900}},
		Languages:   []string{"en-US", "de-DE", "en-CA"},
	},
}

var webglVendors = []string{"Google Inc.", "NVIDIA Corporation", "AMD", "Intel Inc."}
var webglRenderers = []string{
	"ANGLE (NVIDIA GeForce GTX 1050)",
	"Mesa Intel(R) UHD Graphics",
	"ANGLE (AMD Radeon RX 580)",
	"ANGLE (Intel(R) UHD Graphics 620)",
}

func init() {
	rand.Seed(time.Now().UnixNano())
}

func GenerateSessionID() string {
	data := fmt.Sprintf("%d%f", time.Now().UnixNano(), rand.Float64())
	hash := md5.Sum([]byte(data))
	return hex.EncodeToString(hash[:])
}

func GenerateFingerprint() Fingerprint {
	profile := browserProfiles[rand.Intn(len(browserProfiles))]
	resolution := profile.Resolutions[rand.Intn(len(profile.Resolutions))]
	
	timezoneOffsets := []int{-480, -420, -300, -240, 0, 60, 120, 480, 540}
	baseOffset := timezoneOffsets[rand.Intn(len(timezoneOffsets))]
	
	dntOptions := []string{"1", "0", ""}
	
	return Fingerprint{
		SessionID:         GenerateSessionID(),
		UserAgent:         profile.UserAgents[rand.Intn(len(profile.UserAgents))],
		ScreenWidth:       resolution[0],
		ScreenHeight:      resolution[1],
		ColorDepth:        []int{24, 30, 32}[rand.Intn(3)],
		TimezoneOffset:    baseOffset + rand.Intn(5) - 2,
		Language:          profile.Languages[rand.Intn(len(profile.Languages))],
		Platform:          profile.Platform,
		HardwareConcurrency: []int{2, 4, 8, 12, 16}[rand.Intn(5)],
		DeviceMemory:      []int{4, 8, 16, 32}[rand.Intn(4)],
		DoNotTrack:        dntOptions[rand.Intn(len(dntOptions))],
		MaxTouchPoints:    []int{0, 1, 5}[rand.Intn(3)],
		PixelRatio:        []float64{1, 1.25, 1.5, 2, 3}[rand.Intn(5)],
		WebDriver:         false,
		CanvasHash:        generateCanvasHash(),
		WebGLVendor:       webglVendors[rand.Intn(len(webglVendors))],
		WebGLRenderer:     webglRenderers[rand.Intn(len(webglRenderers))],
		AudioFingerprint:  generateAudioFingerprint(),
	}
}

func generateCanvasHash() string {
	data := fmt.Sprintf("%f%d", rand.Float64(), rand.Intn(999999))
	hash := sha256.Sum256([]byte(data))
	return hex.EncodeToString(hash[:])
}

func generateAudioFingerprint() string {
	data := fmt.Sprintf("%f-audio-context", rand.Float64())
	hash := md5.Sum([]byte(data))
	return hex.EncodeToString(hash[:])
}

func ApplyStealthHeaders(headers map[string]string, fp Fingerprint) map[string]string {
	result := make(map[string]string)
	for k, v := range headers {
		result[k] = v
	}
	
	result["User-Agent"] = fp.UserAgent
	result["Accept-Language"] = fp.Language
	if fp.DoNotTrack != "" {
		result["DNT"] = fp.DoNotTrack
	}
	
	return result
}

func GetTimingJitter(baseDelay int) int {
	jitter := rand.Intn(baseDelay/2) - baseDelay/4
	result := baseDelay + jitter
	if result < 100 {
		result = 100
	}
	return result
}

func DefaultStealthOptions() StealthOptions {
	return StealthOptions{
		ProxyChain:    false,
		TorRouting:    false,
		MacSpoofing:   false,
		TimingJitter:  true,
		UserAgentRot:  true,
		HeaderRandom:  true,
		DNSOverHTTPS:  false,
		TrafficPadding: false,
	}
}

func DefaultCapabilities() Capabilities {
	return Capabilities{
		PacketInjection:   false,
		MITMAttacks:       false,
		WebSocketHijack:   false,
		SSLStripping:      false,
		DNSSpoof:          false,
		ARPSpoof:          false,
		SessionHijack:     false,
		CredentialCapture: false,
	}
}
