"""Demo script: build an owner with pets and tasks, then print today's schedule."""

from pawpal_system import Owner, Pet, Scheduler, Task


def format_task(task: Task, pet_for_task: dict) -> str:
    """One display row: time, title, pet, duration, priority, done marker."""
    done = "x" if task.is_completed else " "
    return (f"[{done}] {task.preferred_time or '--:--'}  {task.title:<22} "
            f"{pet_for_task[task.id]:<5} {task.duration_minutes:>3} min  "
            f"[{task.priority}]")


def main() -> None:
    owner = Owner(name="Jordan", available_minutes=90)

    rex = Pet(name="Rex", species="dog", age=4)
    mia = Pet(name="Mia", species="cat", age=2, special_needs="senior diet")
    owner.add_pet(rex)
    owner.add_pet(mia)

    # Added deliberately out of chronological order (and one with no time)
    # so the sorting and filtering output below is meaningful.
    mia.add_task(Task(5, "Vet-prescribed meds", "medication", 5, "high", "21:00"))
    rex.add_task(Task(2, "Training session", "enrichment", 20, "medium", "17:00"))
    mia.add_task(Task(4, "Brush fur", "grooming", 25, "low", "19:00", frequency="weekly"))
    rex.add_task(Task(6, "Fetch in the yard", "enrichment", 15, "low"))
    rex.add_task(Task(1, "Morning walk", "exercise", 30, "high", "07:30"))
    mia.add_task(Task(3, "Breakfast", "feeding", 10, "high", "08:00"))
    mia.tasks[-1].mark_complete()

    owner_pets = {pet.name: pet for pet in owner.pets}
    pet_for_task = {t.id: pet.name for pet in owner.pets for t in pet.tasks}

    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan()

    print("=" * 50)
    print(f"Today's Schedule for {owner.name} ({plan.date.isoformat()})")
    print(f"Time available: {owner.available_minutes} min | "
          f"Pets: {', '.join(owner_pets)}")
    print("=" * 50)

    for task in scheduler.sort_by_time(plan.scheduled_tasks):
        print(format_task(task, pet_for_task))

    if plan.skipped_tasks:
        print("\nSkipped:")
        for task in plan.skipped_tasks:
            print(f"  {task.title} ({pet_for_task[task.id]}): {plan.explanations[task.id]}")

    print("-" * 50)
    print(f"Total scheduled: {plan.get_total_minutes()} min")

    print("\nAll tasks as added (unsorted):")
    for task in owner.get_all_tasks():
        print(format_task(task, pet_for_task))

    print("\nAll tasks via sort_by_time:")
    for task in scheduler.sort_by_time(owner.get_all_tasks()):
        print(format_task(task, pet_for_task))

    print("\nfilter_tasks(completed=True):")
    for task in scheduler.filter_tasks(completed=True):
        print(format_task(task, pet_for_task))

    print("\nfilter_tasks(completed=False):")
    for task in scheduler.filter_tasks(completed=False):
        print(format_task(task, pet_for_task))

    print("\nfilter_tasks(pet_name='rex'), sorted by time:")
    for task in scheduler.sort_by_time(scheduler.filter_tasks(pet_name="rex")):
        print(format_task(task, pet_for_task))

    print("\nfilter_tasks(completed=False, pet_name='Mia'):")
    for task in scheduler.filter_tasks(completed=False, pet_name="Mia"):
        print(format_task(task, pet_for_task))

    before = scheduler.find_conflicts()
    print("\nConflict check (before adding clashing tasks):")
    print("  " + ("\n  ".join(before) or "none"))
    assert before == [], "expected no conflicts in the original task list"

    # Same pet, same time (Rex 17:00) and different pets, same time (07:30).
    rex.add_task(Task(7, "Teeth brushing", "grooming", 5, "low", "17:00"))
    mia.add_task(Task(8, "Flea treatment", "medication", 5, "medium", "07:30"))
    after = scheduler.find_conflicts()
    print("\nConflict check (after adding two clashing tasks):")
    for warning in after:
        print(f"  WARNING: {warning}")

    assert len(after) == 2, f"expected 2 conflicts, got {len(after)}"
    assert any("for Rex at 17:00" in w and "Teeth brushing" in w for w in after)
    assert any("across Rex and Mia at 07:30" in w and "Flea treatment" in w for w in after)
    print("  OK: both conflicts detected as expected.")


if __name__ == "__main__":
    main()
