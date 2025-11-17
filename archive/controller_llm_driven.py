"""
LLM-Driven Controller for Trading Analysis

This module implements a fully LLM-controlled trading analysis system.
The controller makes all strategic decisions using LLM reasoning:
- Which agents to call
- How to execute them (parallel/sequential)
- How to evaluate results
- Whether to conduct debates
- Final investment decision

Design Philosophy:
- No hardcoded workflow graphs
- LLM controls the entire decision-making process
- Complete trajectory tracking for future RL training
- Flexible and interpretable
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .llm import LLMClient
from .models import (
    AnalysisRequest,
    AgentProposal,
    FinalDecision,
    ControllerPlan,
    EvaluationResult,
    DebateRecord,
    Trajectory
)


class LLMController:
    """
    Fully LLM-driven controller for trading analysis.
    
    The controller orchestrates the entire analysis workflow using LLM reasoning
    at each decision point, rather than following a fixed graph structure.
    """
    
    def __init__(
        self,
        llm_client: LLMClient,
        agents: Dict[str, Any],
        max_debate_rounds: int = 2,
        enable_parallel: bool = True,
        verbose: bool = False
    ):
        """
        Initialize the LLM controller.
        
        Args:
            llm_client: LLM client for controller reasoning
            agents: Dictionary of available agents {name: agent_instance}
            max_debate_rounds: Maximum rounds of debate allowed
            enable_parallel: Whether to execute agents in parallel
            verbose: Whether to print detailed logs
        """
        self.llm = llm_client
        self.agents = agents
        self.max_debate_rounds = max_debate_rounds
        self.enable_parallel = enable_parallel
        self.verbose = verbose
        
        # Trajectory tracking for RL
        self.trajectory = Trajectory()
    
    async def analyze(self, request: AnalysisRequest) -> Tuple[FinalDecision, Trajectory]:
        """
        Main analysis workflow controlled by LLM.
        
        Args:
            request: Analysis request with symbol, horizon, context
            
        Returns:
            Tuple of (final decision, complete trajectory)
        """
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Starting LLM-Driven Analysis: {request.symbol}")
            print(f"{'='*60}\n")
        
        # Step 1: Create analysis plan
        plan = await self._create_plan(request)
        self._log_step("plan", plan)
        
        # Step 2: Execute agents according to plan
        agent_results = await self._execute_agents(plan, request)
        self._log_step("agent_execution", agent_results)
        
        # Step 3: Evaluate results and detect conflicts
        evaluation = await self._evaluate_results(agent_results, request)
        self._log_step("evaluation", evaluation)
        
        # Step 4: Conduct debate if needed
        if evaluation.has_conflict and evaluation.recommend_debate:
            if self.verbose:
                print("\nConflict detected - Starting debate process...")
            
            agent_results = await self._conduct_debate(
                agent_results, evaluation, request
            )
            self._log_step("debate_results", agent_results)
        
        # Step 5: Make final decision
        decision = await self._make_final_decision(
            agent_results, evaluation, request
        )
        self._log_step("final_decision", decision)
        
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Analysis Complete: {decision.recommendation} (confidence: {decision.confidence:.2f})")
            print(f"{'='*60}\n")
        
        return decision, self.trajectory
    
    async def _create_plan(self, request: AnalysisRequest) -> ControllerPlan:
        """
        Use LLM to create analysis plan.
        
        The LLM decides:
        - Which agents to use
        - Execution order (parallel or sequential)
        - Specific tasks for each agent
        """
        prompt = f"""You are an expert trading analysis coordinator. Create an optimal analysis plan.

TASK: Analyze {request.symbol} for {request.horizon} investment decision
MARKET CONTEXT: {request.market_context or 'General market conditions'}

AVAILABLE ANALYSTS:
1. news - Analyzes news events, sentiment, and market-moving announcements
2. technical - Analyzes price action, technical indicators, and chart patterns  
3. fundamental - Analyzes financial metrics, valuation, and business fundamentals

INSTRUCTIONS:
1. Decide which analysts are most relevant for this task
2. Determine execution strategy (parallel or sequential)
3. Specify what each analyst should focus on

OUTPUT FORMAT (JSON):
{{
    "selected_agents": ["news", "technical", "fundamental"],
    "execution_mode": "parallel",
    "agent_tasks": {{
        "news": "Focus on recent earnings announcements and sector trends",
        "technical": "Analyze momentum and support/resistance levels",
        "fundamental": "Evaluate valuation relative to sector peers"
    }},
    "reasoning": "Brief explanation of plan"
}}

