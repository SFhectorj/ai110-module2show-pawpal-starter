"""Demo script: build an owner with pets and tasks, then print today's schedule."""

from pawpal_system import Owner, Pet, Scheduler, Task


def main() -> None:
    owner = Owner(name="Jordan", available_minutes=90)

    rex = Pet(name="Rex", species="dog", age=4)
    mia = Pet(name="Mia", species="cat", age=2, special_needs="senior diet")
    owner.add_pet(rex)
    owner.add_pet(mia)

    rex.add_task(Task(1, "Morning walk", "exercise", 30, "high", "07:30"))
    rex.add_task(Task(2, "Training session", "enrichment", 20, "medium", "17:00"))
    mia.add_task(Task(3, "Breakfast", "feeding", 10, "high", "08:00"))
    mia.add_task(Task(4, "Brush fur", "grooming", 25, "low", "19:00", frequency="weekly"))
    mia.add_task(Task(5, "Vet-prescribed meds", "medication", 5, "high", "21:00"))

    owner_pets = {pet.name: pet for pet in owner.pets}
    pet_for_task = {t.id: pet.name for pet in owner.pets for t in pet.tasks}

    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan()

    print("=" * 50)
    print(f"Today's Schedule for {owner.name} ({plan.date.isoformat()})")
    print(f"Time available: {owner.available_minutes} min | "
          f"Pets: {', '.join(owner_pets)}")
    print("=" * 50)

    for task in sorted(plan.scheduled_tasks, key=lambda t: t.preferred_time):
        print(f"{task.preferred_time or '--:--'}  {task.title:<22} "
              f"{pet_for_task[task.id]:<5} {task.duration_minutes:>3} min  "
              f"[{task.priority}]")

    if plan.skipped_tasks:
        print("\nSkipped:")
        for task in plan.skipped_tasks:
            print(f"  {task.title} ({pet_for_task[task.id]}): {plan.explanations[task.id]}")

    print("-" * 50)
    print(f"Total scheduled: {plan.get_total_minutes()} min")


if __name__ == "__main__":
    main()
