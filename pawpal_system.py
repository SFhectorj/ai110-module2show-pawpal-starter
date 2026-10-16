"""PawPal+ logic layer: backend classes for owners, pets, tasks, and scheduling."""

from dataclasses import dataclass, field
from datetime import date

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
VALID_FREQUENCIES = {"once", "daily", "weekly"}


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

    def __post_init__(self) -> None:
        if self.frequency not in VALID_FREQUENCIES:
            raise ValueError(f"frequency must be one of {sorted(VALID_FREQUENCIES)}")
        if self.priority not in PRIORITY_ORDER:
            raise ValueError(f"priority must be one of {sorted(PRIORITY_ORDER)}")

    def mark_complete(self) -> None:
        self.is_completed = True

    def update(self, changes: dict) -> None:
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
        if any(t.id == task.id for t in self.tasks):
            raise ValueError(f"Task id {task.id} already exists for {self.name}")
        self.tasks.append(task)

    def remove_task(self, task_id: int) -> None:
        self.tasks = [t for t in self.tasks if t.id != task_id]

    def edit_task(self, task_id: int, changes: dict) -> None:
        for task in self.tasks:
            if task.id == task_id:
                task.update(changes)
                return
        raise KeyError(f"No task with id {task_id} for {self.name}")

    def get_pending_tasks(self) -> list[Task]:
        return [t for t in self.tasks if not t.is_completed]


@dataclass
class Owner:
    name: str
    available_minutes: int
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        self.pets.append(pet)

    def update_availability(self, minutes: int) -> None:
        if minutes < 0:
            raise ValueError("available minutes cannot be negative")
        self.available_minutes = minutes

    def set_preference(self, key: str, value) -> None:
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
        (self.scheduled_tasks if scheduled else self.skipped_tasks).append(task)
        self.explanations[task.id] = reason

    def get_total_minutes(self) -> int:
        return sum(t.duration_minutes for t in self.scheduled_tasks)

    def get_summary(self) -> str:
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
        """Build a plan from all pending tasks across every pet."""
        plan = DailyPlan(date=date.today())
        pending = [t for t in self.owner.get_all_tasks() if not t.is_completed]
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

    def fits_in_time(self, tasks: list[Task]) -> bool:
        return sum(t.duration_minutes for t in tasks) <= self.owner.available_minutes

    def explain_plan(self, plan: DailyPlan) -> list[str]:
        return [plan.explanations[t.id]
                for t in plan.scheduled_tasks + plan.skipped_tasks
                if t.id in plan.explanations]
