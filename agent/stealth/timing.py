import random
import asyncio
import math
import time
import secrets
import collections
from typing import Optional, List, Dict
from enum import Enum

class BehaviorState(Enum):
    FOCUSED = "focused"       # Cepat, variansi rendah
    DISTRACTED = "distracted" # Lambat, variansi tinggi
    TIRED = "tired"           # Lambat bertahap, jeda panjang
    CONFUSED = "confused"     # Erratic, pola tidak menentu

class TimingRandomizer:
    """
    Entropy-Driven Timing Engine dengan Behavior State Machine & OS Mimicry.
    Menggunakan enkripsi memori internal (CTE) untuk menyembunyikan pola dari analisis forensik.
    """
    
    def __init__(
        self,
        min_delay: float = 1.0,
        max_delay: float = 5.0,
        strategy: str = "epoch_adaptive"
    ):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.strategy = strategy
        
        # --- Cloaked-Timing Encryption (CTE) Setup ---
        # Kita tidak menyimpan request_count mentah di memori agar tidak mudah discan
        self._cte_key = secrets.randbits(32)
        self._encrypted_count = 0 ^ self._cte_key
        self._encrypted_error_count = 0 ^ self._cte_key
        
        # --- Neural Timing Memory (NTM-lite) ---
        # Short-term memory untuk menghitung entropi & mencegah repetisi
        self._ntm_history = collections.deque(maxlen=20)
        
        # --- Behavior State Machine ---
        self._current_state = BehaviorState.FOCUSED
        self._state_timer = time.time()
        self._state_duration = random.uniform(30, 120)  # State berubah tiap 30-120 detik
        
        # --- Epoch-Based Mutation ---
        self._current_epoch_strategy = "gaussian"
        self._epoch_counter = 0
        
        # --- OS Scheduler Profiles (Micro-Jitter) ---
        self._os_profiles = {
            "windows": lambda: random.uniform(0.010, 0.016), # ~15.6ms timer resolution
            "linux": lambda: random.uniform(0.0005, 0.002),  # Tighter scheduler
            "android": lambda: random.expovariate(1.0 / 0.05) if random.random() < 0.1 else 0.001 # Battery saving spikes
        }
        self._selected_os = secrets.choice(list(self._os_profiles.keys()))

    def _cte_get_count(self) -> int:
        """Decrypt internal counter on the fly"""
        return self._encrypted_count ^ self._cte_key

    def _cte_increment_count(self):
        """Increment count securely and rotate key to shift memory footprint"""
        val = self._cte_get_count() + 1
        # Rotate key to change the encrypted value signature in memory
        new_key = secrets.randbits(32)
        self._encrypted_count = val ^ new_key
        self._cte_key = new_key

    def _cte_get_error_count(self) -> int:
        return self._encrypted_error_count ^ self._cte_key
    
    def _cte_add_error(self):
        val = self._cte_get_error_count() + 1
        self._encrypted_error_count = val ^ self._cte_key

    def _cte_reset_error(self):
        self._encrypted_error_count = 0 ^ self._cte_key

    def _calculate_entropy(self) -> float:
        """Menghitung Shannon Entropy dari history delay untuk mendeteksi pola statis"""
        if not self._ntm_history:
            return 1.0
        
        # Binning data untuk menghitung frekuensi
        bins = collections.defaultdict(int)
        for d in self._ntm_history:
            bins[round(d, 1)] += 1 # Round ke 100ms terdekat
            
        entropy = 0.0
        total = len(self._ntm_history)
        for count in bins.values():
            p = count / total
            entropy -= p * math.log2(p)
            
        return entropy

    def _update_behavior_state(self):
        """Update state agent mirip mood manusia"""
        now = time.time()
        if now - self._state_timer > self._state_duration:
            # Transisi State
            choices = list(BehaviorState)
            weights = [0.4, 0.3, 0.2, 0.1] # Focused lebih sering
            self._current_state = random.choices(choices, weights=weights, k=1)[0]
            
            self._state_timer = now
            self._state_duration = random.uniform(30, 300)
            
            # Epoch Mutation: Ganti strategi matematis dasar setiap ganti state
            strategies = ["gaussian", "exponential", "lognormal", "uniform"]
            self._current_epoch_strategy = random.choice(strategies)

    def _apply_os_scheduler_mimic(self, delay: float) -> float:
        """Menambahkan micro-jitter berdasarkan OS Scheduler"""
        jitter_func = self._os_profiles[self._selected_os]
        os_noise = jitter_func()
        return delay + os_noise

    def get_delay(self) -> float:
        """
        Get next delay using Entropy-Driven Engine + Behavior State + OS Mimic
        """
        self._cte_increment_count()
        self._update_behavior_state()
        
        # 1. Base Delay calculation based on Epoch Strategy
        val = 0.0
        mean = (self.min_delay + self.max_delay) / 2
        
        if self._current_epoch_strategy == "gaussian":
            val = random.gauss(mean, (self.max_delay - self.min_delay) / 4)
        elif self._current_epoch_strategy == "exponential":
            val = random.expovariate(1.0 / mean)
        elif self._current_epoch_strategy == "lognormal":
            val = random.lognormvariate(math.log(mean), 0.3)
        else:
            val = random.uniform(self.min_delay, self.max_delay)
            
        # 2. Apply Behavior State Modifier
        if self._current_state == BehaviorState.FOCUSED:
            val *= 0.8 # Lebih cepat
        elif self._current_state == BehaviorState.DISTRACTED:
            val *= random.uniform(1.0, 1.5) # Kadang lambat
        elif self._current_state == BehaviorState.TIRED:
            val *= 1.8 # Lambat signifikan
        elif self._current_state == BehaviorState.CONFUSED:
            if random.random() < 0.3:
                val *= 3.0 # Hesitation pause
                
        # Clamp value
        val = max(self.min_delay, min(val, self.max_delay * 3))
        
        # 3. Entropy Check (Chaos Injection)
        # Jika entropi terlalu rendah (pola terlalu rapi/terdeteksi), suntikkan chaos
        current_entropy = self._calculate_entropy()
        if current_entropy < 1.5 and len(self._ntm_history) > 10:
            chaos_factor = random.uniform(0.5, 2.0)
            val *= chaos_factor
            
        # 4. OS Scheduler Mimicry (Micro-timing)
        final_delay = self._apply_os_scheduler_mimic(val)
        
        # Update Memory
        self._ntm_history.append(final_delay)
        
        return final_delay
    
    async def wait(self):
        """Async wait with advanced calculated delay"""
        delay = self.get_delay()
        await asyncio.sleep(delay)
    
    def _sigmoid_recovery(self, x: int) -> float:
        """
        Fungsi Sigmoid untuk recovery yang smooth.
        Menghasilkan kurva S, bukan lonjakan tajam.
        """
        # x adalah error count. Shift kurva agar mulai naik di error ke-2 atau ke-3
        # k adalah kecuraman kurva
        k = 1.5 
        x0 = 4 # Titik tengah sigmoid (di error ke-4 delay naik drastis)
        
        sigmoid_val = 1 / (1 + math.exp(-k * (x - x0)))
        return sigmoid_val

    def get_adaptive_delay(self, error_occurred: bool = False) -> float:
        """
        Error-Aware Auto Recovery Curve.
        Menggunakan Sigmoid Curve untuk menaikkan delay secara natural saat error terjadi.
        """
        if error_occurred:
            self._cte_add_error()
            err_count = self._cte_get_error_count()
            
            # Hitung multiplier menggunakan sigmoid
            # Range multiplier: dari 1x sampai 10x max_delay
            severity = self._sigmoid_recovery(err_count)
            
            base = self.get_delay()
            penalty = self.max_delay * 10 * severity
            
            total_delay = base + penalty
            return min(total_delay, 300) # Cap at 5 mins
            
        else:
            # Jika sukses, kurangi error count perlahan (Decay)
            current_err = self._cte_get_error_count()
            if current_err > 0 and random.random() > 0.5:
                 # Tidak langsung 0, tapi turun pelan-pelan biar pola "sembuh" natural
                val = current_err - 1
                self._encrypted_error_count = val ^ self._cte_key
                
            return self.get_delay()

    def get_jittered_interval(self, base_interval: float, jitter: float = 0.3) -> float:
        """
        Add jitter to a base interval with OS Mimicry
        """
        jitter_amount = base_interval * jitter
        val = base_interval + random.uniform(-jitter_amount, jitter_amount)
        return self._apply_os_scheduler_mimic(val)