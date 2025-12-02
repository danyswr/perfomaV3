from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio


class ChainOfThought:
    """
    Implements chain-of-thought reasoning for complex problem solving
    """
    
    def __init__(self):
        self.thought_chains: List[Dict] = []
        
    async def reason(self, problem: str, context: Dict) -> Dict:
        """
        Apply chain-of-thought reasoning to a problem
        
        Args:
            problem: The problem to solve
            context: Relevant context
            
        Returns:
            Reasoning chain with conclusion
        """
        chain = {
            "problem": problem,
            "steps": [],
            "started_at": datetime.now().isoformat()
        }
        
        step1 = await self._step_understand(problem)
        chain["steps"].append(step1)
        
        step2 = await self._step_decompose(problem, step1)
        chain["steps"].append(step2)
        
        step3 = await self._step_analyze(step2, context)
        chain["steps"].append(step3)
        
        step4 = await self._step_synthesize(step3)
        chain["steps"].append(step4)
        
        conclusion = await self._step_conclude(chain["steps"])
        chain["conclusion"] = conclusion
        chain["completed_at"] = datetime.now().isoformat()
        
        self.thought_chains.append(chain)
        
        return chain
    
    async def _step_understand(self, problem: str) -> Dict:
        """Step 1: Understand the problem"""
        keywords = self._extract_keywords(problem)
        entities = self._extract_entities(problem)
        
        return {
            "step": "understand",
            "thought": f"First, I need to understand what '{problem[:50]}...' is asking",
            "keywords": keywords,
            "entities": entities,
            "problem_type": self._classify_problem(problem)
        }
    
    async def _step_decompose(self, problem: str, understanding: Dict) -> Dict:
        """Step 2: Decompose into sub-problems"""
        sub_problems = self._break_down_problem(problem, understanding)
        
        return {
            "step": "decompose",
            "thought": "Breaking down the problem into smaller parts",
            "sub_problems": sub_problems,
            "dependencies": self._find_dependencies(sub_problems)
        }
    
    async def _step_analyze(self, decomposition: Dict, context: Dict) -> Dict:
        """Step 3: Analyze each sub-problem"""
        analyses = []
        
        for sub_problem in decomposition["sub_problems"]:
            analysis = {
                "sub_problem": sub_problem,
                "relevant_context": self._find_relevant_context(sub_problem, context),
                "possible_approaches": self._generate_approaches(sub_problem),
                "complexity": self._estimate_complexity(sub_problem)
            }
            analyses.append(analysis)
        
        return {
            "step": "analyze",
            "thought": "Analyzing each sub-problem individually",
            "analyses": analyses
        }
    
    async def _step_synthesize(self, analysis: Dict) -> Dict:
        """Step 4: Synthesize solutions"""
        solutions = []
        
        for item in analysis["analyses"]:
            best_approach = self._select_best_approach(item["possible_approaches"])
            solutions.append({
                "sub_problem": item["sub_problem"],
                "solution": best_approach,
                "confidence": self._calculate_confidence(item)
            })
        
        return {
            "step": "synthesize",
            "thought": "Combining solutions for each sub-problem",
            "solutions": solutions
        }
    
    async def _step_conclude(self, steps: List[Dict]) -> Dict:
        """Step 5: Draw conclusion"""
        synthesis = next((s for s in steps if s["step"] == "synthesize"), None)
        
        if not synthesis:
            return {
                "action": "unknown",
                "confidence": 0.0,
                "reasoning": "Could not complete reasoning chain"
            }
        
        solutions = synthesis.get("solutions", [])
        
        if not solutions:
            return {
                "action": "gather_more_information",
                "confidence": 0.3,
                "reasoning": "Insufficient information to proceed"
            }
        
        avg_confidence = sum(s["confidence"] for s in solutions) / len(solutions)
        
        return {
            "action": solutions[0]["solution"] if solutions else "unknown",
            "confidence": round(avg_confidence, 3),
            "reasoning": f"Based on analysis of {len(solutions)} sub-problems",
            "solutions": solutions
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
                     "have", "has", "had", "do", "does", "did", "will", "would", "could",
                     "should", "may", "might", "must", "can", "to", "of", "in", "for",
                     "on", "with", "at", "by", "from", "as", "into", "through", "during"}
        
        words = text.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return list(set(keywords))[:10]
    
    def _extract_entities(self, text: str) -> List[Dict]:
        """Extract entities from text"""
        entities = []
        
        words = text.split()
        for word in words:
            if word.startswith("http"):
                entities.append({"type": "url", "value": word})
            elif "." in word and not word.endswith("."):
                entities.append({"type": "domain", "value": word})
            elif word.isdigit():
                entities.append({"type": "number", "value": word})
                
        return entities
    
    def _classify_problem(self, problem: str) -> str:
        """Classify the type of problem"""
        problem_lower = problem.lower()
        
        if any(kw in problem_lower for kw in ["how", "what is the best way"]):
            return "procedural"
        elif any(kw in problem_lower for kw in ["why", "explain"]):
            return "explanatory"
        elif any(kw in problem_lower for kw in ["find", "discover", "identify"]):
            return "discovery"
        else:
            return "general"
    
    def _break_down_problem(self, problem: str, understanding: Dict) -> List[str]:
        """Break down problem into sub-problems"""
        keywords = understanding.get("keywords", [])
        
        sub_problems = []
        
        if "scan" in keywords:
            sub_problems.append("Determine target scope")
            sub_problems.append("Select scanning techniques")
            sub_problems.append("Execute scan")
            
        elif "exploit" in keywords:
            sub_problems.append("Identify vulnerability")
            sub_problems.append("Find appropriate exploit")
            sub_problems.append("Execute exploitation")
            
        elif "analyze" in keywords:
            sub_problems.append("Gather data")
            sub_problems.append("Process data")
            sub_problems.append("Draw conclusions")
            
        else:
            sub_problems.append("Understand requirements")
            sub_problems.append("Plan approach")
            sub_problems.append("Execute plan")
            
        return sub_problems
    
    def _find_dependencies(self, sub_problems: List[str]) -> List[Dict]:
        """Find dependencies between sub-problems"""
        dependencies = []
        
        for i, problem in enumerate(sub_problems[1:], 1):
            dependencies.append({
                "from": sub_problems[i-1],
                "to": problem,
                "type": "sequential"
            })
            
        return dependencies
    
    def _find_relevant_context(self, sub_problem: str, context: Dict) -> Dict:
        """Find context relevant to sub-problem"""
        return {
            "has_context": bool(context.get("current")),
            "context_keys": list(context.get("current", {}).keys())[:5]
        }
    
    def _generate_approaches(self, sub_problem: str) -> List[str]:
        """Generate possible approaches"""
        return [
            f"Standard approach for {sub_problem}",
            f"Alternative approach for {sub_problem}",
            f"Fallback approach for {sub_problem}"
        ]
    
    def _estimate_complexity(self, sub_problem: str) -> str:
        """Estimate complexity of sub-problem"""
        if any(kw in sub_problem.lower() for kw in ["exploit", "attack", "complex"]):
            return "high"
        elif any(kw in sub_problem.lower() for kw in ["scan", "identify", "find"]):
            return "medium"
        else:
            return "low"
    
    def _select_best_approach(self, approaches: List[str]) -> str:
        """Select best approach from options"""
        return approaches[0] if approaches else "unknown"
    
    def _calculate_confidence(self, analysis: Dict) -> float:
        """Calculate confidence for a solution"""
        base = 0.7
        
        if analysis.get("relevant_context", {}).get("has_context"):
            base += 0.15
            
        complexity = analysis.get("complexity", "medium")
        if complexity == "low":
            base += 0.1
        elif complexity == "high":
            base -= 0.1
            
        return min(base, 0.95)
