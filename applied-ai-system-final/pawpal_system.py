from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict

@dataclass
class Task:
    title: str
    task_type: str
    duration_minutes: int
    priority: str = "medium"
    frequency: str = "none"
    deadline: Optional[date] = None
    completed: bool = False
    created_at: datetime = field(default_factory=datetime.now)

    def mark_complete(self) -> Optional[Task]:
        """Mark this task as complete and return next occurrence for recurring tasks."""
        self.completed = True

        if self.frequency not in {"daily", "weekly"}:
            return None

        # Use timedelta for accurate recurrence handling.
        # Copilot: Python timedelta lets you add a fixed number of days.
        # Example: next_date = date.today() + timedelta(days=1) for daily.
        duration_days = 1 if self.frequency == "daily" else 7
        next_date = (self.deadline if self.deadline else date.today()) + timedelta(days=duration_days)

        return Task(
            title=self.title,
            task_type=self.task_type,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            frequency=self.frequency,
            deadline=next_date,
            completed=False,
            created_at=datetime.now(),
        )

    def mark_pending(self) -> None:
        """Mark this task as pending/incomplete."""
        self.completed = False

    def update_duration(self, duration_minutes: int) -> None:
        """Update task duration in minutes."""
        self.duration_minutes = duration_minutes

    def update_priority(self, priority: str) -> None:
        """Set task priority."""
        self.priority = priority

    def priority_weight(self) -> int:
        """Return the numeric score for task priority."""
        return {"high": 100, "medium": 50, "low": 20}.get(self.priority, 50)

    def value_density(self) -> float:
        """Return a weight-per-minute vale density used for scoring fit in schedule."""
        if self.duration_minutes <= 0:
            return float("inf")
        return self.priority_weight() / self.duration_minutes

    def is_overdue(self, reference: datetime) -> bool:
        """Return whether the task is overdue compared to reference time."""
        if self.deadline is None:
            return False
        return reference.date() > self.deadline


