"""Comprehensive list of allowed tools for autonomous agents"""

ALLOWED_TOOLS = {
    "network_recon": {"nmap", "rustscan", "masscan", "zmap", "naabu", "scapy", "hping3", "nping", "arp-scan", "netdiscover", "fping", "dnsrecon", "dnsenum", "dnsmap", "dnswalk", "altdns", "amass", "subfinder", "assetfinder", "findomain", "httprobe", "httpx", "waybackurls", "gau", "gospider", "katana", "dnsx", "massdns", "puredns", "shuffledns", "whois", "dig", "nslookup"},
    "web_scanning": {"nikto", "sqlmap", "dirb", "gobuster", "wfuzz", "ffuf", "aquatone", "eyewitness", "gowitness", "whatweb", "wappalyzer-cli", "cmseek", "cmsmap", "droopescan", "joomscan", "wpscan", "drupwn", "curl", "wget", "burpsuite", "zaproxy", "nuclei", "wafw00f"},
    "vuln_scanning": {"trivy", "grype", "snyk", "sonarqube", "clair", "anchore", "semgrep", "checkov", "terrascan", "tfsec", "openscap", "lynis"},
    "exploitation": {"metasploit", "msfvenom", "searchsploit", "hashcat", "john", "hydra", "medusa", "ncrack"},
    "cloud_security": {"aws-cli", "pacu", "prowler", "cloudmapper", "az", "gcloud", "gsutil", "checkov", "cloudsplaining"},
    "active_directory": {"crackmapexec", "impacket", "bloodhound", "sharphound", "pypykatz", "mimikatz", "secretsdump", "evil-winrm", "kerbrute"},
    "container": {"docker", "kubectl", "kubeadm", "kube-bench", "kube-hunter", "trivy", "cdk", "peirates"},
    "dev_tools": {"git", "python", "node", "java", "gcc", "make", "vim", "nano", "sed", "awk", "grep"},
    "system_info": {"uname", "whoami", "hostname", "ifconfig", "ip", "netstat", "ps", "top", "lsof", "id"},
    "database": {"sqlite3", "mysql", "postgresql", "mongosh", "redis-cli"},
    "forensics": {"volatility", "binwalk", "strings", "file", "exiftool", "sleuthkit", "autopsy"},
    "wireless": {"aircrack-ng", "wireshark", "tcpdump", "kismet", "hashcat"},
    "reverse_engineering": {"ghidra", "objdump", "strings", "readelf", "radare2", "r2"},
    "malware_analysis": {"cuckoo", "yara", "strings", "volatility", "wireshark"},
    "osint": {"recon-ng", "theHarvester", "shodan", "censys", "whois"},
    "payloads": {"msfvenom", "donut", "weevely", "netcat", "nc"},
    "api_security": {"postman", "burpsuite", "zaproxy", "owasp-zap"},
}

ALL_ALLOWED_TOOLS = set()
for tools in ALLOWED_TOOLS.values():
    ALL_ALLOWED_TOOLS.update(tools)

def is_tool_allowed(cmd: str) -> bool:
    tool = cmd.split()[0] if cmd else ""
    if tool.startswith("RUN "):
        tool = tool[4:].split()[0]
    return tool.lower() in ALL_ALLOWED_TOOLS

def is_dangerous_command(cmd: str) -> bool:
    dangerous = {"rm -rf", "mkfs", "chmod 777", "reboot", "shutdown", "halt", ":(){:|:&};:"}
    return any(pattern.lower() in cmd.lower() for pattern in dangerous)

def get_allowed_tools_by_category() -> dict:
    return ALLOWED_TOOLS

def get_tool_category(tool: str) -> str:
    for cat, tools in ALLOWED_TOOLS.items():
        if tool.lower() in tools:
            return cat
    return "unknown"
