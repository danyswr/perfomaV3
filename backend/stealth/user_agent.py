import random
import re
import time
import hashlib
import math
import uuid
import json
from typing import List, Dict, Optional, Tuple, Any

class UserAgentRotator:
    """
    Advanced Stealth Identity Engine.
    Features:
    - Browser Fingerprinting & Canvas Spoofing Simulation
    - Per-device Profile Persistence
    - Context-Aware User-Agent Selection
    - Header Mutation (Browser-specific ordering)
    - Browser Version Drift Engine
    - TLS Fingerprint (JA3) Randomizer
    - Behavioral Timing Jitter
    """
    
    # Comprehensive user agent database (Base templates)
    USER_AGENTS = {
        "chrome_windows": [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36",
        ],
        "firefox_windows": [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{version}.0) Gecko/20100101 Firefox/{version}.0",
        ],
        "chrome_mac": [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36",
        ],
        "safari_mac": [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        ],
        "chrome_linux": [
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36",
        ],
        "mobile_android": [
            "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Mobile Safari/537.36",
        ],
        "mobile_ios": [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        ]
    }
    
    # Header ordering profiles (Crucial for avoiding passive fingerprinting)
    HEADER_ORDERS = {
        "chrome": ["Host", "Connection", "sec-ch-ua", "sec-ch-ua-mobile", "sec-ch-ua-platform", "Upgrade-Insecure-Requests", "User-Agent", "Accept", "Sec-Fetch-Site", "Sec-Fetch-Mode", "Sec-Fetch-User", "Sec-Fetch-Dest", "Accept-Encoding", "Accept-Language"],
        "firefox": ["Host", "User-Agent", "Accept", "Accept-Language", "Accept-Encoding", "Connection", "Upgrade-Insecure-Requests", "Sec-Fetch-Dest", "Sec-Fetch-Mode", "Sec-Fetch-Site", "Priority"],
        "safari": ["Host", "Accept", "Sec-Fetch-Site", "Accept-Language", "Sec-Fetch-Mode", "Accept-Encoding", "User-Agent", "Connection"]
    }

    def __init__(self, strategy: str = "context_aware", persistence_enabled: bool = True):
        """
        Initialize the Stealth Engine.
        
        Args:
            strategy: 'random', 'weighted', 'sequential', or 'context_aware'
            persistence_enabled: If True, remembers profile per session_id
        """
        self.strategy = strategy
        self.persistence_enabled = persistence_enabled
        self.current_index = 0
        
        # Persistence Memory (Session ID -> Profile Dict)
        self.profile_memory: Dict[str, Dict] = {}
        
        # Version Drift Config (Simulate real-world adoption)
        self.chrome_version_base = 120
        self.firefox_version_base = 121
        
        self.all_agents = self._flatten_agents()

    def _flatten_agents(self) -> List[str]:
        """Flatten and pre-drift agents"""
        agents = []
        for category, templates in self.USER_AGENTS.items():
            for tmpl in templates:
                # Initial static generation
                ver = self.chrome_version_base if "chrome" in category or "android" in category else self.firefox_version_base
                agents.append(tmpl.format(version=ver))
        return agents

    def _apply_version_drift(self, ua_template: str) -> str:
        """
        Browser Version Drift Engine.
        Automatically updates version numbers based on probability to mimic
        real-world update cycles (e.g., Chrome 120 -> 121 -> 122).
        """
        # 20% chance to drift version up by 1-3 major versions
        drift = 0
        if random.random() < 0.2:
            drift = random.randint(1, 3)
            
        if "Chrome" in ua_template:
            ver = self.chrome_version_base + drift
            # Add micro-version drift (e.g., .123.45)
            micro = f"{random.randint(0, 50)}.{random.randint(0, 200)}"
            return ua_template.format(version=ver).replace(".0.0.0", f".0.{micro}")
            
        elif "Firefox" in ua_template:
            ver = self.firefox_version_base + drift
            return ua_template.format(version=ver)
            
        return ua_template.format(version="17.0") # Fallback

    def _generate_device_fingerprint(self, ua: str) -> Dict[str, Any]:
        """
        Generates a consistent hardware fingerprint based on the User-Agent platform.
        """
        # 1. Hardware Concurrency (Cores)
        cores = 4
        if "Macintosh" in ua or "Win64" in ua:
            cores = random.choice([4, 8, 12, 16])
        elif "Android" in ua or "iPhone" in ua:
            cores = random.choice([4, 6, 8])
            
        # 2. Memory (RAM)
        ram = 8
        if cores >= 8:
            ram = random.choice([16, 32])
        elif "Android" in ua:
            ram = random.choice([4, 6, 8, 12])
            
        # 3. Screen Resolution
        screen = "1920x1080"
        if "Macintosh" in ua:
            screen = random.choice(["2560x1600", "2880x1800"])
        elif "Android" in ua:
            screen = random.choice(["1080x2400", "1440x3088"])
            
        # 4. Canvas Noise (Anti-Fingerprinting Spoof)
        # We generate a unique seed that stays consistent for this session
        canvas_seed = hashlib.md5(f"{ua}-{cores}-{ram}".encode()).hexdigest()[:10]
        
        return {
            "hardwareConcurrency": cores,
            "deviceMemory": ram,
            "screenResolution": screen,
            "canvasSeed": canvas_seed,
            "webglRenderer": "Intel Iris OpenGL Engine" if "Macintosh" in ua else "Direct3D11 vs_5_0 ps_5_0",
            "platform": "MacIntel" if "Macintosh" in ua else ("Win32" if "Windows" in ua else "Linux armv81")
        }

    def _get_geo_context(self, region: str = "US") -> Dict[str, str]:
        """
        Geo-Distributed Identity Layer.
        Returns locale and timezone matching the proxy region.
        """
        regions = {
            "US": {"locale": "en-US", "timezone": "America/New_York"},
            "UK": {"locale": "en-GB", "timezone": "Europe/London"},
            "ID": {"locale": "id-ID", "timezone": "Asia/Jakarta"},
            "DE": {"locale": "de-DE", "timezone": "Europe/Berlin"},
        }
        return regions.get(region, regions["US"])

    def _calculate_ml_stealth_score(self, ua: str, fingerprint: Dict) -> float:
        """
        Machine Learning Pattern Scoring (Simplified).
        Calculates probability of detection based on consistency.
        """
        score = 1.0
        # Penalty for mismatches
        if "Macintosh" in ua and fingerprint['platform'] != "MacIntel":
            score -= 0.5
        if "Windows" in ua and fingerprint['hardwareConcurrency'] < 2:
            score -= 0.3
        
        # Reward for common configs
        if "Chrome" in ua and "Win64" in ua:
            score += 0.1
            
        return min(max(score, 0.0), 1.0)

    def get_session_profile(self, session_id: str = None, target_type: str = "desktop", region: str = "US") -> Dict:
        """
        Retrieves or creates a persistent session profile.
        This is the main entry point for obtaining a consistent identity.
        """
        if session_id and self.persistence_enabled and session_id in self.profile_memory:
            return self.profile_memory[session_id]
        
        # 1. Select UA Template
        ua = self.get_user_agent(target_type=target_type)
        
        # 2. Generate Hardware Fingerprint
        fp = self._generate_device_fingerprint(ua)
        
        # 3. Generate Geo Context
        geo = self._get_geo_context(region)
        
        # 4. Generate TLS Fingerprint (JA3 Simulation)
        tls = self.get_tls_fingerprint(ua)
        
        profile = {
            "user_agent": ua,
            "fingerprint": fp,
            "geo": geo,
            "tls": tls,
            "stealth_score": self._calculate_ml_stealth_score(ua, fp),
            "created_at": time.time()
        }
        
        if session_id and self.persistence_enabled:
            self.profile_memory[session_id] = profile
            
        return profile

    def get_user_agent(self, category: str = None, target_type: str = "desktop") -> str:
        """
        Context-Aware User-Agent Selection Engine.
        Selects UA based on target content type (mobile vs desktop).
        """
        selected_template = ""
        
        if category and category in self.USER_AGENTS:
            selected_template = random.choice(self.USER_AGENTS[category])
        else:
            # Context-Aware Selection
            if target_type == "mobile":
                cats = ["mobile_android", "mobile_ios"]
                # Weighted: Android is more common globally
                cat = random.choices(cats, weights=[0.7, 0.3])[0]
                selected_template = random.choice(self.USER_AGENTS[cat])
            else:
                cats = ["chrome_windows", "chrome_mac", "firefox_windows"]
                cat = random.choices(cats, weights=[0.6, 0.2, 0.2])[0]
                selected_template = random.choice(self.USER_AGENTS[cat])

        # Apply Version Drift
        return self._apply_version_drift(selected_template)

    def get_headers(self, profile: Dict = None, include_extra: bool = True) -> dict:
        """
        Header Mutation Framework.
        Returns headers ordered and capitalized exactly like the real browser.
        """
        if not profile:
            # Fallback to ephemeral profile
            profile = self.get_session_profile()
            
        ua = profile['user_agent']
        locale = profile['geo']['locale']
        
        # Determine Browser Family for ordering
        family = "chrome"
        if "Firefox" in ua: family = "firefox"
        elif "Safari" in ua and "Chrome" not in ua: family = "safari"
        
        # Base headers
        raw_headers = {
            "Host": "TARGET_HOST_PLACEHOLDER", # To be replaced by request lib
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": f"{locale},{locale.split('-')[0]};q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        # Browser Specific Headers
        if family == "chrome":
            # Client Hints (Crucial for modern Chrome)
            platform = '"Windows"' if "Windows" in ua else ('"macOS"' if "Mac" in ua else '"Android"')
            mobile = "?1" if "Mobile" in ua else "?0"
            raw_headers.update({
                "sec-ch-ua": f'"Not_A Brand";v="8", "Chromium";v="{self.chrome_version_base}", "Google Chrome";v="{self.chrome_version_base}"',
                "sec-ch-ua-mobile": mobile,
                "sec-ch-ua-platform": platform,
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1"
            })
        elif family == "firefox":
            raw_headers.update({
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Priority": "u=1"
            })

        # Feature: Header Mutation (Ordering)
        ordered_headers = {}
        order_list = self.HEADER_ORDERS.get(family, self.HEADER_ORDERS["chrome"])
        
        # Fill strictly in order
        for key in order_list:
            if key in raw_headers:
                ordered_headers[key] = raw_headers[key]
        
        # Append leftovers (if any)
        for key, val in raw_headers.items():
            if key not in ordered_headers:
                ordered_headers[key] = val
                
        # Remove Host placeholder if using requests/aiohttp (they add it auto)
        if "Host" in ordered_headers and ordered_headers["Host"] == "TARGET_HOST_PLACEHOLDER":
            del ordered_headers["Host"]
            
        return ordered_headers

    def get_tls_fingerprint(self, ua: str) -> Dict[str, Any]:
        """
        TLS Fingerprint Randomizer.
        Generates a JA3-compatible config structure.
        """
        # Modern Chrome Ciphers
        ciphers = [
            "TLS_AES_128_GCM_SHA256", "TLS_AES_256_GCM_SHA384", "TLS_CHACHA20_POLY1305_SHA256",
            "ECDHE-ECDSA-AES128-GCM-SHA256", "ECDHE-RSA-AES128-GCM-SHA256",
            "ECDHE-ECDSA-AES256-GCM-SHA384", "ECDHE-RSA-AES256-GCM-SHA384"
        ]
        
        if "Firefox" in ua:
            # Firefox typically has slightly different order or preferred curves
            random.shuffle(ciphers)
            
        return {
            "ja3_string_simulated": f"771,4865-4866-4867-49195-49199-49196-49200-52393-52392,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0",
            "ciphers": ciphers,
            "min_version": "TLSv1.2",
            "max_version": "TLSv1.3"
        }

    def simulate_behavior(self, behavior_type: str = "browsing"):
        """
        Behavioral Simulation Engine.
        Injects realistic delays:
        - Think Time: Pause between page loads.
        - Burst Pattern: Rapid asset requests followed by idle.
        """
        if behavior_type == "think_time":
            # Log-normal distribution for reading time (mean 3s)
            sleep_time = random.lognormvariate(1, 0.5)
            time.sleep(min(sleep_time, 10))
        elif behavior_type == "idle_micro":
            # Micro-jitter for mouse movement simulation overhead
            time.sleep(random.uniform(0.05, 0.2))