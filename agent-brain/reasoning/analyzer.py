from typing import Dict, List, Optional, Any
from datetime import datetime
import json


class ReasoningAnalyzer:
    """
    Analyzes tasks and situations using reasoning techniques
    """
    
    def __init__(self):
        self.analysis_history: List[Dict] = []
        
    async def analyze(
        self,
        task: str,
        context: Dict,
        history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Perform deep analysis of a task
        
        Args:
            task: The task to analyze
            context: Current context
            history: Historical data for reference
            
        Returns:
            Analysis result with findings and recommendations
        """
        task_type = self._classify_task(task)
        priority_findings = self._identify_priority_findings(context)
        risk_assessment = self._assess_risks(task, context)
        opportunity_score = self._calculate_opportunity(task, context, history or [])
        
        action_suggestions = self._generate_suggestions(
            task_type, priority_findings, risk_assessment
        )
        
        analysis = {
            "task": task,
            "task_type": task_type,
            "priority_findings": priority_findings,
            "risk_assessment": risk_assessment,
            "opportunity_score": opportunity_score,
            "action_suggestions": action_suggestions,
            "clear_objective": self._has_clear_objective(task),
            "timestamp": datetime.now().isoformat()
        }
        
        self.analysis_history.append(analysis)
        
        return analysis
    
    def _classify_task(self, task: str) -> str:
        """Classify the type of task"""
        task_lower = task.lower()
        
        if any(kw in task_lower for kw in ["scan", "enumerate", "discover"]):
            return "reconnaissance"
        elif any(kw in task_lower for kw in ["exploit", "attack", "pwn"]):
            return "exploitation"
        elif any(kw in task_lower for kw in ["analyze", "investigate", "review"]):
            return "analysis"
        elif any(kw in task_lower for kw in ["report", "document", "summarize"]):
            return "reporting"
        elif any(kw in task_lower for kw in ["defend", "protect", "mitigate"]):
            return "defense"
        else:
            return "general"
    
    def _identify_priority_findings(self, context: Dict) -> List[Dict]:
        """Identify priority findings from context"""
        findings = []
        
        current = context.get("current", {})
        
        if "vulnerabilities" in current:
            for vuln in current["vulnerabilities"]:
                severity = vuln.get("severity", "").lower()
                if severity in ["critical", "high"]:
                    findings.append({
                        "type": "vulnerability",
                        "severity": severity,
                        "details": vuln
                    })
        
        if "open_ports" in current:
            critical_ports = [22, 23, 3389, 445, 1433, 3306, 5432]
            for port in current["open_ports"]:
                if port in critical_ports:
                    findings.append({
                        "type": "open_critical_port",
                        "severity": "high",
                        "port": port
                    })
        
        return findings
    
    def _assess_risks(self, task: str, context: Dict) -> Dict:
        """Assess risks associated with task"""
        risk_factors = []
        overall_risk = "low"
        
        task_lower = task.lower()
        if any(kw in task_lower for kw in ["exploit", "attack", "pwn"]):
            risk_factors.append("aggressive_action")
            overall_risk = "high"
        
        current = context.get("current", {})
        if current.get("detection_count", 0) > 0:
            risk_factors.append("previous_detection")
            overall_risk = "high" if overall_risk != "high" else overall_risk
        
        if current.get("stealth_mode", False):
            overall_risk = "medium" if overall_risk == "high" else overall_risk
        
        return {
            "overall_risk": overall_risk,
            "risk_factors": risk_factors,
            "mitigation_suggestions": self._suggest_mitigations(risk_factors)
        }
    
    def _suggest_mitigations(self, risk_factors: List[str]) -> List[str]:
        """Suggest risk mitigations"""
        mitigations = []
        
        if "aggressive_action" in risk_factors:
            mitigations.append("Use timing delays between actions")
            mitigations.append("Consider stealth mode")
            
        if "previous_detection" in risk_factors:
            mitigations.append("Change IP/proxy")
            mitigations.append("Wait before continuing")
            
        return mitigations
    
    def _calculate_opportunity(
        self,
        task: str,
        context: Dict,
        history: List[Dict]
    ) -> float:
        """Calculate opportunity score"""
        score = 0.5
        
        current = context.get("current", {})
        
        if current.get("vulnerabilities"):
            score += 0.2
            
        if current.get("credentials"):
            score += 0.2
            
        for hist in history[-10:]:
            if hist.get("success", False):
                score += 0.05
            if hist.get("failure", False):
                score -= 0.05
        
        return round(min(max(score, 0.1), 1.0), 3)
    
    def _generate_suggestions(
        self,
        task_type: str,
        priority_findings: List[Dict],
        risk_assessment: Dict
    ) -> List[str]:
        """Generate action suggestions"""
        suggestions = []
        
        if task_type == "reconnaissance":
            suggestions.append("Start with passive reconnaissance")
            suggestions.append("Enumerate subdomains and services")
            
        elif task_type == "exploitation":
            if priority_findings:
                suggestions.append("Focus on critical findings first")
            suggestions.append("Verify exploits in safe environment")
            
        elif task_type == "analysis":
            suggestions.append("Correlate findings from multiple sources")
            suggestions.append("Document all observations")
        
        if risk_assessment.get("overall_risk") == "high":
            suggestions.insert(0, "Consider risk mitigation before proceeding")
            
        return suggestions
    
    def _has_clear_objective(self, task: str) -> bool:
        """Check if task has a clear objective"""
        if len(task) < 10:
            return False
            
        action_words = ["scan", "exploit", "analyze", "find", "discover", "report", "enumerate"]
        return any(word in task.lower() for word in action_words)
