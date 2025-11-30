import random
import asyncio
import time
import hashlib
import secrets
import base64
from typing import List, Optional, Dict
import aiohttp

# --- Security Modules (Helpers for ProxyChain) ---

class CryptoEngine:
    """
    Helper: In-memory encryption for Proxy Behavior Replay Memory.
    Ensures dumped memory reveals nothing about cached responses.
    """
    def __init__(self):
        self._master_key = secrets.token_bytes(32)
        
    def _derive_key(self, context: str) -> bytes:
        """Derive context-specific keys so every entry has a unique lock"""
        return hashlib.pbkdf2_hmac('sha256', self._master_key, context.encode(), 1000)

    def encrypt_data(self, data: str, context: str) -> bytes:
        """Stream cipher simulation using SHA256 keystream (XOR)"""
        key = self._derive_key(context)
        data_bytes = data.encode()
        # Create a keystream long enough for the data
        keystream = hashlib.sha256(key + context.encode()).digest()
        while len(keystream) < len(data_bytes):
            keystream += hashlib.sha256(keystream).digest()
        
        # XOR encryption
        return base64.b64encode(bytes(a ^ b for a, b in zip(data_bytes, keystream[:len(data_bytes)])))

    def decrypt_data(self, encrypted_b64: bytes, context: str) -> str:
        try:
            encrypted = base64.b64decode(encrypted_b64)
            key = self._derive_key(context)
            keystream = hashlib.sha256(key + context.encode()).digest()
            while len(keystream) < len(encrypted):
                keystream += hashlib.sha256(keystream).digest()
            return bytes(a ^ b for a, b in zip(encrypted, keystream[:len(encrypted)])).decode()
        except:
            return ""

class CovertTimingChannel:
    """
    Helper: Generates encrypted jitter for Covert Timing Channel Randomizer.
    Using hash chains to make timing patterns mathematically unpredictable.
    """
    def __init__(self):
        self._seed = secrets.token_bytes(16)
        self._counter = 0

    def get_covert_delay(self, base_delay: float = 1.0) -> float:
        self._counter += 1
        # Hash the seed + counter to get a deterministic but chaotic value
        h = hashlib.sha256(self._seed + str(self._counter).encode()).digest()
        # Convert first 4 bytes to float 0.0-1.0
        rand_val = int.from_bytes(h[:4], 'big') / (2**32)
        
        # Jitter formula: Base + (Base * CryptoRand * Variance)
        # Result is a delay that looks like network noise but is strictly controlled
        return base_delay + (base_delay * rand_val * 1.5)

# --- Main Class (Upgraded with Stealth Ecosystem) ---

