import asyncio
import subprocess
import random
import time
import os
import platform
import sys
from typing import Optional, Dict
from datetime import datetime
from server.config import settings
from stealth.user_agent import UserAgentRotator
from stealth.proxy import ProxyChain
from stealth.timing import TimingRandomizer
from stealth.obfuscation import TrafficObfuscator
from stealth.fingerprint import FingerprintRandomizer

class CommandExecutor:
    """Executes security tool commands with advanced stealth capabilities and cross-platform support"""
    
    def __init__(self, agent_id: str, stealth_mode: bool = False, stealth_config: Optional[Dict] = None, target: str = "", os_type: str = "linux"):
        self.agent_id = agent_id
        self.target = target
        self.stealth_mode = stealth_mode
        self.stealth_config = stealth_config or {}
        self.os_type = os_type
        
        self.user_agent_rotator = UserAgentRotator(
            strategy=self.stealth_config.get("ua_strategy", "random")
        )
        self.proxy_chain = ProxyChain(
            proxy_list=self.stealth_config.get("proxies", [])
        )
        self.timing_randomizer = TimingRandomizer(
            min_delay=self.stealth_config.get("min_delay", 2.0),
            max_delay=self.stealth_config.get("max_delay", 8.0),
            strategy=self.stealth_config.get("timing_strategy", "human_like")
        )
        self.traffic_obfuscator = TrafficObfuscator()
        self.fingerprint_randomizer = FingerprintRandomizer()
        
        self.last_execution_time = 0
        self.error_count = 0
        self.execution_count = 0
        
        self.is_windows = os_type == "windows"
        self.log_dir = self._create_log_directory()
        
    def _create_log_directory(self) -> str:
        """Create log directory for this agent and target"""
        safe_target = "".join(c if c.isalnum() or c in "._-" else "_" for c in self.target[:50])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        log_dir = os.path.join("logs", "agents", self.agent_id, f"{safe_target}_{timestamp}")
        os.makedirs(log_dir, exist_ok=True)
        
        return log_dir
    
    def _get_shell_command(self, command: str) -> tuple:
        """Get the appropriate shell command based on the platform"""
        if self.is_windows:
            return (
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
                False
            )
        else:
            return (command, True)
    
    async def execute(self, command: str) -> str:
        """Execute command with advanced stealth and return output"""
        
        if self.stealth_mode:
            await self._apply_stealth_delay()
        
        if self.stealth_mode:
            command = self._apply_advanced_stealth(command)
        
        self.execution_count += 1
        log_file = os.path.join(self.log_dir, f"exec_{self.execution_count:04d}.log")
        
        try:
            shell_cmd, use_shell = self._get_shell_command(command)
            
            if use_shell:
                process = await asyncio.create_subprocess_shell(
                    shell_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            else:
                process = await asyncio.create_subprocess_exec(
                    *shell_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=600.0
                )
                
                output = stdout.decode('utf-8', errors='ignore')
                error = stderr.decode('utf-8', errors='ignore')
                
                self.error_count = 0
                self.last_execution_time = time.time()
                
                log_content = self._format_log(command, output, error)
                await self._write_log(log_file, log_content)
                
                if error and not output:
                    return f"Output:\n{output}\n\nErrors:\n{error}"
                return output if output else error
                
            except asyncio.TimeoutError:
                process.kill()
                timeout_msg = "Command execution timed out after 10 minutes"
                await self._write_log(log_file, self._format_log(command, "", timeout_msg))
                return timeout_msg
                
        except Exception as e:
            self.error_count += 1
            error_msg = f"Execution error: {str(e)}"
            await self._write_log(log_file, self._format_log(command, "", error_msg))
            return error_msg
    
    def _format_log(self, command: str, output: str, error: str) -> str:
        """Format log content"""
        timestamp = datetime.now().isoformat()
        log_lines = [
            f"=" * 80,
            f"Timestamp: {timestamp}",
            f"Agent: {self.agent_id}",
            f"Target: {self.target}",
            f"Command: {command}",
            f"Platform: {'Windows (PowerShell)' if self.is_windows else 'Linux (Bash)'}",
            f"=" * 80,
            f"\n--- STDOUT ---\n{output}" if output else "",
            f"\n--- STDERR ---\n{error}" if error else "",
            f"\n{'=' * 80}\n"
        ]
        return "\n".join(line for line in log_lines if line)
    
    async def _write_log(self, log_file: str, content: str):
        """Write log content to file asynchronously"""
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            print(f"Failed to write log: {e}")
    
    async def execute_background(self, command: str) -> str:
        """Execute command in background without waiting"""
        try:
            shell_cmd, use_shell = self._get_shell_command(command)
            
            if use_shell:
                process = await asyncio.create_subprocess_shell(
                    shell_cmd,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                    start_new_session=True
                )
            else:
                process = await asyncio.create_subprocess_exec(
                    *shell_cmd,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                    start_new_session=True
                )
            
            return f"Background process started with PID: {process.pid}"
            
        except Exception as e:
            return f"Failed to start background process: {str(e)}"
    
    def _apply_advanced_stealth(self, command: str) -> str:
        """Apply comprehensive stealth modifications to command"""
        
        user_agent = self.user_agent_rotator.get_user_agent()
        proxy = self.proxy_chain.get_proxy() if self.proxy_chain.working_proxies else None
        
        if any(tool in command.lower() for tool in ['nikto', 'dirb', 'curl', 'wget', 'whatweb']):
            if 'nikto' in command.lower():
                if '-useragent' not in command.lower():
                    command += f' -useragent "{user_agent}"'
                if '-Pause' not in command:
                    pause = random.randint(2, 5)
                    command += f' -Pause {pause}'
                if proxy and '-useproxy' not in command.lower():
                    command += f' -useproxy {proxy}'
                    
            elif 'curl' in command.lower():
                if '-A' not in command and '--user-agent' not in command.lower():
                    command += f' -A "{user_agent}"'
                if '--referer' not in command.lower():
                    referers = ["https://www.google.com/", "https://www.bing.com/"]
                    command += f' --referer "{random.choice(referers)}"'
                if proxy and '-x' not in command and '--proxy' not in command.lower():
                    command += f' -x {proxy}'
                if '--connect-timeout' not in command:
                    command += ' --connect-timeout 30'
                    
            elif 'wget' in command.lower():
                if '-U' not in command and '--user-agent' not in command.lower():
                    command += f' -U "{user_agent}"'
                if '--wait' not in command and '--random-wait' not in command:
                    command += f' --random-wait --wait={random.randint(2,5)}'
                if proxy:
                    proxy_env = f'http_proxy={proxy} https_proxy={proxy} '
                    command = proxy_env + command
        
        if 'nmap' in command.lower():
            if '-T' not in command:
                timing = random.choice(['-T2', '-T3']) if self.stealth_mode else '-T3'
                command += f' {timing}'
            
            if '-f' not in command and random.random() > 0.5:
                command += ' -f'
            
            if '-D' not in command and random.random() > 0.6:
                decoys = self._generate_decoy_ips(3)
                command += f' -D {",".join(decoys)},ME'
            
            if '--source-port' not in command and random.random() > 0.5:
                port = random.choice([53, 80, 443, 8080])
                command += f' --source-port {port}'
            
            if '--randomize-hosts' not in command:
                command += ' --randomize-hosts'
            
            if proxy and 'proxychains' not in command:
                command = f'proxychains4 {command}'
        
        if 'sqlmap' in command.lower():
            if '--user-agent' not in command and '--random-agent' not in command:
                command += f' --user-agent="{user_agent}"'
            
            if '--delay' not in command:
                command += f' --delay={random.randint(2, 5)}'
            
            if '--randomize' not in command:
                command += ' --randomize=param'
            
            if proxy and '--proxy' not in command:
                command += f' --proxy={proxy}'
        
        if any(tool in command.lower() for tool in ['gobuster', 'dirb', 'ffuf']):
            if 'gobuster' in command.lower():
                if '-a' not in command and '--useragent' not in command:
                    command += f' -a "{user_agent}"'
                if '--delay' not in command:
                    delay = f'{random.randint(500, 2000)}ms'
                    command += f' --delay {delay}'
                if proxy and '-p' not in command and '--proxy' not in command:
                    command += f' --proxy {proxy}'
        
        return command
    
    def _generate_decoy_ips(self, count: int) -> list:
        """Generate random decoy IP addresses"""
        decoys = []
        for _ in range(count):
            ip = f"{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"
            decoys.append(ip)
        return decoys
    
    async def _apply_stealth_delay(self):
        """Apply intelligent delay based on stealth configuration and error history"""
        
        if self.error_count > 0:
            delay = self.timing_randomizer.get_adaptive_delay(error_occurred=True)
        else:
            delay = self.timing_randomizer.get_delay()
        
        if self.last_execution_time > 0:
            elapsed = time.time() - self.last_execution_time
            if elapsed < delay:
                await asyncio.sleep(delay - elapsed)
        else:
            await asyncio.sleep(delay)
    
    def get_log_directory(self) -> str:
        """Get the log directory for this agent"""
        return self.log_dir
    
    def get_execution_stats(self) -> Dict:
        """Get execution statistics"""
        return {
            "agent_id": self.agent_id,
            "target": self.target,
            "execution_count": self.execution_count,
            "error_count": self.error_count,
            "last_execution_time": self.last_execution_time,
            "log_directory": self.log_dir,
            "platform": "windows" if self.is_windows else "linux"
        }
