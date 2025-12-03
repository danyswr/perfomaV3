import random
import hashlib
import json
from typing import Dict, Tuple

# =============================================
#  Advanced Fingerprint Randomizer (Upgraded)
#  Class name & structure tetap sama sesuai permintaan
# =============================================

class FingerprintRandomizer:
    """Randomize browser fingerprints to avoid tracking — ADVANCED VERSION"""

    def __init__(self):
        self.session_id = self._generate_session_id()
        self.current_profile = self._choose_browser_profile()
        self.current_fingerprint = self._generate_fingerprint()

    # ==================================================
    # SESSION SYSTEM (Stable fingerprint per session)
    # ==================================================
    def _generate_session_id(self) -> str:
        return hashlib.md5(str(random.random()).encode()).hexdigest()

    # ==================================================
    # Browser Profiles (Sync UA, Platform, Resolutions)
    # ==================================================
    def _choose_browser_profile(self):
        profiles = {
            "chrome_win": {
                "platform": "Win32",
                "user_agents": [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/118.0 Safari/537.36"
                ],
                "resolutions": [(1920,1080),(1366,768),(1600,900)],
                "languages": ["en-US","en-GB","de-DE"]
            },
            "chrome_mac": {
                "platform": "MacIntel",
                "user_agents": [
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_2_1) AppleWebKit/537.36 Chrome/123.0 Safari/537.36",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_4) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
                ],
                "resolutions": [(2560,1440),(1440,900)],
                "languages": ["en-US","fr-FR","es-ES"]
            },
            "chrome_linux": {
                "platform": "Linux x86_64",
                "user_agents": [
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
                ],
                "resolutions": [(1920,1080),(1280,720),(1600,900)],
                "languages": ["en-US","de-DE","en-CA"]
            }
        }
        return random.choice(list(profiles.values()))

    # ==================================================
    #  ADVANCED FINGERPRINT GENERATOR
    # ==================================================
    def _generate_fingerprint(self) -> Dict:
        profile = self.current_profile

        # Screen resolution (based on chosen profile)
        screen_width, screen_height = random.choice(profile["resolutions"])

        # Minor noise on timezone offset
        timezone_base = random.choice([-8,-7,-5,-4,0,1,2,8,9]) * 60
        timezone_offset = timezone_base + random.randint(-2, 2)

        fingerprint = {
            # BASIC
            "session_id": self.session_id,
            "user_agent": random.choice(profile["user_agents"]),
            "screen_width": screen_width,
            "screen_height": screen_height,
            "color_depth": random.choice([24, 30, 32]),
            "timezone_offset": timezone_offset,
            "language": random.choice(profile["languages"]),
            "platform": profile["platform"],
            "hardware_concurrency": random.choice([2,4,8,12,16]),
            "device_memory": random.choice([4,8,16,32]),
            "do_not_track": random.choice(["1","0",None]),

            # ADVANCED (Simulated DOM, Canvas, WebGL)
            "max_touch_points": random.choice([0,1,5]),
            "pixel_ratio": random.choice([1,1.25,1.5,2,3]),
            "webdriver": False,
            "canvas_hash": self._fake_canvas_hash(),
            "webgl_vendor": random.choice(["Google Inc.", "NVIDIA Corporation", "AMD"]),
            "webgl_renderer": random.choice([
                "ANGLE (NVIDIA GeForce GTX 1050)",
                "Mesa Intel(R) UHD Graphics",
                "ANGLE (AMD Radeon RX 580)"
            ]),
            "audio_fp": self._fake_audio_fingerprint(),
        }

        return fingerprint

    # ==================================================
    #  Canvas Fingerprint Generator
    # ==================================================
    def _fake_canvas_hash(self) -> str:
        base = str(random.random()) + str(random.randint(1, 999999))
        return hashlib.sha256(base.encode()).hexdigest()

    # ==================================================
    # Audio Fingerprint Simulation
    # ==================================================
    def _fake_audio_fingerprint(self) -> str:
        base = str(random.random()) + "audio-context"
        return hashlib.md5(base.encode()).hexdigest()

    # ==================================================
    # PUBLIC API (Tetap sama)
    # ==================================================
    def get_fingerprint(self) -> Dict:
        return self.current_fingerprint.copy()

    def rotate_fingerprint(self):
        self.session_id = self._generate_session_id()
        self.current_profile = self._choose_browser_profile()
        self.current_fingerprint = self._generate_fingerprint()

    def apply_to_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        headers = headers.copy()

        fp = self.current_fingerprint

        # User-Agent
        headers["User-Agent"] = fp["user_agent"]

        # Do Not Track
        if fp.get("do_not_track"):
            headers["DNT"] = fp["do_not_track"]

        # Language
        headers["Accept-Language"] = fp["language"]

        return headers
