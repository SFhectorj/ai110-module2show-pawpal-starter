from datetime import timedelta

from pawpal_system import Owner, Pet, Scheduler, Task


def test_mark_complete_changes_task_status():
    task = Task(1, "Morning walk", "exercise", 30, "high", "07:30")
    assert task.is_completed is False

    task.mark_complete()

    assert task.is_completed is True


def test_adding_task_increases_pet_task_count():
    pet = Pet(name="Rex", species="dog", age=4)
    assert len(pet.tasks) == 0

    pet.add_task(Task(1, "Morning walk", "exercise", 30, "high", "07:30"))

    assert len(pet.tasks) == 1


def test_sort_by_time_orders_chronologically_with_untimed_last():
    scheduler = Scheduler(Owner(name="Jordan", available_minutes=90))
    tasks = [
        Task(1, "Evening meds", "medication", 5, "high", "21:00"),
        Task(2, "Anytime play", "enrichment", 10, "low"),
        Task(3, "Morning walk", "exercise", 30, "high", "07:30"),
        Task(4, "Training", "enrichment", 20, "medium", "17:00"),
    ]

    result = scheduler.sort_by_time(tasks)

    assert [t.id for t in result] == [3, 4, 1, 2]


def _scheduler_with_two_pets():
    owner = Owner(name="Jordan", available_minutes=90)
    rex = Pet(name="Rex", species="dog", age=4)
    mia = Pet(name="Mia", species="cat", age=2)
    owner.add_pet(rex)
    owner.add_pet(mia)
    rex.add_task(Task(1, "Morning walk", "exercise", 30, "high", "07:30"))
    rex.add_task(Task(2, "Training", "enrichment", 20, "medium", "17:00"))
    mia.add_task(Task(3, "Breakfast", "feeding", 10, "high", "08:00"))
    rex.tasks[0].mark_complete()
    return Scheduler(owner)


def test_filter_tasks_by_completion_status():
    scheduler = _scheduler_with_two_pets()

    assert [t.id for t in scheduler.filter_tasks(completed=True)] == [1]
    assert [t.id for t in scheduler.filter_tasks(completed=False)] == [2, 3]


def test_filter_tasks_by_pet_name_is_case_insensitive():
    scheduler = _scheduler_with_two_pets()

    assert [t.id for t in scheduler.filter_tasks(pet_name="rex")] == [1, 2]
    assert scheduler.filter_tasks(pet_name="Nobody") == []


def test_filter_tasks_combines_filters_and_defaults_to_all():
    scheduler = _scheduler_with_two_pets()

    assert [t.id for t in scheduler.filter_tasks(completed=False, pet_name="Rex")] == [2]
    assert len(scheduler.filter_tasks()) == 3


def test_completing_daily_task_creates_next_day_instance():
    scheduler = _scheduler_with_two_pets()
    pet = scheduler.owner.pets[0]
    pet.tasks[1].frequency = "daily"
    original = pet.tasks[1]

    following = scheduler.complete_task(original.id)

    assert original.is_completed is True
    assert following in pet.tasks
    assert following.id not in {t.id for t in scheduler.owner.get_all_tasks() if t is not following}
    assert following.is_completed is False
    assert following.due_date == original.due_date + timedelta(days=1)
    assert following.title == original.title


def test_completing_weekly_task_creates_instance_seven_days_later():
    scheduler = _scheduler_with_two_pets()
    task = scheduler.owner.pets[1].tasks[0]
    task.frequency = "weekly"

    following = scheduler.complete_task(task.id)

    assert following.due_date == task.due_date + timedelta(days=7)


def test_completing_one_off_task_creates_nothing():
    scheduler = _scheduler_with_two_pets()
    task = scheduler.owner.pets[1].tasks[0]
    task.frequency = "once"
    before = len(scheduler.owner.get_all_tasks())

    assert scheduler.complete_task(task.id) is None
    assert len(scheduler.owner.get_all_tasks()) == before


def test_future_occurrence_is_not_in_todays_plan():
    scheduler = _scheduler_with_two_pets()
    task = scheduler.owner.pets[1].tasks[0]
    task.frequency = "daily"
    following = scheduler.complete_task(task.id)

    plan = scheduler.generate_plan()

    assert following not in plan.scheduled_tasks + plan.skipped_tasks


def test_find_conflicts_returns_nothing_when_times_are_distinct():
    assert _scheduler_with_two_pets().find_conflicts() == []


def test_find_conflicts_detects_same_pet_clash():
    scheduler = _scheduler_with_two_pets()
    rex = scheduler.owner.pets[0]
    rex.add_task(Task(4, "Teeth brushing", "grooming", 5, "low", "17:00"))

    warnings = scheduler.find_conflicts()

    assert len(warnings) == 1
    assert "for Rex at 17:00" in warnings[0]
    assert "Training" in warnings[0] and "Teeth brushing" in warnings[0]


def test_find_conflicts_detects_cross_pet_clash():
    scheduler = _scheduler_with_two_pets()
    scheduler.owner.pets[1].add_task(Task(4, "Flea treatment", "medication", 5, "low", "17:00"))

    warnings = scheduler.find_conflicts()

    assert len(warnings) == 1
    assert "across Rex and Mia" in warnings[0]


def test_find_conflicts_ignores_untimed_completed_and_other_days():
    scheduler = _scheduler_with_two_pets()
    rex, mia = scheduler.owner.pets
    rex.add_task(Task(4, "No time A", "play", 5, "low"))
    mia.add_task(Task(5, "No time B", "play", 5, "low"))
    done = Task(6, "Already done", "play", 5, "low", "17:00")
    done.mark_complete()
    mia.add_task(done)
    mia.add_task(Task(7, "Tomorrow", "play", 5, "low", "17:00",
                      due_date=rex.tasks[1].due_date + timedelta(days=1)))

    assert scheduler.find_conflicts() == []
