"""PawPal+ logic layer: backend classes for owners, pets, tasks, and scheduling."""

from dataclasses import dataclass, field
from datetime import date


@dataclass
class Task:
    id: int
    title: str
    category: str
    duration_minutes: int
    priority: str
    preferred_time: str = ""
    is_completed: bool = False

    def mark_complete(self) -> None:
        pass

    def update(self, changes: dict) -> None:
        pass


@dataclass
class Pet:
    name: str
    species: str
    age: int
    special_needs: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        pass

    def remove_task(self, task_id: int) -> None:
        pass

    def edit_task(self, task_id: int, changes: dict) -> None:
        pass

    def get_pending_tasks(self) -> list[Task]:
        pass


@dataclass
class Owner:
    name: str
    available_minutes: int
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        pass

    def update_availability(self, minutes: int) -> None:
        pass

    def set_preference(self, key: str, value) -> None:
        pass

    def get_all_tasks(self) -> list[Task]:
        pass


@dataclass
class DailyPlan:
    date: date
    scheduled_tasks: list[Task] = field(default_factory=list)
    skipped_tasks: list[Task] = field(default_factory=list)
    explanations: dict = field(default_factory=dict)

    def add_entry(self, task: Task, reason: str) -> None:
        pass

    def get_total_minutes(self) -> int:
        pass

    def get_summary(self) -> str:
        pass


@dataclass
class Scheduler:
    owner: Owner

    def generate_plan(self) -> DailyPlan:
        pass

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        pass

    def fits_in_time(self, tasks: list[Task]) -> bool:
        pass

    def explain_plan(self, plan: DailyPlan) -> list[str]:
        pass