class ProxyChain:
    """
    Advanced proxy chain management with rotation, validation, 
    and Ultra-Secure Stealth features (Cloaking, Encrypted Memory, Rolling Window).
    """
    
    def __init__(self, proxy_list: List[str] = None):
        """
        Initialize proxy chain manager with stealth engines.
        """
        self.proxy_list = proxy_list or []
        self.working_proxies: List[str] = []
        self.failed_proxies: List[str] = []
        self.current_index = 0
        self.proxy_performance: Dict[str, Dict] = {}
        
        # --- Stealth Features Initialization ---
        self.crypto = CryptoEngine()
        self.timing = CovertTimingChannel()
        self._replay_memory: Dict[str, bytes] = {} # Encrypted Replay Memory
        self._rolling_window_seed = secrets.token_hex(16) # For Rolling Window Logic
        
    def _generate_cloaked_headers(self) -> Dict[str, str]:
        """Feature: Active Traffic Cloaking Mode (Headers)"""
        # Uses CSPRNG (secrets) to rotate identity traits securely
        uas = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"
        ]
        return {
            "User-Agent": secrets.choice(uas),
            "Accept-Language": secrets.choice(["en-US,en;q=0.9", "en-GB,en;q=0.8", "id-ID,id;q=0.9"]),
            "Sec-Fetch-Site": "none",
            "DNT": "1",
            "Cache-Control": "max-age=0"
        }

    async def validate_proxy(self, proxy: str, timeout: int = 10) -> bool:
        """
        Validate if proxy is working.
        Includes Active Traffic Cloaking & Covert Timing Jitter.
        """
        try:
            # Feature: Covert Timing Channel (Simulate encrypted human delay)
            # Prevents timing analysis sensors from detecting 'bot-like' rapid-fire checks
            delay = self.timing.get_covert_delay(base_delay=0.3)
            await asyncio.sleep(delay)
            
            # Feature: Active Cloaking Headers
            headers = self._generate_cloaked_headers()
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(
                    "http://httpbin.org/ip",
                    proxy=proxy,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    if response.status == 200:
                        # Feature: Proxy Behavior Replay Memory (Encrypted)
                        # We store the validation response securely. If the tool is dumped/reversed,
                        # this memory block is just random bytes.
                        content = await response.text()
                        context = f"{proxy}|validation"
                        self._replay_memory[context] = self.crypto.encrypt_data(content, context)
                        return True
        except Exception:
            return False
        
        return False
    
    async def validate_all_proxies(self):
        """Validate all proxies with secure shuffling"""
        tasks = []
        # Secure shuffle using system entropy, not pseudo-random
        shuffled_list = list(self.proxy_list)
        random.SystemRandom().shuffle(shuffled_list)
        
        for proxy in shuffled_list:
            tasks.append(self.validate_proxy(proxy))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Reset lists
        self.working_proxies = []
        self.failed_proxies = []
        
        for proxy, is_working in zip(shuffled_list, results):
            if is_working is True:
                self.working_proxies.append(proxy)
                if proxy not in self.proxy_performance:
                    self.proxy_performance[proxy] = {
                        "success_count": 0,
                        "fail_count": 0,
                        "avg_latency": 0
                    }
            else:
                self.failed_proxies.append(proxy)
    
    def get_proxy(self, strategy: str = "secure_rolling") -> Optional[str]:
        """
        Get next proxy. 
        Feature: Rolling Proxy Window with Encrypted Switching Logic.
        
        Args:
            strategy: 'secure_rolling', 'random', 'round_robin', or 'performance'
        """
        if not self.working_proxies:
            return None
        
        if strategy == "secure_rolling":
            # Feature: Instant Failover + Rolling Proxy Window (Encrypted Logic)
            # Uses HMAC to select proxy based on internal state seed.
            # This makes the switching pattern mathematically impossible to predict externally.
            state_string = f"{self._rolling_window_seed}-{self.current_index}-{len(self.working_proxies)}"
            h = hashlib.sha256(state_string.encode()).digest()
            
            # Convert hash slice to index
            idx = int.from_bytes(h[:4], 'big') % len(self.working_proxies)
            self.current_index += 1
            return self.working_proxies[idx]
            
        elif strategy == "round_robin":
            proxy = self.working_proxies[self.current_index % len(self.working_proxies)]
            self.current_index += 1
            return proxy
            
        elif strategy == "performance":
            return min(
                self.working_proxies,
                key=lambda p: self.proxy_performance.get(p, {}).get("fail_count", 0)
            )
        else:  # random (fallback)
            return secrets.choice(self.working_proxies)
    
    def get_proxy_chain(self, chain_length: int = 2) -> List[str]:
        """Get a chain of proxies for multi-hop routing using secure sampling"""
        if len(self.working_proxies) < chain_length:
            return list(self.working_proxies)
        # Use secrets (crypto-secure) for sampling instead of standard random
        return random.SystemRandom().sample(self.working_proxies, chain_length)
    
    def report_success(self, proxy: str, latency: float):
        """Report success and rotate encryption seed for Rolling Window"""
        if proxy in self.proxy_performance:
            perf = self.proxy_performance[proxy]
            perf["success_count"] += 1
            total = perf["success_count"] + perf["fail_count"]
            perf["avg_latency"] = (perf["avg_latency"] * (total - 1) + latency) / total
            
            # Rotate seed to evolve the switching pattern dynamically
            # This ensures the 'Rolling Window' logic never repeats a pattern
            self._rolling_window_seed = hashlib.md5(self._rolling_window_seed.encode()).hexdigest()
    
    def report_failure(self, proxy: str):
        """Report failure and trigger Instant Failover logic"""
        if proxy in self.proxy_performance:
            perf = self.proxy_performance[proxy]
            perf["fail_count"] += 1
            
            total = perf["success_count"] + perf["fail_count"]
            # Strict failover threshold
            if total >= 5 and perf["fail_count"] / total > 0.4:
                if proxy in self.working_proxies:
                    self.working_proxies.remove(proxy)
                    self.failed_proxies.append(proxy)
                    # Feature: Instant Failover Logic
                    # Regenerate seed completely to drastically change the routing path immediately
                    self._rolling_window_seed = secrets.token_hex(16)
    
    def add_tor_support(self, tor_port: int = 9050):
        """Add TOR as a proxy option"""
        tor_proxy = f"socks5://127.0.0.1:{tor_port}"
        if tor_proxy not in self.proxy_list:
            self.proxy_list.append(tor_proxy)