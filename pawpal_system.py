"""PawPal+ logic layer: backend classes for owners, pets, tasks, and scheduling."""

from collections import defaultdict
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from itertools import combinations

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
VALID_FREQUENCIES = {"once", "daily", "weekly"}
RECURRENCE_DAYS = {"daily": 1, "weekly": 7}


@dataclass
class Task:
    id: int
    title: str
    category: str
    duration_minutes: int
    priority: str
    preferred_time: str = ""
    description: str = ""
    frequency: str = "daily"
    is_completed: bool = False
    due_date: date = field(default_factory=date.today)

    def __post_init__(self) -> None:
        """Validate that priority and frequency hold allowed values."""
        if self.frequency not in VALID_FREQUENCIES:
            raise ValueError(f"frequency must be one of {sorted(VALID_FREQUENCIES)}")
        if self.priority not in PRIORITY_ORDER:
            raise ValueError(f"priority must be one of {sorted(PRIORITY_ORDER)}")

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.is_completed = True

    def next_occurrence(self, new_id: int) -> "Task | None":
        """Build the next occurrence of a recurring task.

        Args:
            new_id: Id to give the new task (the caller must ensure it is unused).

        Returns:
            A copy of this task, not completed, due one period after this task's
            due_date (1 day for "daily", 7 for "weekly"). Returns None when the
            frequency is "once", since a one-off task does not recur.
        """
        days = RECURRENCE_DAYS.get(self.frequency)
        if days is None:
            return None
        return replace(self, id=new_id, is_completed=False,
                       due_date=self.due_date + timedelta(days=days))

    def update(self, changes: dict) -> None:
        """Apply field changes from a dict and re-validate the task."""
        for key, value in changes.items():
            if key == "id" or not hasattr(self, key):
                raise AttributeError(f"Cannot update task field '{key}'")
            setattr(self, key, value)
        self.__post_init__()


@dataclass
class Pet:
    name: str
    species: str
    age: int
    special_needs: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet, rejecting duplicate task ids."""
        if any(t.id == task.id for t in self.tasks):
            raise ValueError(f"Task id {task.id} already exists for {self.name}")
        self.tasks.append(task)

    def remove_task(self, task_id: int) -> None:
        """Remove the task with the given id, if present."""
        self.tasks = [t for t in self.tasks if t.id != task_id]

    def edit_task(self, task_id: int, changes: dict) -> None:
        """Update the task with the given id, raising KeyError if not found."""
        for task in self.tasks:
            if task.id == task_id:
                task.update(changes)
                return
        raise KeyError(f"No task with id {task_id} for {self.name}")

    def get_pending_tasks(self) -> list[Task]:
        """Return this pet's tasks that are not yet completed."""
        return [t for t in self.tasks if not t.is_completed]