Be strategic - you don't always need all three analysts."""

        response = await self.llm.complete([
            {"role": "system", "content": "You are a strategic trading analysis coordinator."},
            {"role": "user", "content": prompt}
        ])
        
        plan_data = self._parse_json_response(response)
        
        # Validate and filter agents
        selected = [a for a in plan_data.get("selected_agents", []) if a in self.agents]
        if not selected:
            selected = list(self.agents.keys())  # Fallback: use all
        
        plan = ControllerPlan(
            selected_agents=selected,
            execution_mode=plan_data.get("execution_mode", "parallel"),
            agent_tasks=plan_data.get("agent_tasks", {}),
            reasoning=plan_data.get("reasoning", "")
        )
        
        if self.verbose:
            print(f"[PLAN] Selected agents: {', '.join(plan.selected_agents)}")
            print(f"[PLAN] Execution mode: {plan.execution_mode}")
            print(f"[PLAN] Reasoning: {plan.reasoning}\n")
        
        return plan
    
    async def _fetch_all_data_for_controller(self, request: AnalysisRequest) -> str:
        """
        Fetch all available data for controller to analyze.
        Controller sees the data first to make intelligent decisions.
        
        Returns:
            Formatted string with all available data
        """
        data_sections = []
        
        # Fetch from all agent tools
        for agent_name, agent in self.agents.items():
            if hasattr(agent, 'data_tools') and agent.data_tools:
                for tool in agent.data_tools:
                    try:
                        import asyncio
                        result = await asyncio.to_thread(
                            tool,
                            request.symbol,
                            request.trade_date
                        )
                        data_sections.append(f"=== {tool.__name__} ===\n{result}\n")
                    except Exception as e:
                        data_sections.append(f"=== {tool.__name__} ===\nError: {str(e)}\n")
        
        return "\n".join(data_sections)
    
    async def _generate_dynamic_agent_instructions(
        self,
        plan: ControllerPlan,
        all_data: str,
        request: AnalysisRequest
    ) -> Dict[str, Dict[str, str]]:
        """
        Controller analyzes data and generates COMPLETE instructions for each agent.
        
        NEW: Generates both system prompts AND specific tasks for each agent.
        Controller has FULL control over agent behavior.
        
        Returns:
            Dictionary of {agent_name: {
                "system_prompt": "Dynamic role and guidelines",
                "specific_task": "What to analyze in this case",
                "data_focus": "Which parts of data to focus on"
            }}
        """
        prompt = f"""You are the MASTER CONTROLLER analyzing {request.symbol} for a {request.horizon} investment decision.

You have ALL the market data. Your job is to FULLY CONTROL your specialist agents by giving them:
1. Their role and decision-making guidelines (system prompt)
2. Specific analysis task
3. Which data to focus on

=== AVAILABLE DATA ===
{all_data[:3000]}  

=== SELECTED AGENTS ===
{', '.join(plan.selected_agents)}

TASK: For EVERY agent, you MUST generate COMPLETE instructions including:

1. **System Prompt** (REQUIRED): Define their COMPLETE role, expertise, and ALL decision rules for THIS specific case
   - Include their expertise area (news/technical/fundamental analyst)
   - BE SPECIFIC: Reference actual data values (e.g., "RSI is at 37.38, which is oversold")
   - PROVIDE CLEAR RULES: Tell them exactly what to do (e.g., "RSI < 40 suggests BUY, RSI > 70 suggests SELL")
   - BE DIRECTIVE: Give clear thresholds based on the actual data you see
   - PUSH FOR ACTION: Tell them when to recommend BUY/SELL vs HOLD based on data

2. **Specific Task** (REQUIRED): What exact question they need to answer

3. **Data Focus** (REQUIRED): Which specific metrics/news/indicators to prioritize

EXAMPLE for a news agent if you see positive news:
{{
    "news": {{
        "system_prompt": "You are a NEWS SENTIMENT ANALYST. Today's news shows a Citi upgrade maintaining AAPL as top pick. DECISION RULES: Strong positive analyst upgrades from reputable sources (like Citi) indicate BUY signal with conviction 0.7-0.8. Positive AI-related growth news adds +0.1 to conviction. Only recommend HOLD if news is mixed or neutral. Provide clear BUY/SELL recommendations when news is clearly positive/negative.",
        "specific_task": "Evaluate the trading impact of Citi's reaffirmation and AI growth potential on short-term price action",
        "data_focus": "Citi upgrade analysis, AI market expansion, analyst confidence"
    }}
}}

OUTPUT FORMAT (JSON):
{{
    "news": {{
        "system_prompt": "Complete role + decision rules for THIS case",
        "specific_task": "Exact question to answer",
        "data_focus": "What data to focus on"
    }},
    "technical": {{
        "system_prompt": "Complete role + decision rules for THIS case with actual indicator values",
        "specific_task": "Exact question to answer",  
        "data_focus": "Which indicators to prioritize"
    }},
    "fundamental": {{
        "system_prompt": "Complete role + decision rules for THIS case with actual valuation metrics",
        "specific_task": "Exact question to answer",
        "data_focus": "Which metrics to focus on"
    }},
    "controller_reasoning": "Your strategic reasoning for these specific instructions"
}}

CRITICAL REQUIREMENTS:
- EVERY agent MUST have a complete system_prompt with decision rules
- System prompts MUST reference actual data values you see above
- System prompts MUST include clear BUY/SELL/HOLD criteria for this specific case
- NO generic prompts - make them case-specific!
Only include instructions for selected agents: {plan.selected_agents}"""

        response = await self.llm.complete([
            {"role": "system", "content": "You are the master controller with full authority over agent behavior."},
            {"role": "user", "content": prompt}
        ], max_tokens=1500)
        
        instructions = self._parse_json_response(response)
        
        if self.verbose:
            print(f"[CONTROLLER] Generated complete agent instructions (system prompts + tasks)")
            if "controller_reasoning" in instructions:
                print(f"[CONTROLLER] Reasoning: {instructions['controller_reasoning'][:200]}...\n")
        
        return instructions
    
    async def _execute_agents(
        self, 
        plan: ControllerPlan, 
        request: AnalysisRequest
    ) -> Dict[str, AgentProposal]:
        """
        Execute agents with FULL controller control.
        
        REVOLUTIONARY APPROACH:
        1. Controller fetches ALL data ONCE
        2. Controller analyzes data and generates COMPLETE instructions for each agent
           - Dynamic system prompts (role + decision rules based on THIS data)
           - Specific tasks
           - Data focus areas
        3. Agents receive: preloaded data + dynamic system prompt + specific task
        4. Agents just execute instructions (become simple tools)
        
        Controller is now the TRUE brain!
        
        Args:
            plan: Analysis plan from LLM
            request: Analysis request
            
        Returns:
            Dictionary of agent proposals
        """
        # Step 1: Fetch all data for controller (ONCE)
        if self.verbose:
            print(f"[CONTROLLER] Fetching all data...")
        
        all_data = await self._fetch_all_data_for_controller(request)
        
        # Step 2: Controller generates COMPLETE instructions (system prompts + tasks)
        instructions = await self._generate_dynamic_agent_instructions(plan, all_data, request)
        
        # Step 3: Execute agents with full controller control
        results = {}
        
        if plan.execution_mode == "parallel" and self.enable_parallel:
            # Execute all agents in parallel with controller instructions
            tasks = []
            for agent_name in plan.selected_agents:
                agent = self.agents[agent_name]
                agent_instructions = instructions.get(agent_name, {})
                
                # Extract controller-generated components
                dynamic_system_prompt = agent_instructions.get("system_prompt")
                specific_task = agent_instructions.get("specific_task")
                
                tasks.append(self._run_agent_safe(
                    agent, 
                    request, 
                    specific_task=specific_task,
                    preloaded_data=all_data,
                    dynamic_system_prompt=dynamic_system_prompt
                ))
            
            proposals = await asyncio.gather(*tasks)
            results = {p.agent: p for p in proposals if p is not None}
            
        else:
            # Execute agents sequentially
            for agent_name in plan.selected_agents:
                agent = self.agents[agent_name]
                agent_instructions = instructions.get(agent_name, {})
                
                dynamic_system_prompt = agent_instructions.get("system_prompt")
                specific_task = agent_instructions.get("specific_task")
                
                proposal = await self._run_agent_safe(
                    agent, 
                    request, 
                    specific_task=specific_task,
                    preloaded_data=all_data,
                    dynamic_system_prompt=dynamic_system_prompt
                )
                if proposal:
                    results[agent_name] = proposal
        
        if self.verbose:
            print(f"[EXECUTION] Completed {len(results)} agent analyses with dynamic control\n")
        
        return results
    
    async def _run_agent_safe(
        self, 
        agent: Any, 
        request: AnalysisRequest,
        specific_task: Optional[str] = None,
        preloaded_data: Optional[str] = None,
        dynamic_system_prompt: Optional[str] = None
    ) -> Optional[AgentProposal]:
        """
        Run agent with full controller control and error handling.
        
        NEW: Passes preloaded data and dynamic system prompt to agent.
        
        Args:
            agent: Agent instance
            request: Analysis request
            specific_task: Controller-generated specific task
            preloaded_data: Controller-fetched data (avoids redundant fetching)
            dynamic_system_prompt: Controller-generated system prompt
            
        Returns:
            Agent proposal or None if failed
        """
        try:
            proposal = await agent.analyze(
                request, 
                specific_task=specific_task,
                preloaded_data=preloaded_data,
                dynamic_system_prompt=dynamic_system_prompt
            )
            if self.verbose:
                mode = "DYNAMIC" if dynamic_system_prompt else "DEFAULT"
                print(f"[{agent.name.upper()} - {mode}] {proposal.action} (conviction: {proposal.conviction:.2f})")
            return proposal
        except Exception as e:
            if self.verbose:
                print(f"[{agent.name.upper()}] FAILED: {str(e)}")
            
            # Return neutral proposal on failure
            return AgentProposal(
                agent=agent.name,
                action="HOLD",
                conviction=0.0,
                thesis=f"Analysis failed: {str(e)}",
                evidence=[],
                neutral=True
            )
    
    async def _evaluate_results(
        self, 
        agent_results: Dict[str, AgentProposal],
        request: AnalysisRequest
    ) -> EvaluationResult:
        """
        Use LLM to evaluate agent results and detect conflicts.
        
        Args:
            agent_results: Proposals from agents
            request: Original request
            
        Returns:
            Evaluation with conflict detection and recommendations
        """
        # Format agent results for LLM
        results_summary = []
        for name, proposal in agent_results.items():
            results_summary.append({
                "agent": name,
                "action": proposal.action,
                "conviction": proposal.conviction,
                "thesis": proposal.thesis,
                "evidence_count": len(proposal.evidence)
            })
        
        prompt = f"""Evaluate the following trading analysis results for {request.symbol}.

AGENT PROPOSALS:
{json.dumps(results_summary, indent=2)}

DETAILED ANALYSIS:
{self._format_proposals_detail(agent_results)}

EVALUATION TASKS:
1. Identify any conflicts between agents (e.g., BUY vs SELL recommendations)
2. Assess the strength and credibility of each proposal
3. Determine if debate would help resolve conflicts
4. Identify consensus points

OUTPUT FORMAT (JSON):
{{
    "has_conflict": true/false,
    "conflict_description": "Description of conflicts",
    "recommend_debate": true/false,
    "debate_focus": "What should be debated",
    "consensus_points": ["List of points where agents agree"],
    "credibility_ranking": {{"agent_name": score_0_to_1}},
    "reasoning": "Your evaluation reasoning"
}}"""

        response = await self.llm.complete([
            {"role": "system", "content": "You are an expert at evaluating trading analyses and identifying conflicts."},
            {"role": "user", "content": prompt}
        ])
        
        eval_data = self._parse_json_response(response)
        
        evaluation = EvaluationResult(
            has_conflict=eval_data.get("has_conflict", False),
            conflict_description=eval_data.get("conflict_description", ""),
            recommend_debate=eval_data.get("recommend_debate", False),
            debate_focus=eval_data.get("debate_focus", ""),
            consensus_points=eval_data.get("consensus_points", []),
            credibility_ranking=eval_data.get("credibility_ranking", {}),
            reasoning=eval_data.get("reasoning", "")
        )
        
        if self.verbose and evaluation.has_conflict:
            print(f"[EVALUATION] Conflict detected: {evaluation.conflict_description}")
            print(f"[EVALUATION] Recommend debate: {evaluation.recommend_debate}\n")
        
        return evaluation
    
    async def _conduct_debate(
        self,
        agent_results: Dict[str, AgentProposal],
        evaluation: EvaluationResult,
        request: AnalysisRequest
    ) -> Dict[str, AgentProposal]:
        """
        LLM-moderated debate between conflicting agents.
        
        Args:
            agent_results: Current agent proposals
            evaluation: Evaluation showing conflicts
            request: Original request
            
        Returns:
            Updated agent proposals after debate
        """
        debate_history = []
        current_results = dict(agent_results)
        
        for round_num in range(self.max_debate_rounds):
            if self.verbose:
                print(f"\n[DEBATE] Round {round_num + 1}/{self.max_debate_rounds}")
            
            # Generate debate guidance from LLM
            guidance = await self._generate_debate_guidance(
                current_results, evaluation, debate_history, round_num
            )
            
            if self.verbose:
                print(f"[DEBATE] Focus: {guidance['focus']}")
            
            # Have agents respond to debate
            updated_results = await self._agent_rebuttals(
                current_results, guidance, request
            )
            
            # Record debate round
            debate_history.append({
                "round": round_num + 1,
                "guidance": guidance,
                "results": {k: v.to_dict() for k, v in updated_results.items()}
            })
            
            # Check for convergence
            if self._check_convergence(current_results, updated_results):
                if self.verbose:
                    print(f"[DEBATE] Converged after round {round_num + 1}")
                break
            
            current_results = updated_results
        
        # Log debate record
        self._log_step("debate", DebateRecord(
            rounds=len(debate_history),
            history=debate_history,
            converged=self._check_convergence(agent_results, current_results)
        ))
        
        return current_results
    
    async def _generate_debate_guidance(
        self,
        results: Dict[str, AgentProposal],
        evaluation: EvaluationResult,
        history: List[Dict],
        round_num: int
    ) -> Dict[str, Any]:
        """
        Generate LLM guidance for debate round.
        """
        prompt = f"""You are moderating a debate between trading analysts.

CURRENT POSITIONS:
{self._format_proposals_detail(results)}

CONFLICT: {evaluation.conflict_description}
FOCUS AREA: {evaluation.debate_focus}

PREVIOUS DEBATE ROUNDS: {len(history)}

Generate guidance for debate round {round_num + 1}:
1. What specific points should be debated?
2. Which agents should respond to which arguments?
3. What evidence or data would help resolve conflicts?

OUTPUT FORMAT (JSON):
{{
    "focus": "Main focus for this round",
    "questions": ["Specific questions to address"],
    "agent_instructions": {{"agent_name": "What this agent should focus on"}}
}}"""

        response = await self.llm.complete([
            {"role": "system", "content": "You are an expert debate moderator for trading analysis."},
            {"role": "user", "content": prompt}
        ])
        
        return self._parse_json_response(response)
    
    async def _agent_rebuttals(
        self,
        current_results: Dict[str, AgentProposal],
        guidance: Dict[str, Any],
        request: AnalysisRequest
    ) -> Dict[str, AgentProposal]:
        """
        Get agent rebuttals in debate.
        """
        updated = {}
        
        # Prepare context for each agent
        for agent_name, current_proposal in current_results.items():
            agent = self.agents.get(agent_name)
            if not agent:
                continue
            
            # Get other agents' positions
            peer_proposals = {k: v for k, v in current_results.items() if k != agent_name}
            
            # Get specific instruction for this agent
            instruction = guidance.get("agent_instructions", {}).get(agent_name, "")
            
            try:
                # Agent responds to debate
                revised_proposal = await agent.debate(
                    initial_proposal=current_proposal,
                    peer_proposals=peer_proposals,
                    debate_focus=guidance.get("focus", ""),
                    specific_instruction=instruction,
                    request=request
                )
                
                updated[agent_name] = revised_proposal
                
                if self.verbose:
                    action_changed = revised_proposal.action != current_proposal.action
                    conv_change = revised_proposal.conviction - current_proposal.conviction
                    print(f"  [{agent_name.upper()}] " + 
                          f"{'Changed to ' + revised_proposal.action if action_changed else revised_proposal.action} " +
                          f"(Δconv: {conv_change:+.2f})")
                
            except Exception as e:
                if self.verbose:
                    print(f"  [{agent_name.upper()}] Debate failed: {str(e)}")
                updated[agent_name] = current_proposal  # Keep original
        
        return updated
    
    async def _make_final_decision(
        self,
        agent_results: Dict[str, AgentProposal],
        evaluation: EvaluationResult,
        request: AnalysisRequest
    ) -> FinalDecision:
        """
        LLM makes final investment decision.
        
        Args:
            agent_results: Final agent proposals
            evaluation: Evaluation result
            request: Original request
            
        Returns:
            Final decision with recommendation and confidence
        """
        prompt = f"""Make the final investment decision for {request.symbol} ({request.horizon} horizon).

ANALYST RECOMMENDATIONS:
{self._format_proposals_detail(agent_results)}

EVALUATION:
- Conflicts: {evaluation.conflict_description or 'None'}
- Consensus: {', '.join(evaluation.consensus_points) if evaluation.consensus_points else 'None'}
- Credibility ranking: {json.dumps(evaluation.credibility_ranking, indent=2)}

MARKET CONTEXT: {request.market_context or 'N/A'}

DECISION REQUIREMENTS:
1. Recommendation: BUY, SELL, or HOLD
2. Confidence: 0.0 to 1.0 (based on agreement and evidence strength)
3. Detailed rationale explaining the decision
4. Key risks and caveats
5. Weight given to each analyst

OUTPUT FORMAT (JSON):
{{
    "recommendation": "BUY/SELL/HOLD",
    "confidence": 0.75,
    "rationale": "Detailed explanation",
    "key_factors": ["Factor 1", "Factor 2"],
    "risks": ["Risk 1", "Risk 2"],
    "agent_weights": {{"agent_name": weight_0_to_1}},
    "reasoning_process": "How you arrived at this decision"
}}

CRITICAL DECISION PRINCIPLES:
- Trust your analysts - they are experts who have analyzed the data
- If 2+ analysts agree on BUY/SELL, strongly consider following their recommendation
- Higher agreement = higher confidence
- HOLD should ONLY be used when analysts are genuinely split or all recommend HOLD
- Don't default to HOLD just to be "safe" - that defeats the purpose of analysis
- Conflicting signals = evaluate which analyst has stronger evidence, don't just pick HOLD
- If one analyst says BUY with high conviction (>0.7) and others are neutral, lean BUY
- If one analyst says SELL with high conviction (>0.7) and others are neutral, lean SELL
- Strong evidence from multiple sources = higher confidence and should override neutrality"""

        response = await self.llm.complete([
            {"role": "system", "content": "You are an expert portfolio manager making final investment decisions."},
            {"role": "user", "content": prompt}
        ])
        
        decision_data = self._parse_json_response(response)
        
        decision = FinalDecision(
            symbol=request.symbol,
            horizon=request.horizon,
            recommendation=decision_data.get("recommendation", "HOLD"),
            confidence=float(decision_data.get("confidence", 0.5)),
            rationale=decision_data.get("rationale", ""),
            key_factors=decision_data.get("key_factors", []),
            risks=decision_data.get("risks", []),
            agent_weights=decision_data.get("agent_weights", {}),
            agent_proposals=agent_results,
            evaluation=evaluation,
            timestamp=datetime.utcnow().isoformat()
        )
        
        return decision
    
    def _check_convergence(
        self,
        before: Dict[str, AgentProposal],
        after: Dict[str, AgentProposal]
    ) -> bool:
        """
        Check if agents have converged (no more conflicts).
        """
        # Get unique actions (excluding HOLD)
        before_actions = {p.action for p in before.values() if p.action != "HOLD"}
        after_actions = {p.action for p in after.values() if p.action != "HOLD"}
        
        # Converged if all actionable agents agree
        return len(after_actions) <= 1
    
    def _format_proposals_detail(self, proposals: Dict[str, AgentProposal]) -> str:
        """Format proposals for LLM consumption."""
        lines = []
        for name, prop in proposals.items():
            lines.append(f"\n{name.upper()} ANALYST:")
            lines.append(f"  Action: {prop.action}")
            lines.append(f"  Conviction: {prop.conviction:.2f}")
            lines.append(f"  Thesis: {prop.thesis}")
            if prop.evidence:
                lines.append(f"  Evidence:")
                for ev in prop.evidence[:5]:  # Limit to top 5
                    lines.append(f"    - {ev}")
        return "\n".join(lines)
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling code blocks."""
        try:
            # Try direct parse
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON in code blocks or text
            start = response.find('{')
            end = response.rfind('}')
            if start != -1 and end != -1 and end > start:
                json_str = response[start:end+1]
                return json.loads(json_str)
            
            # Fallback: return empty dict
            return {}
    
    def _log_step(self, step_name: str, data: Any):
        """Log a step in the trajectory."""
        self.trajectory.add_step(step_name, data)
    
    def save_trajectory(self, output_dir: Path):
        """Save complete trajectory to file for RL training."""
        self.trajectory.save(output_dir)

