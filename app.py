import streamlit as st
from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
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

st.divider()

st.subheader("Owner")

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=120)
if "next_task_id" not in st.session_state:
    st.session_state.next_task_id = 1

owner = st.session_state.owner

col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name", value=owner.name)
with col2:
    available = st.number_input(
        "Minutes available today", min_value=0, max_value=1440, value=owner.available_minutes
    )
owner.name = owner_name
owner.update_availability(int(available))

st.subheader("Pets")
with st.form("add_pet_form", clear_on_submit=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with c2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with c3:
        age = st.number_input("Age", min_value=0, max_value=40, value=3)
    special_needs = st.text_input("Special needs (optional)")
    if st.form_submit_button("Add pet"):
        if not pet_name.strip():
            st.error("Pet name is required.")
        else:
            owner.add_pet(
                Pet(name=pet_name.strip(), species=species, age=int(age), special_needs=special_needs)
            )
            st.success(f"Added {pet_name.strip()}.")

if owner.pets:
    st.table(
        [
            {"name": p.name, "species": p.species, "age": p.age, "tasks": len(p.tasks)}
            for p in owner.pets
        ]
    )
else:
    st.info("No pets yet. Add one above.")

st.subheader("Tasks")
if not owner.pets:
    st.caption("Add a pet before scheduling tasks.")
else:
    with st.form("add_task_form"):
        target_name = st.selectbox("Pet", [p.name for p in owner.pets])
        c1, c2 = st.columns(2)
        with c1:
            task_title = st.text_input("Task title", value="Morning walk")
            category = st.text_input("Category", value="exercise")
            frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])
        with c2:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
            preferred_time = st.text_input("Preferred time (HH:MM, optional)")
        if st.form_submit_button("Add task"):
            pet = next(p for p in owner.pets if p.name == target_name)
            try:
                pet.add_task(
                    Task(
                        id=st.session_state.next_task_id,
                        title=task_title,
                        category=category,
                        duration_minutes=int(duration),
                        priority=priority,
                        preferred_time=preferred_time.strip(),
                        frequency=frequency,
                    )
                )
                st.session_state.next_task_id += 1
                st.success(f"Added '{task_title}' to {pet.name}.")
            except ValueError as e:
                st.error(str(e))

all_rows = [
    {
        "pet": p.name,
        "title": t.title,
        "duration_minutes": t.duration_minutes,
        "priority": t.priority,
        "preferred_time": t.preferred_time,
        "done": t.is_completed,
    }
    for p in owner.pets
    for t in p.tasks
]
if all_rows:
    st.write("Current tasks:")
    st.table(all_rows)
else:
    st.info("No tasks yet.")

st.divider()

st.subheader("Build Schedule")

if st.button("Generate schedule"):
    plan = Scheduler(owner).generate_plan()
    st.success(f"{plan.get_total_minutes()} of {owner.available_minutes} minutes scheduled.")
    pet_of = {t.id: p.name for p in owner.pets for t in p.tasks}
    st.markdown("**Scheduled**")
    for t in plan.scheduled_tasks:
        st.write(f"- {t.title} ({pet_of.get(t.id, '?')}, {t.duration_minutes} min): {plan.explanations[t.id]}")
    if plan.skipped_tasks:
        st.markdown("**Skipped**")
        for t in plan.skipped_tasks:
            st.write(f"- {t.title} ({pet_of.get(t.id, '?')}): {plan.explanations[t.id]}")