@dataclass
class Owner:
    name: str
    available_minutes: int
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def update_availability(self, minutes: int) -> None:
        """Set the owner's available minutes for the day."""
        if minutes < 0:
            raise ValueError("available minutes cannot be negative")
        self.available_minutes = minutes

    def set_preference(self, key: str, value) -> None:
        """Store an owner preference under the given key."""
        self.preferences[key] = value

    def get_all_tasks(self) -> list[Task]:
        """Every task across all of the owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]


@dataclass
class DailyPlan:
    date: date
    scheduled_tasks: list[Task] = field(default_factory=list)
    skipped_tasks: list[Task] = field(default_factory=list)
    explanations: dict = field(default_factory=dict)

    def add_entry(self, task: Task, reason: str, scheduled: bool = True) -> None:
        """Record a task as scheduled or skipped along with the reason."""
        (self.scheduled_tasks if scheduled else self.skipped_tasks).append(task)
        self.explanations[task.id] = reason

    def get_total_minutes(self) -> int:
        """Return the total duration of all scheduled tasks."""
        return sum(t.duration_minutes for t in self.scheduled_tasks)

    def get_summary(self) -> str:
        """Return a human-readable text summary of the plan."""
        lines = [f"Plan for {self.date.isoformat()} "
                 f"({self.get_total_minutes()} min scheduled)"]
        for t in self.scheduled_tasks:
            lines.append(f"  [x] {t.title} ({t.duration_minutes} min) - {self.explanations.get(t.id, '')}")
        for t in self.skipped_tasks:
            lines.append(f"  [ ] {t.title} skipped - {self.explanations.get(t.id, '')}")
        return "\n".join(lines)


@dataclass
class Scheduler:
    owner: Owner

    def generate_plan(self) -> DailyPlan:
        """Build today's plan with a greedy, priority-first fill.

        Considers tasks that are not completed and are due today or earlier
        (future occurrences of recurring tasks are left out). Tasks are taken
        in sort_tasks order and scheduled while they fit in the owner's
        remaining minutes; a task that does not fit is skipped with a reason,
        but smaller later tasks can still be scheduled. This is not optimal:
        it can skip a long high-priority task in favour of shorter ones.

        Returns:
            A DailyPlan with scheduled and skipped tasks and an explanation for each.
        """
        plan = DailyPlan(date=date.today())
        today = plan.date
        pending = [t for t in self.owner.get_all_tasks()
                   if not t.is_completed and t.due_date <= today]
        remaining = self.owner.available_minutes
        for task in self.sort_tasks(pending):
            if task.duration_minutes <= remaining:
                remaining -= task.duration_minutes
                plan.add_entry(task, f"{task.priority} priority; fits in remaining time")
            else:
                plan.add_entry(task, f"needs {task.duration_minutes} min but only {remaining} left", scheduled=False)
        return plan

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Highest priority first, then earliest preferred time, then shortest."""
        return sorted(
            tasks,
            key=lambda t: (
                PRIORITY_ORDER.get(t.priority, len(PRIORITY_ORDER)),
                t.preferred_time == "",
                t.preferred_time,
                t.duration_minutes,
            ),
        )

    def complete_task(self, task_id: int) -> Task | None:
        """Mark a task complete and, if it recurs, schedule its next occurrence.

        The next occurrence is added to the same pet and gets an id one higher
        than the largest id across all of the owner's pets, so ids stay unique.

        Args:
            task_id: Id of the task to complete.

        Returns:
            The newly created task, or None if the task does not recur.

        Raises:
            KeyError: If no pet has a task with this id.
        """
        for pet in self.owner.pets:
            for task in pet.tasks:
                if task.id == task_id:
                    task.mark_complete()
                    new_id = max(t.id for t in self.owner.get_all_tasks()) + 1
                    following = task.next_occurrence(new_id)
                    if following is not None:
                        pet.add_task(following)
                    return following
        raise KeyError(f"No task with id {task_id}")

    def find_conflicts(self) -> list[str]:
        """Detect pending tasks booked for the same moment.

        Pending tasks are bucketed by (due_date, preferred_time), then every
        pair inside a bucket is reported, so one pass over the tasks plus the
        number of clashing pairs bounds the work. Matching is on exact start
        time only; differing start times with overlapping durations are not
        detected. Tasks that are completed or have no preferred time are skipped.

        Returns:
            One human-readable warning per clashing pair, saying whether it is
            within one pet or across two, or an empty list if there are none.
        """
        slots: defaultdict[tuple[date, str], list[tuple[str, Task]]] = defaultdict(list)
        for pet in self.owner.pets:
            for task in pet.get_pending_tasks():
                if task.preferred_time:
                    slots[task.due_date, task.preferred_time].append((pet.name, task))

        warnings = []
        for (day, time), entries in slots.items():
            for (pet_a, a), (pet_b, b) in combinations(entries, 2):
                scope = f"for {pet_a}" if pet_a == pet_b else f"across {pet_a} and {pet_b}"
                warnings.append(f"Conflict {scope} at {time} on {day.isoformat()}: "
                                f"'{a.title}' and '{b.title}'")
        return warnings

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Order tasks chronologically by preferred time.

        The sort key is a tuple, so tasks with no time (``""``) sort after every
        timed task. Times are compared as strings, which is correct only for
        zero-padded "HH:MM" values. The sort is stable, so ties keep input order.

        Returns:
            A new sorted list; the input list is not modified.
        """
        return sorted(tasks, key=lambda t: (t.preferred_time == "", t.preferred_time))

    def filter_tasks(self, completed: bool | None = None,
                     pet_name: str | None = None) -> list[Task]:
        """Select tasks by completion status and/or pet name.

        Args:
            completed: True for finished tasks, False for unfinished ones,
                None to ignore completion status.
            pet_name: Only tasks for the pet with this name (case-insensitive),
                or None to include every pet.

        Returns:
            Matching tasks in pet order, then insertion order. Both filters
            are combined with AND; with neither set, all tasks are returned.
        """
        return [
            task
            for pet in self.owner.pets
            if pet_name is None or pet.name.lower() == pet_name.lower()
            for task in pet.tasks
            if completed is None or task.is_completed == completed
        ]

    def fits_in_time(self, tasks: list[Task]) -> bool:
        """Return True if the tasks' total duration fits the owner's availability."""
        return sum(t.duration_minutes for t in tasks) <= self.owner.available_minutes

    def explain_plan(self, plan: DailyPlan) -> list[str]:
        """Return the reason for each scheduled and skipped task."""
        return [plan.explanations[t.id]
                for t in plan.scheduled_tasks + plan.skipped_tasks
                if t.id in plan.explanations]