@dataclass
class Pet:
    name: str
    species: str
    age: int = 0
    health_notes: str = ""
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet."""
        self.tasks.append(task)

    def remove_task(self, title: str) -> None:
        """Remove a task by title from this pet."""
        self.tasks = [t for t in self.tasks if t.title != title]

    def get_tasks(self, include_completed: bool = False) -> List[Task]:
        """Return tasks, optionally including completed tasks."""
        return [t for t in self.tasks if include_completed or not t.completed]

    def summary(self) -> str:
        """Return a short description string for this pet."""
        return f"{self.name} ({self.species}, age {self.age})"


@dataclass
class Owner:
    name: str
    available_hours: float = 8.0
    preferences: Dict[str, str] = field(default_factory=dict)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        """Remove a pet by name."""
        self.pets = [p for p in self.pets if p.name != pet_name]

    def get_pet(self, pet_name: str) -> Optional[Pet]:
        """Get a pet instance by name, or None."""
        for pet in self.pets:
            if pet.name == pet_name:
                return pet
        return None

    def get_all_tasks(self, include_completed: bool = False) -> List[Task]:
        """Return all tasks for all pets belonging to this owner."""
        tasks = []
        for pet in self.pets:
            tasks.extend(pet.get_tasks(include_completed=include_completed))
        return tasks


@dataclass
class ScheduledTask:
    task: Task
    pet: Pet
    start_time: datetime
    end_time: datetime
    reason: Optional[str] = None

    def duration(self) -> int:
        """Return the scheduled task duration in minutes."""
        return int((self.end_time - self.start_time).total_seconds() // 60)

    def conflicts_with(self, other: ScheduledTask) -> bool:
        """Return whether this scheduled task conflicts with another one."""
        return not (self.end_time <= other.start_time or self.start_time >= other.end_time)


@dataclass
class Scheduler:
    owner: Owner
    date: date = field(default_factory=date.today)
    scheduled_items: List[ScheduledTask] = field(default_factory=list)
    explanation: str = ""

    def get_pending_tasks(self) -> List[Task]:
        """Return pending tasks for the owner across all pets."""
        return self.owner.get_all_tasks(include_completed=False)

    def get_tasks_sorted(self) -> List[Task]:
        """Return pending tasks sorted by deadline, priority, duration, and creation time."""
        priority_rank = {"high": 1, "medium": 2, "low": 3}
        tasks = self.get_pending_tasks()
        return sorted(
            tasks,
            key=lambda t: (
                t.deadline or date.max,
                priority_rank.get(t.priority, 2),
                -t.duration_minutes,
                t.created_at,
            ),
        )

    def _select_tasks_for_capacity(self, tasks: List[Task], capacity_minutes: int) -> List[Task]:
        """Choose the best subset of tasks that fits into available time using 0/1 knapsack on priority weight.

        This method is a lightweight heuristic for the owner's limited time budget.
        It assigns a numeric value to each task based on priority and then chooses
        the highest-value combination that still fits within capacity.

        Returns:
            A list of selected tasks to schedule.
        """
        if capacity_minutes <= 0 or not tasks:
            return []

        dp: List[tuple[float, List[int]]] = [(0.0, []) for _ in range(capacity_minutes + 1)]

        for idx, task in enumerate(tasks):
            duration = task.duration_minutes
            if duration > capacity_minutes or duration <= 0:
                continue

            value = task.priority_weight()
            for cap in range(capacity_minutes, duration - 1, -1):
                prev_score, prev_indices = dp[cap - duration]
                candidate_score = prev_score + value
                if candidate_score > dp[cap][0]:
                    dp[cap] = (candidate_score, prev_indices + [idx])

        best_score, best_indices = max(dp, key=lambda x: x[0])
        return [tasks[i] for i in best_indices]

    def generate_plan(self, start_time: datetime = None) -> List[ScheduledTask]:
        """Build a schedule using a knapsack-based selection to maximize priority value in available hours."""
        if start_time is None:
            start_time = datetime.combine(self.date, datetime.min.time()).replace(hour=8, minute=0)

        self.scheduled_items = []
        remaining_minutes = int(self.owner.available_hours * 60)
        current_time = start_time

        pending_tasks = self.get_tasks_sorted()
        selected_tasks = self._select_tasks_for_capacity(pending_tasks, remaining_minutes)

        if not selected_tasks:
            self.explanation = "No tasks could be scheduled within available hours."
            return self.scheduled_items

        # Keep task order human-friendly based on sorted preferences.
        selected_tasks = [t for t in pending_tasks if t in selected_tasks]

        for task in selected_tasks:
            if task.duration_minutes > remaining_minutes:
                continue

            end_time = current_time + timedelta(minutes=task.duration_minutes)
            assigned_pet = next((pet for pet in self.owner.pets if task in pet.tasks), None)
            if assigned_pet is None:
                continue

            scheduled = ScheduledTask(
                task=task,
                pet=assigned_pet,
                start_time=current_time,
                end_time=end_time,
                reason=f"Priority {task.priority}",
            )
            self.scheduled_items.append(scheduled)
            current_time = end_time
            remaining_minutes -= task.duration_minutes

            next_task = task.mark_complete()
            if next_task:
                assigned_pet.add_task(next_task)

        if not self.scheduled_items:
            self.explanation = "No tasks could be scheduled within available hours."
        else:
            self.explanation = (
                f"Scheduled {len(self.scheduled_items)} tasks with total {int(self.owner.available_hours*60 - remaining_minutes)} "
                f"min used and {remaining_minutes} min available."
            )

        conflicts = self.detect_conflicts()
        if conflicts:
            warning_text = " | ".join(conflicts)
            self.explanation += " WARNING: " + warning_text

        return self.scheduled_items

    def detect_conflicts(self) -> List[str]:
        """Return a list of conflict warning messages for overlapping scheduled tasks.

        This is a lightweight non-fatal strategy: the scheduler will report conflicts
        rather than crash, letting the UI layer decide how to resolve them.

        Returns:
            List of warnings, each describing a pair of conflicting tasks.
        """
        warnings: List[str] = []
        n = len(self.scheduled_items)
        for i in range(n):
            for j in range(i + 1, n):
                first = self.scheduled_items[i]
                second = self.scheduled_items[j]
                if first.conflicts_with(second):
                    warnings.append(
                        f"Conflict between '{first.task.title}' (pet {first.pet.name}) "
                        f"and '{second.task.title}' (pet {second.pet.name}) at {first.start_time.strftime('%H:%M')}."
                    )
        return warnings

    def explain_plan(self) -> str:
        """Return a human-friendly explanation of how the plan was generated.

        Warnings from conflict detection are appended to this string, so the caller
        can display both positives and potential issues in one place.

        Returns:
            Explanation string with optional conflict warning details.
        """
        return self.explanation

    def score_plan(self) -> float:
        """Score the plan effectiveness based on completed tasks ratio."""
        if not self.scheduled_items:
            return 0.0
        completed = len(self.scheduled_items)
        total = len(self.owner.get_all_tasks(include_completed=True))
        if total == 0:
            return 1.0
        return completed / total
