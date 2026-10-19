# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Implementation summary

The logic layer lives in `pawpal_system.py`. `main.py` is a terminal demo that builds an owner with two pets and prints today's schedule. The Streamlit UI in `app.py` is not yet connected to these classes.

### How the classes work together

```
Owner ──has many──▶ Pet ──has many──▶ Task
  ▲
  └── Scheduler ──produces──▶ DailyPlan
```

- **`Task`**: one care activity (title, category, duration, priority, preferred time, frequency, completion status). It validates priority (`high`/`medium`/`low`) and frequency (`once`/`daily`/`weekly`), and can be marked complete or updated.
- **`Pet`**: pet details plus its own list of tasks. It adds (rejecting duplicate ids), removes and edits tasks, and reports which are still pending.
- **`Owner`**: holds the pets, the minutes available per day, and preferences. `get_all_tasks()` returns every pet's tasks in one list.
- **`Scheduler`**: the "brain". It reads from `owner.get_all_tasks()` rather than from a single pet, so scheduling covers every pet. It drops completed tasks, sorts the rest (priority first, then preferred time, then shortest), and fills the owner's available minutes in that order.
- **`DailyPlan`**: the result. It holds the scheduled tasks, the skipped tasks (those that didn't fit), and a reason for each, with helpers for total minutes and a text summary.

### Flow

1. Create an `Owner` and add `Pet`s, then add `Task`s to each pet.
2. `Scheduler(owner).generate_plan()` gathers all pending tasks across pets, sorts them and greedily schedules what fits.
3. Anything that doesn't fit goes to `skipped_tasks` with an explanation, available through `explain_plan()` or `get_summary()`.

### Known limitation

Task ids are only unique within a pet. `DailyPlan.explanations` is keyed by task id, so two pets with the same task id would overwrite each other's explanations.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

```
==================================================
Today's Schedule for Jordan (2026-10-15)
Time available: 90 min | Pets: Rex, Mia
==================================================
07:30  Morning walk           Rex    30 min  [high]
08:00  Breakfast              Mia    10 min  [high]
17:00  Training session       Rex    20 min  [medium]
19:00  Brush fur              Mia    25 min  [low]
21:00  Vet-prescribed meds    Mia     5 min  [high]
--------------------------------------------------
Total scheduled: 90 min
```

## 🧪 Testing PawPal+

```bash
python -m pytest
```

The suite (`tests/test_pawpal.py`, 44 tests) covers:

- **Sorting:** chronological order, untimed tasks last, stable ties, empty input, input not mutated.
- **Recurrence:** daily (+1 day) and weekly (+7 days) follow-ups, one-off tasks, year-end and leap-year rollover, unique ids across pets, unknown ids.
- **Conflict detection:** same-time clashes within one pet and across pets, three-way clashes, and ignored cases (completed, untimed, different dates).
- **Plan generation:** priority order, exact-fit boundary, skipped tasks with reasons, never exceeding available time, overdue and future tasks.
- **Edge cases and validation:** pets with no tasks, owners with no pets, zero availability, invalid priority/frequency, duplicate ids.
- **Known limitations (documented as tests):** unpadded times sort as strings, overlapping durations with different start times are not flagged, completing a recurring task twice creates two follow-ups, a failed `Task.update` leaves the bad value in place, and task ids may repeat across pets.

Sample test output:

```
============================= test session starts ==============================
platform darwin -- Python 3.13.2, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/beck/Developer/ai110-module2show-pawpal-starter
plugins: anyio-4.14.1
collected 44 items

tests/test_pawpal.py ............................................        [100%]

============================== 44 passed in 0.02s ==============================
```

**Confidence Level: ★★★★☆ (4/5)** — All 44 tests pass, and the core behaviors (sorting, recurrence, conflict detection, planning) are verified including edge cases. One star is held back because five known limitations are documented rather than fixed.

## 📐 Smarter Scheduling

All of these live on `Scheduler` in `pawpal_system.py` (except where noted) and are exercised in `main.py` and `tests/test_pawpal.py`.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Plan ordering | `Scheduler.sort_tasks()` | Priority first, then preferred time, then shortest duration |
| Sorting by time | `Scheduler.sort_by_time()` | Chronological; tasks with no time go last |
| Filtering | `Scheduler.filter_tasks()` | By completion status and/or pet name |
| Conflict detection | `Scheduler.find_conflicts()` | Warns when pending tasks share a day and exact start time |
| Recurring tasks | `Task.next_occurrence()`, `Scheduler.complete_task()` | Completing a daily/weekly task creates the next one |

### Sorting

- `sort_by_time(tasks)` returns a new list ordered by `preferred_time`. It uses `sorted()` with a lambda key that returns a tuple, `(preferred_time == "", preferred_time)`. Tuples compare element by element and `False < True`, so untimed tasks sort after every timed one.
- `"HH:MM"` strings compare correctly as text only when they are zero-padded (`"07:30"`, not `"7:30"`).
- `sort_tasks()` is a separate ordering used by `generate_plan()` to decide what gets scheduled first when time is limited.

### Filtering

`filter_tasks(completed=None, pet_name=None)` returns matching tasks across all of the owner's pets.

- `completed=True` returns finished tasks and `completed=False` returns unfinished ones.
- `pet_name` matches case-insensitively, so `"rex"` finds Rex.
- A filter left as `None` is not applied. Both filters combine with AND, and with neither set every task is returned.
- The result is not sorted, so wrap it in `sort_by_time()` if you want it ordered.

### Conflict detection

`find_conflicts()` returns a list of warning strings and never raises, so the plan is still generated.

- Pending tasks are grouped by `(due_date, preferred_time)`, and every pair inside a group is reported. It checks within one pet and across pets, with a different message for each.
- Completed tasks, untimed tasks and tasks on different days are ignored.
- Example: `Conflict across Rex and Mia at 07:30 on 2026-10-18: 'Morning walk' and 'Flea treatment'`.
- **Limitation:** it matches exact start times only. A 30-minute task at 07:30 and another at 07:45 overlap but are not flagged. See the tradeoff in `reflection.md`.
- `generate_plan()` does not act on conflicts; call `find_conflicts()` alongside it to surface them.

### Recurring tasks

- `Task.due_date` (default: today) records when an occurrence is due.
- `Task.next_occurrence(new_id)` returns a not-completed copy due one period later: 1 day for `"daily"`, 7 days for `"weekly"`. It returns `None` for `"once"`.
- `Scheduler.complete_task(task_id)` marks the task complete and, if it recurs, adds the next occurrence to the same pet. The new task's id is one more than the largest id across all pets. It returns the new task, `None` for one-off tasks, and raises `KeyError` for an unknown id.
- The next due date is the old `due_date` plus the period, not today plus the period, so a late completion does not shift the schedule.
- `generate_plan()` skips tasks whose `due_date` is after today, so tomorrow's copy does not appear in today's plan.
- Calling `task.mark_complete()` directly does not create a follow-up, because a task does not know which pet owns it. Use `scheduler.complete_task()`.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
