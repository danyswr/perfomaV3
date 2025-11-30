import random
import string
import hashlib
import time
import math
import uuid
import json
import base64
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

# --- Configuration Constants & Datasets ---

COMMON_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1"
]

TLS_CIPHERS = [
    "TLS_AES_128_GCM_SHA256", "TLS_AES_256_GCM_SHA384", "TLS_CHACHA20_POLY1305_SHA256",
    "ECDHE-ECDSA-AES128-GCM-SHA256", "ECDHE-RSA-AES128-GCM-SHA256",
    "ECDHE-ECDSA-AES256-GCM-SHA384", "ECDHE-RSA-AES256-GCM-SHA384",
    "ECDHE-ECDSA-CHACHA20-POLY1305", "ECDHE-RSA-CHACHA20-POLY1305",
    "ECDHE-RSA-AES128-SHA", "ECDHE-RSA-AES256-SHA", "AES128-GCM-SHA256",
    "AES256-GCM-SHA384", "AES128-SHA256", "AES256-SHA256"
]

TLS_EXTENSIONS = [
    "0", "23", "65281", "10", "11", "35", "16", "5", "13", "18", "51", "45", "43", "27", "21"
]

@dataclass
class SessionProfile:
    """Stores the behavioral profile of a simulated user session."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    patience_level: float = 1.0  # 0.5 (impatient) to 2.0 (very patient)
    mouse_speed: float = 1.0
    preferred_content_types: List[str] = field(default_factory=list)
    history: List[str] = field(default_factory=list)
    cookies: Dict[str, str] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

class TrafficObfuscator:
    """
    Advanced Traffic obfuscation techniques to avoid pattern detection.
    Includes JA3 signatures, HTTP/2 simulation, and behavioral profiling.
    """
    
    def __init__(self, profile_seed: int = None):
        if profile_seed:
            random.seed(profile_seed)
            
        self.dummy_params = self._generate_dummy_params()
        self.current_profile = self._initialize_session_profile()
        self.ja3_signature = self._generate_ja3_context()
        
    def _initialize_session_profile(self) -> SessionProfile:
        """Initialize a unique behavioral profile for this session instance."""
        profile = SessionProfile()
        profile.patience_level = random.uniform(0.8, 1.5)
        profile.mouse_speed = random.uniform(0.9, 1.2)
        # Simulate interest categories for referrer logic
        categories = ["tech", "news", "lifestyle", "shopping", "dev"]
        profile.preferred_content_types = random.sample(categories, k=random.randint(1, 3))
        return profile

    def _generate_dummy_params(self) -> List[str]:
        """Generate realistic-looking dummy parameter names based on ad-tech standards."""
        return [
            "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
            "ref", "source", "campaign_id", "gclid", "fbclid", "_ga",
            "session_id", "timestamp", "nonce", "cache_buster", "cb",
            "client_id", "user_id", "tracking_id", "request_id",
            "h", "v", "s", "q", "token", "auth_token", "csrf"
        ]
        
    # ==========================================
    # CORE PARAMETER OBFUSCATION
    # ==========================================

    def add_dummy_parameters(self, url: str, count: int = None) -> str:
        """
        Add dummy parameters to URL to obfuscate real intent.
        
        Args:
            url: Original URL
            count: Number of dummy params to add (random if None)
        """
        if '?' not in url:
            url += '?'
        elif not url.endswith('&') and not url.endswith('?'):
            url += '&'
        
        if count is None:
            # Randomize count based on URL length to look proportional
            count = random.randint(1, 4)
        
        params = []
        used_keys = set()
        
        for _ in range(count):
            # Ensure unique keys
            available_keys = [k for k in self.dummy_params if k not in used_keys]
            if not available_keys:
                break
                
            param_name = random.choice(available_keys)
            used_keys.add(param_name)
            
            param_value = self._generate_random_value(param_name)
            params.append(f"{param_name}={param_value}")
        
        return url + '&'.join(params)
    
    def _generate_random_value(self, context_key: str = "") -> str:
        """
        Generate realistic random parameter value based on the key name context.
        """
        # Context-aware value generation
        if "id" in context_key or "token" in context_key:
            return uuid.uuid4().hex[:random.randint(16, 32)]
        
        if "time" in context_key:
            return str(int(time.time() * 1000) - random.randint(0, 50000))
            
        value_types = [
            lambda: ''.join(random.choices(string.ascii_lowercase + string.digits, k=random.randint(6, 12))),
            lambda: str(random.randint(100000, 999999)),
            lambda: hashlib.md5(str(random.random()).encode()).hexdigest()[:16],
            lambda: base64.urlsafe_b64encode(random.randbytes(10)).decode().rstrip('=')
        ]
        return random.choice(value_types)()
    
    def randomize_parameter_order(self, url: str) -> str:
        """Randomize the order of URL parameters to evade signature detection."""
        if '?' not in url:
            return url
        
        base_url, params = url.split('?', 1)
        if not params:
            return url
            
        # Handle fragment identifiers if present
        fragment = ""
        if '#' in params:
            params, fragment = params.split('#', 1)
            fragment = '#' + fragment
            
        param_list = params.split('&')
        random.shuffle(param_list)
        
        return base_url + '?' + '&'.join(param_list) + fragment

    # ==========================================
    # HEADER & FINGERPRINTING OBFUSCATION
    # ==========================================

    def add_random_headers(self, base_headers: Dict[str, str]) -> Dict[str, str]:
        """
        Add random but realistic headers including HTTP/2 pseudo-header simulation
        and browser-specific headers.
        """
        headers = base_headers.copy()
        
        # Ensure User-Agent exists
        if "User-Agent" not in headers:
            headers["User-Agent"] = random.choice(COMMON_USER_AGENTS)

        # 1. Random Referer based on history or generic
        if "Referer" not in headers:
            headers["Referer"] = self._generate_referer_from_history()
        
        # 2. Client Hints (High entropy)
        if random.random() > 0.4:
            headers.update(self._generate_client_hints())

        # 3. HTTP/2 Priority (RFC 9218) or Legacy
        headers.update(self._generate_http2_priority())

        # 4. Cache Control Jitter
        if random.random() > 0.8:
            headers["Cache-Control"] = random.choice(["max-age=0", "no-cache", "no-store"])

        # 5. Language permutation
        headers["Accept-Language"] = self._generate_accept_language()

        return headers

    def _generate_ja3_context(self) -> Dict[str, str]:
        """
        Generates a random TLS JA3 signature string and associated parameters.
        This allows the calling network client to configure its SSL context to match.
        Format: SSLVersion,Ciphers,Extensions,EllipticCurves,EllipticCurvePointFormats
        """
        tls_version = "771" # TLS 1.2 (usually represented as decimal)
        
        # Randomize Ciphers
        num_ciphers = random.randint(8, 15)
        # Using simplified IDs for simulation. Real JA3 uses decimal IDs (e.g., 4865)
        cipher_ids = [str(random.randint(4865, 52393)) for _ in range(num_ciphers)]
        ciphers_str = "-".join(cipher_ids)
        
        # Randomize Extensions
        ext_list = TLS_EXTENSIONS.copy()
        random.shuffle(ext_list)
        ext_str = "-".join(ext_list[:random.randint(5, len(ext_list))])
        
        # Curves & Formats
        curves = ["23", "24", "25", "29"]
        curves_str = "-".join(random.sample(curves, k=random.randint(2, 4)))
        point_formats = "0" # Uncompressed
        
        ja3_string = f"{tls_version},{ciphers_str},{ext_str},{curves_str},{point_formats}"
        
        return {
            "ja3_string": ja3_string,
            "ja3_hash": hashlib.md5(ja3_string.encode()).hexdigest(),
            "simulated_ciphers": cipher_ids
        }

    def get_ja3_spoof_config(self) -> Dict[str, Any]:
        """Returns the current JA3 configuration to be applied to the socket/adapter."""
        return self.ja3_signature

    def _generate_http2_priority(self) -> Dict[str, str]:
        """
        Generates HTTP/2 Priority headers or RFC 9218 Priority headers.
        Randomization helps blend in with different browser stacks.
        """
        headers = {}
        # 70% chance to use new RFC 9218 Priority
        if random.random() < 0.7:
            urgency = random.randint(0, 7)
            incremental = random.choice([True, False])
            val = f"u={urgency}"
            if incremental:
                val += ", i"
            headers["Priority"] = val
        else:
            # Legacy HTTP/2 simulation often handled at frame level, 
            # but some proxies respect headers like X-Priority
            pass 
        return headers

    def configure_domain_fronting(self, real_host: str, front_domain: str) -> Tuple[str, Dict[str, str]]:
        """
        Configures Domain Fronting style traffic.
        
        Args:
            real_host: The actual hidden destination (e.g., my-c2.appspot.com)
            front_domain: The high-reputation domain to put in SNI (e.g., google.com)
            
        Returns:
            Tuple of (connection_url, headers_dict)
        """
        # The connection URL connects to the reputable domain (CDN/Front)
        connection_url = f"https://{front_domain}/"
        
        # The Host header guides the CDN to the internal origin
        headers = {
            "Host": real_host,
            "X-Forwarded-Proto": "https",
            "X-Original-Host": front_domain # Sometimes adds legitimacy
        }
        
        return connection_url, headers

    # ==========================================
    # BEHAVIORAL & TIMING OBFUSCATION
    # ==========================================

    def calculate_human_jitter(self, base_delay: float) -> float:
        """
        Calculates a 'human-like' delay using a Gaussian distribution.
        Humans don't wait exactly 1.0s, they wait 1.0s +/- variance.
        """
        # Calculate mean based on patience profile
        mean_delay = base_delay * self.current_profile.patience_level
        
        # Standard deviation is 20% of the mean
        sigma = mean_delay * 0.2
        
        jittered = random.gauss(mean_delay, sigma)
        return max(0.1, jittered) # Ensure at least 100ms

    def simulate_request_flow(self):
        """
        Blocking call that sleeps for a calculated 'human' amount of time 
        between requests. Call this before making a network request.
        """
        # Reading time simulation
        base_read_time = random.randint(2, 15)
        sleep_time = self.calculate_human_jitter(base_read_time)
        time.sleep(sleep_time)

    def generate_referer_chain(self, target_url: str) -> List[str]:
        """
        Generates a logical chain of history for the 'History' simulation.
        e.g., Search Engine -> Blog -> Landing Page -> Target
        """
        chain = []
        
        # Start with a search engine
        engines = [
            f"https://www.google.com/search?q={random.choice(['login', 'news', 'weather'])}",
            "https://duckduckgo.com/",
            "https://bing.com/"
        ]
        chain.append(random.choice(engines))
        
        # Maybe an intermediate site
        if random.random() > 0.5:
            intermediates = [
                "https://reddit.com/r/technology",
                "https://medium.com/topic/software",
                "https://stackoverflow.com/questions/"
            ]
            chain.append(random.choice(intermediates))
            
        # Update internal profile history
        self.current_profile.history.extend(chain)
        self.current_profile.history.append(target_url)
        
        return chain

    def _generate_referer_from_history(self) -> str:
        """Pick the last visited URL from profile history or a default."""
        if self.current_profile.history:
            # 80% chance to use the last URL, 20% to start fresh
            if random.random() < 0.8:
                return self.current_profile.history[-1]
        
        return random.choice([
            "https://www.google.com/",
            "https://www.bing.com/",
            "https://twitter.com/",
            "" # Direct entry
        ])

    def generate_realistic_cookies(self) -> Dict[str, str]:
        """Generate realistic-looking cookies based on session profile."""
        cookies = self.current_profile.cookies.copy()
        
        # Session cookie (always present/refreshed)
        if "session_id" not in cookies:
            cookies["session_id"] = self.current_profile.session_id
        
        # Analytics cookies (GA style)
        if random.random() > 0.3 and "_ga" not in cookies:
            cookies["_ga"] = f"GA1.2.{random.randint(100000000, 999999999)}.{int(time.time())}"
        
        if random.random() > 0.5 and "_gid" not in cookies:
            cookies["_gid"] = f"GA1.2.{random.randint(100000000, 999999999)}.{int(time.time())}"
            
        # Consent cookies
        if "consent" not in cookies:
            cookies["consent"] = "YES+" + datetime_str()
            
        # Security/CSRF tokens
        cookies["XSRF-TOKEN"] = hashlib.sha1(str(random.random()).encode()).hexdigest()
        
        # Save state
        self.current_profile.cookies = cookies
        return cookies

    # ==========================================
    # PAYLOAD & PADDING OBFUSCATION
    # ==========================================

    def add_random_packet_padding(self, data: Dict, min_size: int = 64, max_size: int = 1024) -> Dict:
        """
        Adds random padding to JSON payloads to vary packet sizes, making 
        traffic analysis (size fingerprinting) harder.
        """
        pad_size = random.randint(min_size, max_size)
        
        # Generate random junk data
        junk_data = ''.join(random.choices(string.ascii_letters + string.digits, k=pad_size))
        
        # Add as a benign field that most servers will ignore
        padding_keys = ["_padding", "meta_trace", "d_debug", "ux_metrics", "z_cache"]
        key = random.choice(padding_keys)
        
        data[key] = junk_data
        return data

    def generate_mouse_telemetry(self) -> Dict[str, Any]:
        """
        Generates fake mouse movement data to send in POST requests.
        This makes the session look highly interactive and human.
        """
        points = []
        start_x = random.randint(100, 500)
        start_y = random.randint(100, 500)
        
        # Generate a bezier-like curve (simplified)
        for i in range(random.randint(10, 50)):
            start_x += int(random.gauss(5, 2))
            start_y += int(random.gauss(2, 2))
            timestamp = int(time.time() * 1000) + (i * 20)
            points.append([start_x, start_y, timestamp])
            
        return {
            "telemetry": {
                "mouse_events": points,
                "screen_res": f"{random.choice([1920, 2560])}x{random.choice([1080, 1440])}",
                "pixel_ratio": random.choice([1, 1.5, 2])
            }
        }

    # ==========================================
    # HELPERS
    # ==========================================

    def _generate_client_hints(self) -> Dict[str, str]:
        """Generates Modern Browser Client Hints (sec-ch-ua)."""
        platform = "Windows"
        if "Macintosh" in self.current_profile.session_id: platform = "macOS" # simplified logic
        
        return {
            "sec-ch-ua": '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": f'"{platform}"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1"
        }
        
    def _generate_accept_language(self) -> str:
        """Generates q-factor weighted languages."""
        langs = ["en-US", "en-GB", "id-ID", "es-ES", "fr-FR"]
        primary = random.choice(langs)
        secondary = "en" if primary != "en" else "en-US"
        
        return f"{primary}, {secondary};q=0.9, *;q=0.8"

def datetime_str():
    """Helper for cookie dates."""
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d")


# ==========================================
# USAGE DEMONSTRATION
# ==========================================

if __name__ == "__main__":
    print("[*] Initializing Traffic Obfuscator Engine...")
    obfuscator = TrafficObfuscator()
    
    # 1. JA3 Signature Generation
    print("\n[1] --- Generated JA3 Signature (TLS Fingerprint) ---")
    ja3_config = obfuscator.get_ja3_spoof_config()
    print(f"JA3 Hash: {ja3_config['ja3_hash']}")
    print(f"String (Truncated): {ja3_config['ja3_string'][:60]}...")
    
    # 2. Domain Fronting
    print("\n[2] --- Domain Fronting Configuration ---")
    target = "api.malicious-c2.com"
    front = "www.google.com"
    url, headers = obfuscator.configure_domain_fronting(target, front)
    print(f"Connect URL: {url}")
    print(f"Host Header: {headers['Host']}")
    
    # 3. Request Generation with Padding & Dummy Params
    print("\n[3] --- Obfuscated Request Generation ---")
    base_url = "https://example.com/api/v1/status"
    
    # Add dummy params
    obfuscated_url = obfuscator.add_dummy_parameters(base_url)
    obfuscated_url = obfuscator.randomize_parameter_order(obfuscated_url)
    print(f"URL: {obfuscated_url}")
    
    # Headers
    req_headers = obfuscator.add_random_headers(headers)
    print("Headers:")
    for k, v in req_headers.items():
        print(f"  {k}: {v}")
        
    # Cookies
    cookies = obfuscator.generate_realistic_cookies()
    print("Cookies:", json.dumps(cookies, indent=2))
    
    # Payload with padding
    payload = {"command": "heartbeat", "status": "active"}
    padded_payload = obfuscator.add_random_packet_padding(payload, min_size=128)
    print("Padded Payload:", json.dumps(padded_payload))

    # 4. Behavioral Simulation
    print("\n[4] --- Behavioral Jitter ---")
    base_wait = 0.5
    jittered = obfuscator.calculate_human_jitter(base_wait)
    print(f"Base wait: {base_wait}s -> Jittered wait: {jittered:.4f}s (Patience Level: {obfuscator.current_profile.patience_level:.2f})")
    
    # 5. Telemetry
    print("\n[5] --- Fake Telemetry Data ---")
    print(str(obfuscator.generate_mouse_telemetry())[:150] + "...")

    print("\n[*] Obfuscation profile ready.")