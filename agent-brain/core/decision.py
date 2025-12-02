import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import random


class DecisionMaker:
    """
    Strategic decision making for agent actions
    Generates strategies and makes tactical decisions
    """
    
    def __init__(self):
        self.strategy_templates = self._load_strategy_templates()
        self.decision_history: List[Dict] = []
        
    def _load_strategy_templates(self) -> Dict:
        """Load strategy templates"""
        return {
            "stealth": {
                "name": "Stealth Reconnaissance",
                "phases": [
                    {"phase": "passive_recon", "actions": ["dns_lookup", "whois", "certificate_analysis"]},
                    {"phase": "active_recon", "actions": ["port_scan_slow", "service_detection"]},
                    {"phase": "vulnerability_analysis", "actions": ["version_check", "cve_lookup"]},
                    {"phase": "exploitation", "actions": ["targeted_exploit", "minimal_footprint"]}
                ],
                "timing_multiplier": 3.0,
                "noise_level": "low"
            },
            "aggressive": {
                "name": "Aggressive Assessment",
                "phases": [
                    {"phase": "fast_recon", "actions": ["full_port_scan", "service_enumeration"]},
                    {"phase": "vulnerability_scan", "actions": ["automated_vuln_scan", "fuzz_testing"]},
                    {"phase": "exploitation", "actions": ["multi_exploit", "parallel_attacks"]}
                ],
                "timing_multiplier": 0.5,
                "noise_level": "high"
            },
            "balanced": {
                "name": "Balanced Assessment",
                "phases": [
                    {"phase": "initial_recon", "actions": ["targeted_scan", "service_detection"]},
                    {"phase": "vulnerability_analysis", "actions": ["smart_vuln_detection"]},
                    {"phase": "exploitation", "actions": ["verified_exploits"]}
                ],
                "timing_multiplier": 1.0,
                "noise_level": "medium"
            }
        }
    
    async def decide(
        self,
        analysis: Dict,
        constraints: List[str],
        available_actions: List[str]
    ) -> Dict:
        """
        Make a strategic decision based on analysis
        
        Args:
            analysis: Result from reasoning analyzer
            constraints: List of constraints to consider
            available_actions: Available actions to choose from
            
        Returns:
            Decision with recommended actions and reasoning
        """
        priority_findings = analysis.get("priority_findings", [])
        risk_assessment = analysis.get("risk_assessment", {})
        opportunity_score = analysis.get("opportunity_score", 0.5)
        
        filtered_actions = self._filter_by_constraints(available_actions, constraints)
        
        ranked_actions = self._rank_actions(filtered_actions, analysis)
        
        selected_actions = ranked_actions[:3]
        
        confidence = self._calculate_confidence(analysis, len(selected_actions))
        
        reasoning = self._generate_decision_reasoning(
            analysis, selected_actions, constraints
        )
        
        decision = {
            "actions": selected_actions,
            "confidence": confidence,
            "reasoning": reasoning,
            "constraints_applied": constraints,
            "risk_level": risk_assessment.get("overall_risk", "medium"),
            "timestamp": datetime.now().isoformat()
        }
        
        self.decision_history.append(decision)
        
        return decision
    
    async def generate_strategy(self, target: Dict, mode: str = "stealth") -> Dict:
        """
        Generate attack/assessment strategy for target
        
        Args:
            target: Target information
            mode: Strategy mode (stealth, aggressive, balanced)
            
        Returns:
            Complete strategy with phases and actions
        """
        template = self.strategy_templates.get(mode, self.strategy_templates["balanced"])
        
        target_type = target.get("type", "unknown")
        target_url = target.get("url", target.get("domain", ""))
        
        customized_phases = []
        for phase in template["phases"]:
            customized_phase = {
                "name": phase["phase"],
                "actions": [],
                "estimated_duration": self._estimate_duration(phase, template["timing_multiplier"]),
                "priority": self._get_phase_priority(phase["phase"])
            }
            
            for action in phase["actions"]:
                action_detail = {
                    "action": action,
                    "target": target_url,
                    "parameters": self._get_action_parameters(action, target, mode),
                    "timeout": self._get_action_timeout(action, template["timing_multiplier"])
                }
                customized_phase["actions"].append(action_detail)
                
            customized_phases.append(customized_phase)
        
        strategy = {
            "name": template["name"],
            "mode": mode,
            "target": target,
            "phases": customized_phases,
            "noise_level": template["noise_level"],
            "timing_multiplier": template["timing_multiplier"],
            "total_estimated_duration": sum(p["estimated_duration"] for p in customized_phases),
            "created_at": datetime.now().isoformat()
        }
        
        return strategy
    
    def _filter_by_constraints(self, actions: List[str], constraints: List[str]) -> List[str]:
        """Filter actions based on constraints"""
        filtered = actions.copy()
        
        constraint_filters = {
            "no_exploit": ["exploit_vulnerability", "data_exfiltration"],
            "passive_only": ["exploit_vulnerability", "lateral_movement", "privilege_escalation"],
            "stealth": ["exploit_vulnerability", "data_exfiltration", "lateral_movement"]
        }
        
        for constraint in constraints:
            if constraint in constraint_filters:
                for blocked_action in constraint_filters[constraint]:
                    if blocked_action in filtered:
                        filtered.remove(blocked_action)
                        
        return filtered
    
    def _rank_actions(self, actions: List[str], analysis: Dict) -> List[str]:
        """Rank actions by relevance to analysis"""
        action_scores = {}
        
        opportunity_score = analysis.get("opportunity_score", 0.5)
        has_vulnerabilities = bool(analysis.get("priority_findings", []))
        
        for action in actions:
            score = 0.5
            
            if has_vulnerabilities and "exploit" in action:
                score += 0.3
            elif not has_vulnerabilities and "scan" in action:
                score += 0.3
            elif "gather" in action or "analyze" in action:
                score += 0.2
                
            score += opportunity_score * 0.2
            
            action_scores[action] = score
        
        ranked = sorted(actions, key=lambda x: action_scores.get(x, 0), reverse=True)
        return ranked
    
    def _calculate_confidence(self, analysis: Dict, num_actions: int) -> float:
        """Calculate decision confidence"""
        base_confidence = 0.6
        
        if analysis.get("priority_findings"):
            base_confidence += 0.2
            
        if analysis.get("clear_objective", False):
            base_confidence += 0.15
            
        base_confidence -= max(0, (num_actions - 2) * 0.05)
        
        return round(min(max(base_confidence, 0.3), 0.95), 3)
    
    def _generate_decision_reasoning(
        self,
        analysis: Dict,
        selected_actions: List[str],
        constraints: List[str]
    ) -> str:
        """Generate human-readable reasoning for decision"""
        reasoning_parts = []
        
        if analysis.get("priority_findings"):
            reasoning_parts.append(
                f"Identified {len(analysis['priority_findings'])} priority findings requiring attention."
            )
        else:
            reasoning_parts.append("No immediate threats detected. Recommending reconnaissance actions.")
        
        if selected_actions:
            actions_str = ", ".join(selected_actions[:3])
            reasoning_parts.append(f"Recommended actions: {actions_str}.")
        
        if constraints:
            reasoning_parts.append(f"Operating under constraints: {', '.join(constraints)}.")
        
        return " ".join(reasoning_parts)
    
    def _estimate_duration(self, phase: Dict, multiplier: float) -> int:
        """Estimate duration for a phase in seconds"""
        base_durations = {
            "passive_recon": 60,
            "active_recon": 120,
            "fast_recon": 30,
            "initial_recon": 90,
            "vulnerability_analysis": 180,
            "vulnerability_scan": 240,
            "exploitation": 300
        }
        
        phase_name = phase.get("phase", "default")
        base = base_durations.get(phase_name, 120)
        
        return int(base * multiplier)
    
    def _get_phase_priority(self, phase_name: str) -> int:
        """Get priority for a phase (1 = highest)"""
        priorities = {
            "passive_recon": 1,
            "fast_recon": 1,
            "initial_recon": 1,
            "active_recon": 2,
            "vulnerability_analysis": 3,
            "vulnerability_scan": 3,
            "exploitation": 4
        }
        return priorities.get(phase_name, 5)
    
    def _get_action_parameters(self, action: str, target: Dict, mode: str) -> Dict:
        """Get parameters for an action"""
        params = {"target": target.get("url", target.get("domain", ""))}
        
        if mode == "stealth":
            params["rate_limit"] = 0.5
            params["randomize_timing"] = True
        elif mode == "aggressive":
            params["rate_limit"] = 10.0
            params["parallel"] = True
            
        return params
    
    def _get_action_timeout(self, action: str, multiplier: float) -> int:
        """Get timeout for an action in seconds"""
        base_timeouts = {
            "dns_lookup": 10,
            "whois": 15,
            "port_scan_slow": 300,
            "full_port_scan": 120,
            "service_detection": 60,
            "targeted_exploit": 180
        }
        
        base = base_timeouts.get(action, 60)
        return int(base * multiplier)
