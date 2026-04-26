"""
Tests for the AI Agent Module

These tests verify the Agentic Workflow AI feature:
- Observe: Analyze current state of tasks and schedule
- Think: Generate insights and recommendations
- Act: Provide actionable suggestions
- Check: Verify recommendations make sense
"""

import pytest
from datetime import date, datetime, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler
from ai_agent import PawPalAI, AIRecommendation, AgentAnalysis, create_ai_agent


class TestPawPalAI:
    """Test suite for the PawPalAI agent."""
    
    @pytest.fixture
    def setup_owner_with_pets(self):
        """Create a test owner with pets and tasks."""
        owner = Owner(name="Jordan", available_hours=4.0)
        pet1 = Pet(name="Mochi", species="dog", age=3)
        pet2 = Pet(name="Neko", species="cat", age=2)
        owner.add_pet(pet1)
        owner.add_pet(pet2)
        
        # Add some tasks
        pet1.add_task(Task(
            title="Morning walk",
            task_type="walk",
            duration_minutes=30,
            priority="high",
            deadline=date.today()
        ))
        pet1.add_task(Task(
            title="Feed breakfast",
            task_type="feed",
            duration_minutes=15,
            priority="high",
            deadline=date.today()
        ))
        pet2.add_task(Task(
            title="Feed dinner",
            task_type="feed",
            duration_minutes=10,
            priority="medium",
            deadline=date.today()
        ))
        
        return owner
    
    def test_ai_agent_initialization(self, setup_owner_with_pets):
        """Test that AI agent initializes correctly."""
        scheduler = Scheduler(owner=setup_owner_with_pets)
        ai = create_ai_agent(scheduler)
        
        assert isinstance(ai, PawPalAI)
        assert ai.owner.name == "Jordan"
        assert ai.scheduler is not None
    
    def test_observe_detects_overdue_tasks(self):
        """Test that observe stage detects overdue tasks."""
        owner = Owner(name="Jordan", available_hours=2.0)
        pet = Pet(name="Mochi", species="dog")
        owner.add_pet(pet)
        
        # Add an overdue task
        yesterday = date.today() - timedelta(days=1)
        pet.add_task(Task(
            title="Overdue vet visit",
            task_type="meds",
            duration_minutes=60,
            priority="high",
            deadline=yesterday
        ))
        
        scheduler = Scheduler(owner=owner)
        ai = create_ai_agent(scheduler)
        analysis = ai.observe()
        
        # Check that overdue warning was generated
        assert any("overdue" in w.lower() for w in analysis.warnings)
    
    def test_observe_generates_insights(self, setup_owner_with_pets):
        """Test that observe stage generates insights."""
        scheduler = Scheduler(owner=setup_owner_with_pets)
        ai = create_ai_agent(scheduler)
        analysis = ai.observe()
        
        # Should have insights about task distribution
        assert len(analysis.insights) > 0
    
    def test_think_generates_recommendations(self, setup_owner_with_pets):
        """Test that think stage generates recommendations."""
        scheduler = Scheduler(owner=setup_owner_with_pets)
        ai = create_ai_agent(scheduler)
        recommendations = ai.think()
        
        # Should have at least one recommendation
        assert len(recommendations) > 0
        assert all(isinstance(r, AIRecommendation) for r in recommendations)
    
    def test_think_recommendations_have_required_fields(self, setup_owner_with_pets):
        """Test that recommendations have all required fields."""
        scheduler = Scheduler(owner=setup_owner_with_pets)
        ai = create_ai_agent(scheduler)
        recommendations = ai.think()
        
        for rec in recommendations:
            assert rec.type in ["schedule", "priority", "conflict", "optimization"]
            assert rec.title
            assert rec.description
            assert 0.0 <= rec.confidence <= 1.0
            assert isinstance(rec.action_items, list)
            assert rec.priority_score >= 0
    
    def test_act_generates_natural_language(self, setup_owner_with_pets):
        """Test that act stage generates natural language summary."""
        scheduler = Scheduler(owner=setup_owner_with_pets)
        ai = create_ai_agent(scheduler)
        recommendations = ai.think()
        summary = ai.act(recommendations)
        
        # Should contain markdown formatting
        assert "##" in summary
        assert len(summary) > 0
    
    def test_check_validates_empty_plan(self, setup_owner_with_pets):
        """Test that check stage handles empty plan."""
        scheduler = Scheduler(owner=setup_owner_with_pets)
        ai = create_ai_agent(scheduler)
        
        is_valid, issues = ai.check([])
        
        assert is_valid is False
        assert len(issues) > 0
    
    def test_check_validates_plan_with_gaps(self, setup_owner_with_pets):
        """Test that check detects large gaps in schedule."""
        from pawpal_system import ScheduledTask
        
        owner = setup_owner_with_pets
        pet = owner.pets[0]
        
        # Create tasks for the schedule
        task1 = Task(title="Task 1", task_type="walk", duration_minutes=30)
        task2 = Task(title="Task 2", task_type="feed", duration_minutes=30)
        
        start = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        scheduled_items = [
            ScheduledTask(
                task=task1,
                pet=pet,
                start_time=start,
                end_time=start + timedelta(minutes=30)
            ),
            ScheduledTask(
                task=task2,
                pet=pet,
                start_time=start + timedelta(hours=2),  # 2 hour gap!
                end_time=start + timedelta(hours=2, minutes=30)
            ),
        ]
        
        scheduler = Scheduler(owner=owner)
        scheduler.scheduled_items = scheduled_items
        ai = create_ai_agent(scheduler)
        
        is_valid, issues = ai.check(scheduled_items)
        
        # Should detect the large gap
        assert any("gap" in issue.lower() for issue in issues)
    
    def test_check_validates_priority_distribution(self, setup_owner_with_pets):
        """Test that check validates priority distribution."""
        from pawpal_system import ScheduledTask
        
        owner = setup_owner_with_pets
        pet = owner.pets[0]
        
        # Create only low-priority tasks
        task1 = Task(title="Low priority 1", task_type="walk", duration_minutes=30, priority="low")
        task2 = Task(title="Low priority 2", task_type="feed", duration_minutes=30, priority="low")
        
        start = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        scheduled_items = [
            ScheduledTask(
                task=task1,
                pet=pet,
                start_time=start,
                end_time=start + timedelta(minutes=30)
            ),
            ScheduledTask(
                task=task2,
                pet=pet,
                start_time=start + timedelta(minutes=30),
                end_time=start + timedelta(hours=1)
            ),
        ]
        
        scheduler = Scheduler(owner=owner)
        scheduler.scheduled_items = scheduled_items
        ai = create_ai_agent(scheduler)
        
        is_valid, issues = ai.check(scheduled_items)
        
        # Should have some issues (the check should find something)
        assert len(issues) > 0
    
    def test_run_agentic_workflow_returns_complete_analysis(self, setup_owner_with_pets):
        """Test that full agentic workflow returns complete analysis."""
        scheduler = Scheduler(owner=setup_owner_with_pets)
        ai = create_ai_agent(scheduler)
        analysis = ai.run_agentic_workflow()
        
        assert isinstance(analysis, AgentAnalysis)
        assert len(analysis.recommendations) > 0
        assert len(analysis.insights) >= 0
        assert len(analysis.warnings) >= 0
        assert analysis.summary
    
    def test_generate_plan_explanation(self, setup_owner_with_pets):
        """Test that plan explanation is generated correctly."""
        from pawpal_system import ScheduledTask
        
        owner = setup_owner_with_pets
        pet = owner.pets[0]
        
        task = Task(title="Morning walk", task_type="walk", duration_minutes=30, priority="high")
        start = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        
        plan = [
            ScheduledTask(
                task=task,
                pet=pet,
                start_time=start,
                end_time=start + timedelta(minutes=30),
                reason="High priority"
            )
        ]
        
        scheduler = Scheduler(owner=owner)
        ai = create_ai_agent(scheduler)
        
        explanation = ai.generate_plan_explanation(plan)
        
        assert "##" in explanation
        assert "Morning walk" in explanation
        assert "Mochi" in explanation
    
    def test_time_constraint_recommendation(self):
        """Test that AI recommends when tasks exceed available time."""
        owner = Owner(name="Jordan", available_hours=1.0)  # Only 1 hour
        pet = Pet(name="Mochi", species="dog")
        owner.add_pet(pet)
        
        # Add tasks totaling more than available time
        pet.add_task(Task(title="Task 1", task_type="walk", duration_minutes=30, priority="high"))
        pet.add_task(Task(title="Task 2", task_type="feed", duration_minutes=30, priority="medium"))
        pet.add_task(Task(title="Task 3", task_type="groom", duration_minutes=30, priority="low"))
        
        scheduler = Scheduler(owner=owner)
        ai = create_ai_agent(scheduler)
        recommendations = ai.think()
        
        # Should have a time constraint recommendation
        time_recs = [r for r in recommendations if r.type == "optimization"]
        assert len(time_recs) > 0
    
    def test_recurring_task_pattern_detection(self):
        """Test that AI detects recurring task patterns."""
        owner = Owner(name="Jordan", available_hours=2.0)
        pet = Pet(name="Mochi", species="dog")
        owner.add_pet(pet)
        
        # Add recurring tasks
        pet.add_task(Task(
            title="Daily walk",
            task_type="walk",
            duration_minutes=30,
            priority="high",
            frequency="daily",
            deadline=date.today()
        ))
        pet.add_task(Task(
            title="Weekly grooming",
            task_type="groom",
            duration_minutes=60,
            priority="medium",
            frequency="weekly",
            deadline=date.today()
        ))
        
        scheduler = Scheduler(owner=owner)
        ai = create_ai_agent(scheduler)
        recommendations = ai.think()
        
        # Should detect recurring patterns
        recurring_recs = [r for r in recommendations if "recurring" in r.title.lower()]
        assert len(recurring_recs) > 0


class TestAIRecommendation:
    """Test suite for AIRecommendation dataclass."""
    
    def test_recommendation_creation(self):
        """Test creating a recommendation."""
        rec = AIRecommendation(
            type="schedule",
            title="Test Recommendation",
            description="Test description",
            confidence=0.85,
            action_items=["Action 1", "Action 2"],
            priority_score=75
        )
        
        assert rec.type == "schedule"
        assert rec.confidence == 0.85
        assert len(rec.action_items) == 2
    
    def test_default_values(self):
        """Test default values for recommendations."""
        rec = AIRecommendation(
            type="priority",
            title="Test",
            description="Test"
        )
        
        assert rec.confidence == 0.0
        assert rec.action_items == []
        assert rec.priority_score == 0