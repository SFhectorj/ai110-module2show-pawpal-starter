import streamlit as st
from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("A pet care planner: add pets and tasks, spot clashes, and build today's schedule.")

st.divider()

st.subheader("Owner")

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=120)

owner = st.session_state.owner
scheduler = Scheduler(owner)


def next_task_id() -> int:
    """Next unused id; derived from existing tasks so recurring copies never collide."""
    return max((t.id for t in owner.get_all_tasks()), default=0) + 1


PRIORITY_BADGE = {"high": "🔴 high", "medium": "🟡 medium", "low": "🟢 low"}


def task_rows(tasks: list[Task]) -> list[dict]:
    """Display rows for a list of tasks."""
    pet_of = {t.id: p.name for p in owner.pets for t in p.tasks}
    return [
        {
            "Time": t.preferred_time or "—",
            "Pet": pet_of.get(t.id, "?"),
            "Task": t.title,
            "Minutes": t.duration_minutes,
            "Priority": PRIORITY_BADGE[t.priority],
            "Repeats": t.frequency,
            "Due": t.due_date.isoformat(),
            "Status": "✅ done" if t.is_completed else "⏳ pending",
        }
        for t in tasks
    ]


def show_conflicts() -> None:
    """Warn about tasks booked at the same time, with a concrete way to fix it."""
    conflicts = scheduler.find_conflicts()
    if not conflicts:
        return
    st.warning(
        f"**⚠️ {len(conflicts)} scheduling conflict{'s' if len(conflicts) > 1 else ''} found.** "
        "You can't be in two places at once, so these tasks can't both happen at their "
        "preferred time."
    )
    for message in conflicts:
        st.warning(message, icon="🕒")
    st.caption("💡 To fix: change one task's preferred time, or leave it blank to let PawPal+ place it.")


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
                        id=next_task_id(),
                        title=task_title,
                        category=category,
                        duration_minutes=int(duration),
                        priority=priority,
                        preferred_time=preferred_time.strip(),
                        frequency=frequency,
                    )
                )
                st.success(f"Added '{task_title}' to {pet.name}.")
            except ValueError as e:
                st.error(str(e))

if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))

if owner.get_all_tasks():
    show_conflicts()

    f1, f2, f3 = st.columns(3)
    with f1:
        pet_filter = st.selectbox("Pet", ["All pets"] + [p.name for p in owner.pets])
    with f2:
        status_filter = st.selectbox("Status", ["All", "Pending", "Completed"])
    with f3:
        sort_choice = st.selectbox("Sort by", ["Time of day", "Priority"])

    shown = scheduler.filter_tasks(
        completed={"All": None, "Pending": False, "Completed": True}[status_filter],
        pet_name=None if pet_filter == "All pets" else pet_filter,
    )
    shown = scheduler.sort_by_time(shown) if sort_choice == "Time of day" else scheduler.sort_tasks(shown)

    if shown:
        st.table(task_rows(shown))
    else:
        st.info("No tasks match these filters.")

    pending = scheduler.filter_tasks(completed=False)
    if pending:
        with st.form("complete_task_form"):
            labels = {f"{r['Pet']}: {r['Task']} (due {r['Due']})": t.id
                      for r, t in zip(task_rows(pending), pending)}
            choice = st.selectbox("Mark a task done", list(labels))
            if st.form_submit_button("Complete task"):
                following = scheduler.complete_task(labels[choice])
                st.session_state.flash = (
                    f"Done! Next {following.frequency} occurrence added for "
                    f"{following.due_date.isoformat()}."
                    if following else "Done! This was a one-off task."
                )
                st.rerun()
else:
    st.info("No tasks yet.")

st.divider()

st.subheader("Build Schedule")

if st.button("Generate schedule"):
    show_conflicts()
    plan = scheduler.generate_plan()
    if not plan.scheduled_tasks and not plan.skipped_tasks:
        st.info("Nothing due today. Add a task or enjoy the day off!")
    else:
        total, budget = plan.get_total_minutes(), owner.available_minutes
        st.success(f"{total} of {budget} minutes scheduled ({len(plan.scheduled_tasks)} tasks).")
        st.progress(min(total / budget, 1.0) if budget else 0.0)

        pet_of = {t.id: p.name for p in owner.pets for t in p.tasks}

        def plan_rows(tasks: list[Task]) -> list[dict]:
            return [
                {
                    "Time": t.preferred_time or "—",
                    "Pet": pet_of.get(t.id, "?"),
                    "Task": t.title,
                    "Minutes": t.duration_minutes,
                    "Priority": PRIORITY_BADGE[t.priority],
                    "Why": plan.explanations[t.id],
                }
                for t in tasks
            ]

        if plan.scheduled_tasks:
            st.markdown("**✅ Scheduled**")
            st.table(plan_rows(scheduler.sort_by_time(plan.scheduled_tasks)))
        if plan.skipped_tasks:
            st.warning(
                f"{len(plan.skipped_tasks)} task(s) didn't fit in your available time. "
                "Increase your minutes or shorten/reschedule these."
            )
            st.table(plan_rows(plan.skipped_tasks))
