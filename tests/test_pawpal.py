from datetime import date, timedelta

import pytest

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


# --- Edge cases: empty and zero ---

def test_pet_with_no_tasks_is_handled_everywhere():
    owner = Owner(name="Jordan", available_minutes=60)
    owner.add_pet(Pet(name="Empty", species="cat", age=1))
    scheduler = Scheduler(owner)

    assert owner.pets[0].get_pending_tasks() == []
    assert scheduler.filter_tasks() == []
    assert scheduler.find_conflicts() == []
    plan = scheduler.generate_plan()
    assert plan.scheduled_tasks == [] and plan.skipped_tasks == []
    assert plan.get_total_minutes() == 0


def test_owner_with_no_pets_has_no_tasks_and_cannot_complete():
    scheduler = Scheduler(Owner(name="Jordan", available_minutes=60))

    assert scheduler.owner.get_all_tasks() == []
    with pytest.raises(KeyError):
        scheduler.complete_task(1)


def test_sort_by_time_of_empty_list_is_empty():
    assert Scheduler(Owner(name="J", available_minutes=0)).sort_by_time([]) == []


def test_zero_available_minutes_skips_everything_with_reasons():
    scheduler = _scheduler_with_two_pets()
    scheduler.owner.update_availability(0)

    plan = scheduler.generate_plan()

    assert plan.scheduled_tasks == []
    assert len(plan.skipped_tasks) == 2
    assert all(plan.explanations[t.id] for t in plan.skipped_tasks)


def test_negative_availability_is_rejected():
    with pytest.raises(ValueError):
        Owner(name="J", available_minutes=10).update_availability(-1)


# --- Edge cases: same time and ties ---

def test_three_tasks_in_one_slot_give_three_pairwise_warnings():
    scheduler = _scheduler_with_two_pets()
    rex, mia = scheduler.owner.pets
    rex.add_task(Task(4, "A", "play", 5, "low", "17:00"))
    mia.add_task(Task(5, "B", "play", 5, "low", "17:00"))

    assert len(scheduler.find_conflicts()) == 3


def test_same_time_on_different_dates_is_not_a_conflict():
    owner = Owner(name="J", available_minutes=60)
    pet = Pet(name="Rex", species="dog", age=1)
    owner.add_pet(pet)
    today = date.today()
    pet.add_task(Task(1, "A", "play", 5, "low", "09:00", due_date=today))
    pet.add_task(Task(2, "B", "play", 5, "low", "09:00", due_date=today + timedelta(days=1)))

    assert Scheduler(owner).find_conflicts() == []


def test_sort_by_time_is_stable_for_equal_times():
    scheduler = Scheduler(Owner(name="J", available_minutes=0))
    tasks = [Task(i, f"T{i}", "play", 5, "low", "08:00") for i in (3, 1, 2)]

    assert [t.id for t in scheduler.sort_by_time(tasks)] == [3, 1, 2]


def test_sort_by_time_does_not_modify_input():
    scheduler = Scheduler(Owner(name="J", available_minutes=0))
    tasks = [Task(1, "B", "play", 5, "low", "10:00"), Task(2, "A", "play", 5, "low", "08:00")]

    scheduler.sort_by_time(tasks)

    assert [t.id for t in tasks] == [1, 2]


# --- Edge cases: time handling (documents known limits) ---

def test_unpadded_times_sort_incorrectly_known_limitation():
    scheduler = Scheduler(Owner(name="J", available_minutes=0))
    tasks = [Task(1, "Ten", "play", 5, "low", "10:00"), Task(2, "Nine", "play", 5, "low", "9:00")]

    # String comparison puts "9:00" after "10:00"; only zero-padded HH:MM is supported.
    assert [t.id for t in scheduler.sort_by_time(tasks)] == [1, 2]


def test_overlapping_durations_with_different_starts_are_not_detected():
    owner = Owner(name="J", available_minutes=120)
    pet = Pet(name="Rex", species="dog", age=1)
    owner.add_pet(pet)
    pet.add_task(Task(1, "Long walk", "exercise", 60, "high", "08:00"))
    pet.add_task(Task(2, "Feeding", "feeding", 10, "high", "08:30"))

    # Known gap: only exact start-time matches are flagged.
    assert Scheduler(owner).find_conflicts() == []


# --- Edge cases: recurrence ---

def test_daily_recurrence_rolls_over_year_end():
    scheduler = _scheduler_with_two_pets()
    task = scheduler.owner.pets[1].tasks[0]
    task.frequency = "daily"
    task.due_date = date(2025, 12, 31)

    assert scheduler.complete_task(task.id).due_date == date(2026, 1, 1)


def test_weekly_recurrence_rolls_over_month_end_and_leap_day():
    scheduler = _scheduler_with_two_pets()
    task = scheduler.owner.pets[1].tasks[0]
    task.frequency = "weekly"
    task.due_date = date(2024, 2, 26)

    assert scheduler.complete_task(task.id).due_date == date(2024, 3, 4)


def test_recurring_follow_up_gets_globally_unique_id_across_pets():
    scheduler = _scheduler_with_two_pets()
    mia_task = scheduler.owner.pets[1].tasks[0]  # id 3, the highest on Mia
    scheduler.owner.pets[0].tasks[1].id = 40     # a larger id on a different pet

    following = scheduler.complete_task(mia_task.id)

    assert following.id == 41
    ids = [t.id for t in scheduler.owner.get_all_tasks()]
    assert len(ids) == len(set(ids))


