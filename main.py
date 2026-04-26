from datetime import datetime, timedelta
from pawpal_system import Owner, Pet, Task, Scheduler, ScheduledTask

owner = Owner(name="Jordan", available_hours=4.0)
pet1 = Pet(name="Mochi", species="dog", age=3)
pet2 = Pet(name="Neko", species="cat", age=2)

owner.add_pet(pet1)
owner.add_pet(pet2)

task_a = Task(title="Morning walk", task_type="walk", duration_minutes=30, priority="high")
task_b = Task(title="Feed dinner", task_type="feed", duration_minutes=15, priority="medium")
task_c = Task(title="Grooming", task_type="groom", duration_minutes=45, priority="low")

pet1.add_task(task_a)
pet2.add_task(task_b)
pet1.add_task(task_c)

scheduler = Scheduler(owner=owner)
plan = scheduler.generate_plan(start_time=datetime.now().replace(hour=9, minute=0, second=0, microsecond=0))

# Inject a lightweight conflict scenario with two simultaneous tasks.
conflict_start = datetime.now().replace(hour=11, minute=0, second=0, microsecond=0)
conflict_end = conflict_start + timedelta(minutes=30)
conflict_task_a = ScheduledTask(task=task_a, pet=pet1, start_time=conflict_start, end_time=conflict_end)
conflict_task_b = ScheduledTask(task=task_b, pet=pet2, start_time=conflict_start, end_time=conflict_end)

scheduler.scheduled_items.extend([conflict_task_a, conflict_task_b])

print("Today's Schedule")
print("================")
if not scheduler.scheduled_items:
    print(scheduler.explain_plan())
else:
    for item in scheduler.scheduled_items:
        print(f"{item.start_time.strftime('%H:%M')} - {item.end_time.strftime('%H:%M')} | {item.pet.name} | {item.task.title} ({item.task.task_type}) [priority: {item.task.priority}]")

conflict_warnings = scheduler.detect_conflicts()
if conflict_warnings:
    print("\nWarning: Conflicts detected:")
    for warning in conflict_warnings:
        print("-", warning)

print("\nExplanation:", scheduler.explain_plan())
print("Plan score:", scheduler.score_plan())
