package tools

var AllowedTools = map[string][]string{
	"network_recon": {
		"nmap", "rustscan", "masscan", "naabu", "dnsrecon", "dnsenum",
		"amass", "subfinder", "httpx", "whois", "dig", "nslookup",
		"fping", "arp-scan", "netdiscover", "dnsx", "massdns",
	},
	"web_scanning": {
		"nikto", "sqlmap", "gobuster", "ffuf", "nuclei", "whatweb",
		"wpscan", "curl", "wget", "dirb", "wfuzz", "wafw00f",
	},
	"vuln_scanning": {
		"trivy", "grype", "semgrep", "lynis", "openscap", "snyk",
	},
	"exploitation": {
		"metasploit", "msfvenom", "searchsploit", "hashcat", "john",
		"hydra", "medusa", "ncrack",
	},
	"cloud_security": {
		"aws-cli", "pacu", "prowler", "az", "gcloud", "checkov",
	},
	"container": {
		"docker", "kubectl", "kube-bench", "kube-hunter", "trivy",
	},
	"osint": {
		"recon-ng", "theHarvester", "shodan", "censys", "maltego",
	},
	"system_info": {
		"uname", "whoami", "hostname", "ifconfig", "ip", "netstat", "ps",
		"top", "lsof", "id", "cat", "ls", "find", "grep",
	},
	"database": {
		"sqlite3", "mysql", "psql", "mongosh", "redis-cli",
	},
	"forensics": {
		"volatility", "binwalk", "strings", "file", "exiftool",
	},
	"wireless": {
		"aircrack-ng", "wireshark", "tcpdump", "kismet",
	},
	"api_security": {
		"postman", "burpsuite", "zaproxy", "owasp-zap",
	},
}

var DangerousCommands = []string{
	"rm -rf", "mkfs", "chmod 777", ":(){:|:&};:",
	"reboot", "shutdown", "halt", "dd if=/dev/zero",
}

func GetAllAllowedTools() []string {
	var all []string
	for _, tools := range AllowedTools {
		all = append(all, tools...)
	}
	return all
}

func IsToolAllowed(tool string, requestedTools []string, allowedToolsOnly bool) bool {
	if !allowedToolsOnly || len(requestedTools) == 0 {
		return isInAllowedTools(tool)
	}
	
	for _, t := range requestedTools {
		if t == tool {
			return true
		}
	}
	return false
}

func isInAllowedTools(tool string) bool {
	for _, tools := range AllowedTools {
		for _, t := range tools {
			if t == tool {
				return true
			}
		}
	}
	return false
}

func IsDangerousCommand(cmd string) bool {
	for _, dangerous := range DangerousCommands {
		if contains(cmd, dangerous) {
			return true
		}
	}
	return false
}

func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(s) > 0 && containsSubstring(s, substr))
}

func containsSubstring(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}

func GetToolCategory(tool string) string {
	for category, tools := range AllowedTools {
		for _, t := range tools {
			if t == tool {
				return category
			}
		}
	}
	return "unknown"
}

func FilterToolsByCategory(category string) []string {
	if tools, exists := AllowedTools[category]; exists {
		return tools
	}
	return []string{}
}
