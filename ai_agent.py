"""
AI Agent Module for PawPal+

This module implements an Agentic Workflow AI feature that:
- Analyzes tasks and provides smart recommendations
- Generates natural language explanations for scheduling decisions
- Detects potential issues and suggests resolutions
- Plans, acts, and checks its own work
"""

import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass, field

from pawpal_system import Task, Pet, Owner, Scheduler, ScheduledTask

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class AIRecommendation:
    """Represents an AI-generated recommendation."""
    type: str  # "schedule", "priority", "conflict", "optimization"
    title: str
    description: str
    confidence: float = 0.0  # 0.0 to 1.0
    action_items: List[str] = field(default_factory=list)
    priority_score: int = 0


@dataclass
class AgentAnalysis:
    """Results from the AI agent's analysis."""
    recommendations: List[AIRecommendation] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    summary: str = ""


class PawPalAI:
    """
    AI Agent that plans, acts, and checks its own work.
    
    This implements an Agentic Workflow with the following stages:
    1. Observe - Analyze current state of tasks and schedule
    2. Think - Generate insights and recommendations
    3. Act - Provide actionable suggestions
    4. Check - Verify recommendations make sense
    """
    
    def __init__(self, scheduler: Scheduler):
        self.scheduler = scheduler
        self.owner = scheduler.owner
        self.analysis: Optional[AgentAnalysis] = None
        logger.info(f"Initialized PawPalAI for owner: {self.owner.name}")
    
    def observe(self) -> AgentAnalysis:
        """
        Stage 1: Observe - Analyze current state.
        
        Returns:
            AgentAnalysis with current state insights
        """
        logger.info("AI Agent: Observing current state...")
        
        analysis = AgentAnalysis()
        all_tasks = self.owner.get_all_tasks(include_completed=True)
        pending_tasks = self.owner.get_all_tasks(include_completed=False)
        
        # Analyze task distribution
        task_by_priority = {"high": 0, "medium": 0, "low": 0}
        task_by_type = {}
        overdue_count = 0
        
        now = datetime.now()
        for task in pending_tasks:
            task_by_priority[task.priority] += 1
            task_by_type[task.task_type] = task_by_type.get(task.task_type, 0) + 1
            if task.is_overdue(now):
                overdue_count += 1
        
        # Generate insights
        if overdue_count > 0:
            analysis.warnings.append(
                f"⚠️ You have {overdue_count} overdue task(s)! Consider rescheduling."
            )
        
        if task_by_priority["high"] > 3:
            analysis.insights.append(
                f"📊 High priority alert: {task_by_priority['high']} high-priority tasks pending."
            )
        
        if not pending_tasks:
            analysis.insights.append("✅ All tasks completed! Great job staying on top of pet care.")

        # Time constraint guardrail — visible warning if tasks exceed available hours
        total_minutes = sum(t.duration_minutes for t in pending_tasks)
        available_minutes = int(self.owner.available_hours * 60)
        if total_minutes > available_minutes:
            msg = (
                f"⚠️ Time Constraint: tasks need {total_minutes}min but only "
                f"{available_minutes}min available — lower-priority tasks will be dropped."
            )
            analysis.insights.append(msg)
            analysis.warnings.append(msg)

        # Task type insights
        if "walk" in task_by_type:
            analysis.insights.append(f"🚶 {task_by_type['walk']} walk task(s) scheduled - great for pet health!")
        if "feed" in task_by_type:
            analysis.insights.append(f"🍖 {task_by_type['feed']} feeding task(s) - nutrition is key!")
        
        logger.info(f"AI Agent: Observed {len(pending_tasks)} pending tasks, {overdue_count} overdue")
        return analysis
    
    def think(self) -> List[AIRecommendation]:
        """
        Stage 2: Think - Generate recommendations based on analysis.
        
        Returns:
            List of AIRecommendation objects
        """
        logger.info("AI Agent: Thinking about recommendations...")
        
        recommendations = []
        pending_tasks = self.scheduler.get_pending_tasks()
        
        # Recommendation 1: Optimize task order
        if len(pending_tasks) > 1:
            high_priority = [t for t in pending_tasks if t.priority == "high"]
            if high_priority:
                rec = AIRecommendation(
                    type="schedule",
                    title="Prioritize High-Priority Tasks",
                    description=f"You have {len(high_priority)} high-priority tasks. Consider doing these first for maximum value.",
                    confidence=0.85,
                    action_items=[
                        "Schedule high-priority tasks at your peak energy times",
                        "Break large tasks into smaller chunks if needed"
                    ],
                    priority_score=100
                )
                recommendations.append(rec)
        
        # Recommendation 2: Time management
        total_minutes = sum(t.duration_minutes for t in pending_tasks)
        available_minutes = int(self.owner.available_hours * 60)
        
        if total_minutes > available_minutes:
            rec = AIRecommendation(
                type="optimization",
                title="Time Constraint Detected",
                description=f"Your tasks require {total_minutes}min but you only have {available_minutes}min available. The scheduler will use a knapsack algorithm to maximize priority value.",
                confidence=0.95,
                action_items=[
                    "Consider reducing task durations",
                    "Lower priority of less critical tasks",
                    "Spread tasks across multiple days"
                ],
                priority_score=90
            )
            recommendations.append(rec)
        
        # Recommendation 3: Recurring task patterns
        daily_tasks = [t for t in pending_tasks if t.frequency == "daily"]
        weekly_tasks = [t for t in pending_tasks if t.frequency == "weekly"]
        
        if daily_tasks or weekly_tasks:
            rec = AIRecommendation(
                type="schedule",
                title="Recurring Task Pattern",
                description=f"You have {len(daily_tasks)} daily and {len(weekly_tasks)} weekly recurring tasks. Consistency is key for pet care!",
                confidence=0.90,
                action_items=[
                    "Set reminders for recurring tasks",
                    "Consider batching similar tasks"
                ],
                priority_score=70
            )
            recommendations.append(rec)
        
        # Recommendation 4: Pet-specific insights
        for pet in self.owner.pets:
            pet_tasks = pet.get_tasks(include_completed=False)
            if len(pet_tasks) > 5:
                rec = AIRecommendation(
                    type="priority",
                    title=f"Busy Schedule for {pet.name}",
                    description=f"{pet.name} has {len(pet_tasks)} pending tasks. Consider if all are necessary.",
                    confidence=0.75,
                    action_items=[
                        f"Review {pet.name}'s task list",
                        "Remove completed or outdated tasks"
                    ],
                    priority_score=60
                )
                recommendations.append(rec)
        
        # Sort by priority score
        recommendations.sort(key=lambda x: x.priority_score, reverse=True)
        
        logger.info(f"AI Agent: Generated {len(recommendations)} recommendations")
        return recommendations
    
    def act(self, recommendations: List[AIRecommendation]) -> str:
        """
        Stage 3: Act - Generate natural language summary and action plan.
        
        Args:
            recommendations: List of recommendations to act on
            
        Returns:
            Natural language summary of actions to take
        """
        logger.info("AI Agent: Acting on recommendations...")
        
        if not recommendations:
            return "✅ Your schedule looks optimal! No specific recommendations at this time."
        
        summary_parts = []
        summary_parts.append("## 🤖 AI Analysis & Recommendations\n")
        
        for i, rec in enumerate(recommendations, 1):
            summary_parts.append(f"### {i}. {rec.title}")
            summary_parts.append(f"**Confidence:** {rec.confidence*100:.0f}%")
            summary_parts.append(f"\n{rec.description}\n")
            
            if rec.action_items:
                summary_parts.append("**Suggested Actions:**")
                for action in rec.action_items:
                    summary_parts.append(f"- {action}")
            summary_parts.append("")
        
        result = "\n".join(summary_parts)
        logger.info("AI Agent: Action plan generated")
        return result
    
    def check(self, plan: List[ScheduledTask]) -> Tuple[bool, List[str]]:
        """
        Stage 4: Check - Verify the generated plan makes sense.
        
        Args:
            plan: The scheduled plan to verify
            
        Returns:
            Tuple of (is_valid, issues_found)
        """
        logger.info("AI Agent: Checking plan validity...")
        
        issues = []
        
        if not plan:
            issues.append("No tasks were scheduled. Either no tasks exist or they exceed available time.")
            return False, issues
        
        # Check for gaps in schedule
        for i in range(len(plan) - 1):
            current_end = plan[i].end_time
            next_start = plan[i + 1].start_time
            gap_minutes = (next_start - current_end).total_seconds() / 60
            
            if gap_minutes > 30:
                issues.append(f"Large gap of {int(gap_minutes)}min between '{plan[i].task.title}' and '{plan[i+1].task.title}'")
        
        # Check priority distribution
        priority_counts = {"high": 0, "medium": 0, "low": 0}
        for item in plan:
            priority_counts[item.task.priority] += 1
        
        if priority_counts["high"] == 0 and len(plan) > 2:
            issues.append("Warning: No high-priority tasks in schedule. Consider if urgent tasks exist.")
        
        # Check total time utilization
        total_scheduled = sum(item.duration() for item in plan)
        available = self.owner.available_hours * 60
        utilization = total_scheduled / available if available > 0 else 0
        
        if utilization < 0.5:
            issues.append(f"Low time utilization: only {utilization*100:.0f}% of available time used.")
        elif utilization > 0.95:
            issues.append("Very high utilization! Consider leaving buffer for unexpected tasks.")
        
        is_valid = len(issues) == 0
        if is_valid:
            logger.info("AI Agent: Plan validation passed")
        else:
            logger.warning(f"AI Agent: Plan validation found {len(issues)} issues")
        
        return is_valid, issues
    
    def run_agentic_workflow(self) -> AgentAnalysis:
        """
        Execute the full agentic workflow: Observe → Think → Act → Check.
        
        Returns:
            AgentAnalysis with complete results
        """
        logger.info("Starting agentic workflow...")
        
        # Stage 1: Observe
        analysis = self.observe()
        
        # Stage 2: Think
        recommendations = self.think()
        analysis.recommendations = recommendations
        
        # Stage 3: Act (store in summary)
        analysis.summary = self.act(recommendations)
        
        # Stage 4: Check (on current plan if exists)
        if self.scheduler.scheduled_items:
            is_valid, issues = self.check(self.scheduler.scheduled_items)
            analysis.warnings.extend(issues)
        
        self.analysis = analysis
        logger.info("Agentic workflow complete")
        return analysis
    
    def generate_plan_explanation(self, plan: List[ScheduledTask]) -> str:
        """
        Generate a natural language explanation of the schedule.
        
        Args:
            plan: The scheduled tasks
            
        Returns:
            Human-readable explanation
        """
        if not plan:
            return "No tasks were scheduled."
        
        lines = []
        lines.append("## 📋 Schedule Explanation\n")
        
        # Group by time blocks
        morning_tasks = [p for p in plan if p.start_time.hour < 12]
        afternoon_tasks = [p for p in plan if 12 <= p.start_time.hour < 17]
        evening_tasks = [p for p in plan if p.start_time.hour >= 17]
        
        if morning_tasks:
            lines.append("### 🌅 Morning")
            for item in morning_tasks:
                lines.append(f"- **{item.start_time.strftime('%H:%M')}** - {item.task.title} for {item.pet.name} ({item.task.duration_minutes}min, {item.task.priority} priority)")
        
        if afternoon_tasks:
            lines.append("### ☀️ Afternoon")
            for item in afternoon_tasks:
                lines.append(f"- **{item.start_time.strftime('%H:%M')}** - {item.task.title} for {item.pet.name} ({item.task.duration_minutes}min, {item.task.priority} priority)")
        
        if evening_tasks:
            lines.append("### 🌙 Evening")
            for item in evening_tasks:
                lines.append(f"- **{item.start_time.strftime('%H:%M')}** - {item.task.title} for {item.pet.name} ({item.task.duration_minutes}min, {item.task.priority} priority)")
        
        # Add reasoning
        lines.append("\n### 💡 Why this schedule?")
        lines.append(self.scheduler.explanation)
        
        # Add AI insights
        if self.analysis and self.analysis.insights:
            lines.append("\n### 🔍 AI Insights")
            for insight in self.analysis.insights:
                lines.append(f"- {insight}")
        
        return "\n".join(lines)


def create_ai_agent(scheduler: Scheduler) -> PawPalAI:
    """
    Factory function to create an AI agent for a scheduler.
    
    Args:
        scheduler: The scheduler to analyze
        
    Returns:
        PawPalAI instance
    """
    return PawPalAI(scheduler)