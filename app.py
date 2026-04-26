import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler
from ai_agent import create_ai_agent, PawPalAI

# Configure logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+ AI-Powered Pet Care Planner")

st.markdown(
    """
Welcome to **PawPal+**, an AI-powered pet care planning assistant.

This app uses an **Agentic Workflow** AI system that:
- 🤖 Analyzes your tasks and provides smart recommendations
- 📊 Generates natural language explanations for scheduling decisions
- ⚠️ Detects potential issues and suggests resolutions
- ✅ Plans, acts, and checks its own work
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_hours=8.0)

owner = st.session_state.owner

st.divider()
st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)
owner.available_hours = st.number_input("Available hours", min_value=1.0, max_value=24.0, value=owner.available_hours)

st.divider()
st.subheader("Add Pet")
new_pet_name = st.text_input("Pet name", value="")
new_pet_species = st.selectbox("Species", ["dog", "cat", "other"])
new_pet_age = st.number_input("Age", min_value=0, max_value=30, value=0)

if st.button("Add pet"):
    if new_pet_name.strip():
        owner.add_pet(Pet(name=new_pet_name.strip(), species=new_pet_species, age=int(new_pet_age)))

pet_names = [pet.name for pet in owner.pets]
if pet_names:
    st.write("Current pets:")
    for pet in owner.pets:
        st.write(f"- {pet.summary()} ({len(pet.tasks)} tasks)")
else:
    st.info("No pets added yet.")

st.divider()
st.subheader("Add Task")
if pet_names:
    selected_pet_name = st.selectbox("Assign to pet", pet_names)
    task_title = st.text_input("Task title", value="Morning walk")
    task_type = st.selectbox("Task type", ["walk", "feed", "meds", "groom", "enrich"])
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=1)

    if st.button("Add task"):
        selected_pet = owner.get_pet(selected_pet_name)
        if selected_pet is not None:
            selected_pet.add_task(Task(title=task_title, task_type=task_type, duration_minutes=int(duration), priority=priority))

    selected_pet = owner.get_pet(selected_pet_name)
    if selected_pet:
        st.write(f"Tasks for {selected_pet.name}:")
        st.table([
            {
                "Title": t.title,
                "Type": t.task_type,
                "Duration": t.duration_minutes,
                "Priority": t.priority,
                "Completed": t.completed,
            }
            for t in selected_pet.tasks
        ])
else:
    st.info("Add a pet first before adding tasks.")

st.divider()
st.subheader("🤖 AI-Powered Schedule")

# Initialize AI agent
scheduler = Scheduler(owner=owner)
ai_agent = create_ai_agent(scheduler)

# Run agentic workflow to get recommendations
with st.spinner("🤖 AI is analyzing your pet care tasks..."):
    try:
        analysis = ai_agent.run_agentic_workflow()
        
        # Display warnings prominently
        if analysis.warnings:
            for warning in analysis.warnings:
                st.warning(warning)

        # Display AI insights
        if analysis.insights:
            st.markdown("### 💡 AI Insights")
            for insight in analysis.insights:
                if "⚠️" in insight:
                    st.warning(insight)
                elif "✅" in insight:
                    st.success(insight)
                else:
                    st.info(insight)

        # Display recommendations
        if analysis.recommendations:
            st.markdown("### 📋 AI Recommendations")
            for rec in analysis.recommendations[:3]:  # Show top 3
                with st.expander(f"{rec.title} (Confidence: {rec.confidence*100:.0f}%)"):
                    st.write(rec.description)
                    if rec.action_items:
                        st.markdown("**Suggested Actions:**")
                        for action in rec.action_items:
                            st.write(f"- {action}")
    except Exception as e:
        logger.error(f"AI agent error: {e}")
        st.error(f"AI analysis temporarily unavailable: {e}")

st.divider()
st.subheader("📅 Build Schedule")

if st.button("Generate schedule", type="primary"):
    scheduler = Scheduler(owner=owner)
    
    # Get pending tasks
    pending = scheduler.get_tasks_sorted()
    if pending:
        st.markdown("### Pending tasks sorted by deadline and priority")
        st.table([
            {
                "Pet": next((p.name for p in owner.pets if t in p.tasks), "Unknown"),
                "Title": t.title,
                "Type": t.task_type,
                "Duration": t.duration_minutes,
                "Priority": t.priority,
                "Deadline": t.deadline or "-",
                "Frequency": t.frequency,
            }
            for t in pending
        ])
    else:
        st.info("No pending tasks found.")

    # Generate plan
    plan = scheduler.generate_plan()
    
    # Run AI check on the plan
    ai_agent = create_ai_agent(scheduler)
    is_valid, issues = ai_agent.check(plan)
    
    # Display conflicts
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        st.warning("⚠️ Conflicts detected in your schedule:")
        for warn in conflicts:
            st.warning(warn)
    else:
        st.success("✅ No conflict detected in the planned schedule.")

    if not plan:
        st.info(scheduler.explain_plan())
    else:
        # AI-powered schedule explanation
        st.success("📅 Today's Schedule")
        st.table([
            {
                "Start": item.start_time.strftime('%H:%M'),
                "End": item.end_time.strftime('%H:%M'),
                "Pet": item.pet.name,
                "Task": item.task.title,
                "Type": item.task.task_type,
                "Priority": item.task.priority,
                "Reason": item.reason,
            }
            for item in plan
        ])

        # AI-powered explanation
        st.markdown("### 🤖 AI Schedule Analysis")
        
        # Show plan score
        st.metric("Plan Score", f"{scheduler.score_plan()*100:.0f}%")
        
        # Show AI-generated explanation
        explanation = ai_agent.generate_plan_explanation(plan)
        st.markdown(explanation)
        
        # Show AI validation results
        if issues:
            st.warning("⚠️ AI Plan Validation Issues:")
            for issue in issues:
                st.write(f"- {issue}")
        else:
            st.success("✅ AI validation passed - schedule looks optimal!")

