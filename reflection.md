# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
  - I designed a small domain model around pet care scheduling with separate objects for Owner, Pet, Task, Scheduler, and ScheduledTask. The system is centered on generating a daily plan from a set of tasks while respecting owner availability and task priority.
- What classes did you include, and what responsibilities did you assign to each?
  - `Owner`: store owner profile, availability, and preferences. Responsible for providing constraints and settings to the scheduler.
  - `Pet`: store pet details (name, species, age, care requirements). Responsible for representing pet-specific needs and helping identify required tasks.
  - `Task`: represent a single care activity (title, duration, priority, optional windows). Responsible for task state updates, completion, and validation.
  - `Scheduler`: orchestrate planning. Responsible for selecting and ordering tasks, applying constraints, and producing schedule entries + explanations.
  - `ScheduledTask`: represent a task scheduled at a specific time slot with a reason. Responsible for conflict checking and duration tracking.

Core user actions:

1. Add or edit a pet profile (owner/pet details, preferences, constraints) so the system has context.
2. Add and prioritize care tasks (walking, feeding, meds, enrichment, grooming) including duration requirements.
3. Generate and view a daily plan for today, with scheduled tasks and reasoning for the chosen order.

classDiagram
    class Owner {
        +str name
        +float available_hours
        +dict preferences
        +update_profile()
        +set_availability()
        +get_preference(key)
    }

    class Pet {
        +str name
        +str species
        +int age
        +str health_notes
        +dict care_requirements
        +update_health_notes()
        +needs_task(task_type)
        +summary()
    }

    class Task {
        +str title
        +str task_type
        +int duration_minutes
        +str priority
        +datetime? window_start
        +datetime? window_end
        +bool completed
        +mark_complete()
        +update_priority()
        +adjust_duration()
        +is_overdue(today)
    }

    class ScheduledTask {
        +Task task
        +datetime start_time
        +datetime end_time
        +str reason
        +duration()
        +flag_conflict(other)
    }

    class Scheduler {
        +Owner owner
        +Pet pet
        +List~Task~ tasks
        +date date
        +List~ScheduledTask~ scheduled_items
        +str explanation
        +add_task(task)
        +remove_task(task_id)
        +generate_plan()
        +get_today_tasks()
        +explain_plan()
        +score_plan()
    }

    Owner "1" -- "1" Pet : owns
    Scheduler "1" -- "1" Owner
    Scheduler "1" -- "1" Pet
    Scheduler "1" -- "*" Task
    Scheduler "1" -- "*" ScheduledTask
    ScheduledTask "1" -- "1" Task


**b. Design changes**

- Did your design change during implementation?
  - Yes. I started with a simple `Task` focus, then added explicit `Owner` and `Pet` classes to model constraints and preferences more clearly.
- If yes, describe at least one change and why you made it.
  - `Owner` initially included `email`, but I removed it because authentication/contact details are out of scope for a planning prototype; it simplified the data model and kept the focus on scheduling behavior.
  - I added `ScheduledTask` to separate raw task definition from scheduled instances, which made conflict detection and timeline generation easier to reason about.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
  - Time available (`Owner.available_hours` and summed task durations), so the plan never exceeds the owner's daily capacity.
  - Priority levels (`Task.priority`), encoded as numeric weights (high, medium, low) to prefer the most important pet care actions.
  - Optional deadlines (`Task.deadline`) and recurrence frequency (`Task.frequency`), to ensure overdue items are surfaced and daily/weekly tasks roll over.
  - Conflict avoidance with `ScheduledTask.conflicts_with` for overlapping time slots in the same or different pets.
  - It also tracks completed state so only pending tasks get scheduled, and supports owner preferences as future extension points.

- How did you decide which constraints mattered most?
  - I prioritized the constraints that directly affect owner effort and pet welfare: available time and task urgency.
  - Priority and deadlines align with real-world care needs (e.g., feeding is higher priority than optional grooming when time is scarce).
  - Recurrence and conflict detection were added next so users can trust the plan is not only feasible but repeatable and non-overlapping.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
  - The scheduler trades perfect global optimality for simplicity and responsiveness. It uses a greedy knapsack-like approach with priority weighting rather than exhaustive search over all task permutations.

- Why is that tradeoff reasonable for this scenario?
  - Pet owners need fast, understandable schedules in a UX context, not heavy computation. The chosen approach almost always yields practically good plans for the expected small number of tasks and provides clear reasoning and warnings, while keeping the codebase approachable for student project scope.

---

## 3. AI Collaboration

**a. How you used AI**
- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
    - I used AI to help design the domain model and class interactions (Owner, Pet, Task, Scheduler, ScheduledTask).
    - AI was helpful in suggesting algorithm patterns, especially priority-weighted scheduling and knapsack-style selection for limited available time.
- What kinds of prompts or questions were most helpful?
    - I used prompts to implement recurring task behavior, conflict detection, and Streamlit UI patterns.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
    - Initially, the AI solution suggested `mark_complete()` simply toggled complete state. I required a recurrence-aware return value to generate subsequent daily/weekly tasks, so I changed it to return a new task instance.
- How did you evaluate or verify what the AI suggested?
    - I wrote and ran unit tests (e.g., recurring task generation and schedule conflict detection) and used `python -m pytest` to confirm behavior after each change.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
    - Task completion and recurrence generation (`daily`/`weekly`).
    - Pet CRUD task operations.
    - Scheduler sorting, capacity selection, generation, conflict detection, and scoring.
    - Streamlit display behavior for sorted tasks and warnings.
- Why were these tests important?
    - They ensure core scheduling logic works and the user workflow remains reliable under real constraints.

**b. Confidence**

- How confident are you that your scheduler works correctly?
    - 4/5: all tests pass, core behaviors covered, and additional edge cases are identified for future work.
- What edge cases would you test next if you had more time?
    - Zero or negative duration tasks.
    - Invalid priority values.
    - Simultaneous task start/end overlap in generate_plan.
    - Very large task lists for performance.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
    - Implementing recurring task handling and conflict warnings made the scheduler practical and dependable.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
    - Add time windows (earliest/latest start), recurrence schedule on a calendar, and an optional optimization solver.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
    - Incremental implementation with tests is crucial, and AI is a strong assistant when suggestions are validated and adapted to real requirements.
