import os
import json
from datetime import datetime
from typing import Dict, Any, List
from server.config import settings
import aiofiles
import logging

def setup_logging():
    """Setup Python's built-in logging system"""
    log_dir = settings.LOG_DIR
    log_file = os.path.join(
        log_dir,
        f"system_{datetime.now().strftime('%Y%m%d')}.log"
    )
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized")
    return logger


class Logger:
    """Logging system for all agent activities with per-agent log files"""
    
    def __init__(self):
        self.log_dir = settings.LOG_DIR
        self.findings_dir = settings.FINDINGS_DIR
        self.agent_logs_dir = os.path.join(self.log_dir, "agents")
        os.makedirs(self.agent_logs_dir, exist_ok=True)
        self._agent_log_files: Dict[str, str] = {}
        
    def _get_agent_log_path(self, agent_id: str) -> str:
        """Get or create per-agent log file path"""
        if agent_id not in self._agent_log_files:
            agent_num = agent_id.split('-')[-1][:8] if '-' in agent_id else agent_id[:8]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = os.path.join(
                self.agent_logs_dir,
                f"agent_{agent_num}_{timestamp}.log"
            )
            self._agent_log_files[agent_id] = log_file
        return self._agent_log_files[agent_id]
    
    async def log_agent_event(
        self,
        agent_id: str,
        message: str,
        event_type: str = "info",
        metadata: Dict[str, Any] = None
    ):
        """Log an event to per-agent log file and broadcast in real-time"""
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "type": event_type,
            "message": message,
            "metadata": metadata or {}
        }
        
        log_file = self._get_agent_log_path(agent_id)
        
        async with aiofiles.open(log_file, 'a') as f:
            await f.write(json.dumps(log_entry) + "\n")
        
        try:
            from server.ws import manager
            if manager and manager.active_connections:
                await manager.broadcast_agent_log(agent_id, log_entry)
        except Exception:
            pass
        
        await self.log_event(message, event_type, {**(metadata or {}), "agent_id": agent_id})
        
    async def log_event(
        self,
        message: str,
        event_type: str = "info",
        metadata: Dict[str, Any] = None
    ):
        """Log an event to file"""
        
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "type": event_type,
            "message": message,
            "metadata": metadata or {}
        }
        
        log_file = os.path.join(
            self.log_dir,
            f"agent_system_{datetime.now().strftime('%Y%m%d')}.log"
        )
        
        async with aiofiles.open(log_file, 'a') as f:
            await f.write(json.dumps(log_entry) + "\n")
    
    async def write_finding(self, agent_id: str, content: str, target: str = None, severity: str = "Info"):
        """Write finding to target-specific findings file"""
        
        target_name = target if target else "general"
        safe_target = "".join(c if c.isalnum() or c in "._-" else "_" for c in target_name[:50])
        target_dir = os.path.join(self.findings_dir, safe_target)
        os.makedirs(target_dir, exist_ok=True)
        
        findings_file = os.path.join(
            target_dir,
            f"findings_{datetime.now().strftime('%Y%m%d')}.txt"
        )
        
        timestamp = datetime.now().isoformat()
        
        async with aiofiles.open(findings_file, 'a') as f:
            await f.write(f"\n[{timestamp}] [{agent_id}] [{severity}]\n")
            await f.write(content + "\n")
            await f.write("-" * 80 + "\n")
        
        await self.log_agent_event(
            agent_id,
            f"Finding: {content[:100]}...",
            "finding",
            {"severity": severity, "target": target_name}
        )
    
    def get_agent_log_files(self) -> Dict[str, str]:
        """Get all agent log file paths"""
        return self._agent_log_files.copy()
    
    def create_agent_log(self, agent_id: str) -> str:
        """Create a new log file for an agent"""
        return self._get_agent_log_path(agent_id)


class ReportGenerator:
    """Generate reports from findings - JSON/TXT/PDF only (no HTML)"""
    
    def __init__(self, shared_knowledge: Dict, target: str = None):
        self.shared_knowledge = shared_knowledge
        self.target = target or "general"
        self.target_dir = os.path.join(settings.FINDINGS_DIR, self.target)
        os.makedirs(self.target_dir, exist_ok=True)
        
    async def generate_txt_report(self) -> str:
        """Generate clean TXT report"""
        
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = os.path.join(self.target_dir, filename)
        
        findings = self.shared_knowledge.get("findings", [])
        
        content = f"""CYBER SECURITY ASSESSMENT REPORT
Target: {self.target}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Findings: {len(findings)}

{'='*80}
FINDINGS
{'='*80}
"""
        
        for i, finding in enumerate(findings, 1):
            content += f"""
[{i}] {finding.get('severity', 'Info').upper()}
Content: {finding.get('content', 'N/A')}
Agent: {finding.get('agent_id', 'Unknown')}
Time: {finding.get('timestamp', 'Unknown')}
{'-'*80}
"""
        
        async with aiofiles.open(filepath, 'w') as f:
            await f.write(content)
        
        return filepath
    
    async def export_json(self) -> str:
        """Export findings as JSON"""
        
        filename = f"findings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.target_dir, filename)
        
        data = {
            "target": self.target,
            "timestamp": datetime.now().isoformat(),
            "findings": self.shared_knowledge.get("findings", [])
        }
        
        async with aiofiles.open(filepath, 'w') as f:
            await f.write(json.dumps(data, indent=2))
        
        return filepath
    
    async def generate_pdf(self) -> str:
        """Generate PDF report (if reportlab available)"""
        
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.target_dir, filename)
        
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor='#333333',
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            elements.append(Paragraph(f"Assessment Report: {self.target}", title_style))
            elements.append(Spacer(1, 0.3*inch))
            
            findings = self.shared_knowledge.get("findings", [])
            for finding in findings:
                severity = finding.get("severity", "Info")
                content = finding.get("content", "")
                elements.append(Paragraph(f"<b>[{severity}]</b> {content}", styles['Normal']))
                elements.append(Spacer(1, 0.2*inch))
            
            doc.build(elements)
        except ImportError:
            pass
        
        return filepath