def test_complete_task_with_unknown_id_raises_key_error():
    with pytest.raises(KeyError):
        _scheduler_with_two_pets().complete_task(999)


def test_completing_same_recurring_task_twice_creates_two_follow_ups_known_limitation():
    scheduler = _scheduler_with_two_pets()
    task = scheduler.owner.pets[1].tasks[0]
    task.frequency = "daily"
    before = len(scheduler.owner.get_all_tasks())

    scheduler.complete_task(task.id)
    scheduler.complete_task(task.id)

    assert len(scheduler.owner.get_all_tasks()) == before + 2


def test_future_follow_up_still_appears_in_filter_tasks():
    scheduler = _scheduler_with_two_pets()
    task = scheduler.owner.pets[1].tasks[0]
    task.frequency = "daily"
    following = scheduler.complete_task(task.id)

    assert following in scheduler.filter_tasks(completed=False, pet_name="Mia")


# --- Edge cases: plan generation ---

def _plan_scheduler(minutes, *tasks):
    owner = Owner(name="J", available_minutes=minutes)
    pet = Pet(name="Rex", species="dog", age=1)
    owner.add_pet(pet)
    for t in tasks:
        pet.add_task(t)
    return Scheduler(owner)


def test_plan_schedules_high_priority_before_low():
    scheduler = _plan_scheduler(
        100,
        Task(1, "Low", "play", 10, "low", "06:00"),
        Task(2, "High", "meds", 10, "high", "20:00"),
        Task(3, "Med", "play", 10, "medium", "07:00"),
    )

    assert [t.id for t in scheduler.generate_plan().scheduled_tasks] == [2, 3, 1]


def test_task_that_exactly_fills_remaining_time_is_scheduled():
    plan = _plan_scheduler(30, Task(1, "Walk", "exercise", 30, "high")).generate_plan()

    assert [t.id for t in plan.scheduled_tasks] == [1]
    assert plan.get_total_minutes() == 30


def test_long_high_priority_task_is_skipped_while_smaller_ones_still_fit():
    scheduler = _plan_scheduler(
        30,
        Task(1, "Long grooming", "grooming", 45, "high"),
        Task(2, "Short play", "play", 10, "low"),
    )

    plan = scheduler.generate_plan()

    assert [t.id for t in plan.skipped_tasks] == [1]
    assert [t.id for t in plan.scheduled_tasks] == [2]
    assert "45" in plan.explanations[1]


def test_plan_never_exceeds_available_minutes():
    scheduler = _plan_scheduler(
        50, *[Task(i, f"T{i}", "play", 20, "medium") for i in range(1, 6)]
    )

    assert scheduler.generate_plan().get_total_minutes() <= 50


def test_overdue_incomplete_task_is_included_in_todays_plan():
    overdue = Task(1, "Missed meds", "meds", 5, "high", due_date=date.today() - timedelta(days=2))
    plan = _plan_scheduler(30, overdue).generate_plan()

    assert overdue in plan.scheduled_tasks


def test_completed_tasks_are_excluded_from_plan():
    done = Task(1, "Done", "play", 5, "high")
    done.mark_complete()
    plan = _plan_scheduler(30, done).generate_plan()

    assert plan.scheduled_tasks == [] and plan.skipped_tasks == []


# --- Edge cases: validation and integrity ---

def test_invalid_priority_or_frequency_rejected_on_construction():
    with pytest.raises(ValueError):
        Task(1, "X", "play", 5, "urgent")
    with pytest.raises(ValueError):
        Task(1, "X", "play", 5, "high", frequency="monthly")


def test_update_rejects_id_and_unknown_fields():
    task = Task(1, "X", "play", 5, "high")

    with pytest.raises(AttributeError):
        task.update({"id": 2})
    with pytest.raises(AttributeError):
        task.update({"colour": "red"})


def test_update_with_invalid_value_raises():
    task = Task(1, "X", "play", 5, "high")

    with pytest.raises(ValueError):
        task.update({"priority": "urgent"})


def test_failed_update_leaves_bad_value_on_task_known_limitation():
    task = Task(1, "X", "play", 5, "high")

    with pytest.raises(ValueError):
        task.update({"priority": "urgent"})

    # update() sets attributes before validating, so the task is left invalid.
    assert task.priority == "urgent"


def test_duplicate_task_id_rejected_within_one_pet():
    pet = Pet(name="Rex", species="dog", age=1)
    pet.add_task(Task(1, "A", "play", 5, "low"))

    with pytest.raises(ValueError):
        pet.add_task(Task(1, "B", "play", 5, "low"))


def test_duplicate_task_id_across_pets_is_allowed_known_limitation():
    scheduler = _plan_scheduler(30, Task(1, "A", "play", 5, "low"))
    other = Pet(name="Mia", species="cat", age=1)
    scheduler.owner.add_pet(other)

    other.add_task(Task(1, "B", "play", 5, "low"))  # no error

    ids = [t.id for t in scheduler.owner.get_all_tasks()]
    assert ids == [1, 1]


def test_edit_and_remove_missing_task():
    pet = Pet(name="Rex", species="dog", age=1)

    with pytest.raises(KeyError):
        pet.edit_task(1, {"title": "New"})
    pet.remove_task(1)  # silently a no-op
    assert pet.tasks == []
