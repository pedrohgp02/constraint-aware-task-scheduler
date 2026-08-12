"""Constraint-aware priority scheduler.

Core implementation extracted and cleaned from the original CS110 scheduler project.
Tasks can be fixed-time, bounded by a time window, flexible, and dependent on
other tasks. A custom max-heap selects the highest-priority schedulable task.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

TimeWindow = Optional[Union[int, tuple[int, int]]]


class MaxHeapq:
    """A max-heap priority queue implemented on top of a Python list."""

    def __init__(self) -> None:
        self.heap: list[tuple[float, "Task"]] = []

    def __len__(self) -> int:
        return len(self.heap)

    @staticmethod
    def _left(i: int) -> int:
        return 2 * i + 1

    @staticmethod
    def _right(i: int) -> int:
        return 2 * i + 2

    @staticmethod
    def _parent(i: int) -> int:
        return (i - 1) // 2

    def heappush(self, item: tuple[float, "Task"]) -> None:
        self.heap.append(item)
        i = len(self.heap) - 1
        while i > 0:
            parent = self._parent(i)
            if self.heap[parent][0] >= self.heap[i][0]:
                break
            self.heap[parent], self.heap[i] = self.heap[i], self.heap[parent]
            i = parent

    def heappop(self) -> tuple[float, "Task"]:
        if not self.heap:
            raise IndexError("pop from empty heap")
        if len(self.heap) == 1:
            return self.heap.pop()

        root = self.heap[0]
        self.heap[0] = self.heap.pop()
        self._heapify(0)
        return root

    def _heapify(self, i: int) -> None:
        while True:
            largest = i
            left = self._left(i)
            right = self._right(i)

            if left < len(self.heap) and self.heap[left][0] > self.heap[largest][0]:
                largest = left
            if right < len(self.heap) and self.heap[right][0] > self.heap[largest][0]:
                largest = right
            if largest == i:
                return

            self.heap[i], self.heap[largest] = self.heap[largest], self.heap[i]
            i = largest


@dataclass
class Task:
    """A schedulable unit of work.

    time_window can be:
    - None: fully flexible
    - int: fixed start time, in minutes after midnight
    - tuple(start, end): bounded scheduling window
    """

    task_id: int
    description: str
    duration: int
    dependencies: list[int] | None = None
    time_window: TimeWindow = None
    priority: float = 0
    status: str = "not_yet_started"

    def __post_init__(self) -> None:
        self.dependencies = list(self.dependencies or [])

    def calculate_priority(
        self,
        current_time: int,
        dependency_weight: float = 5,
        duration_weight: float = 1,
        urgency_weight: float = 10,
    ) -> float:
        dependency_penalty = len(self.dependencies) * dependency_weight
        duration_penalty = self.duration * duration_weight / 20

        if isinstance(self.time_window, int):
            urgency_bonus = urgency_weight * 15
        elif isinstance(self.time_window, tuple):
            start_time, end_time = self.time_window
            if current_time >= end_time:
                urgency_bonus = -100
            elif current_time >= start_time:
                width = max(end_time - start_time, 1)
                urgency_bonus = urgency_weight * (
                    1 + (current_time - start_time) / width
                )
            else:
                urgency_bonus = urgency_weight
        else:
            urgency_bonus = urgency_weight

        self.priority = 100 - dependency_penalty - duration_penalty + urgency_bonus
        return self.priority


class Scheduler:
    """Greedy constraint-aware scheduler backed by a custom max-heap."""

    def __init__(self, tasks: list[Task], start_time: int = 8 * 60, end_time: int = 22 * 60) -> None:
        self.tasks = tasks
        self.start_time = start_time
        self.end_time = end_time
        self.current_time = start_time
        self.completed_tasks: list[Task] = []
        self.schedule: list[dict[str, object]] = []
        self.missed_tasks: list[Task] = []
        self.heap = MaxHeapq()

    def dependencies_completed(self, task: Task) -> bool:
        completed_ids = {item.task_id for item in self.completed_tasks}
        return all(dep in completed_ids for dep in task.dependencies)

    def has_conflict(self, start_time: int, end_time: int) -> bool:
        for entry in self.schedule:
            existing_start = int(entry["start_time"])
            existing_end = int(entry["end_time"])
            if start_time < existing_end and end_time > existing_start:
                return True
        return False

    def _record(self, task: Task, start_time: int, end_time: int) -> None:
        task.status = "completed"
        self.schedule.append(
            {
                "task_id": task.task_id,
                "description": task.description,
                "start_time": start_time,
                "end_time": end_time,
                "priority": task.priority,
            }
        )
        if task not in self.completed_tasks:
            self.completed_tasks.append(task)

    def schedule_dependencies(self, task: Task) -> bool:
        task_lookup = {item.task_id: item for item in self.tasks}
        for dep_id in task.dependencies:
            if dep_id in {item.task_id for item in self.completed_tasks}:
                continue
            dependency = task_lookup.get(dep_id)
            if dependency is None:
                return False
            if not self.schedule_dependencies(dependency):
                return False
            if dependency.status == "not_yet_started" and not self.find_time_slot(dependency):
                return False
        return True

    def schedule_fixed_time_tasks(self, unscheduled_tasks: list[Task]) -> None:
        fixed = [task for task in unscheduled_tasks if isinstance(task.time_window, int)]
        for task in sorted(fixed, key=lambda item: int(item.time_window)):
            if not self.schedule_dependencies(task):
                task.status = "missed"
                self.missed_tasks.append(task)
                continue

            start = int(task.time_window)
            end = start + task.duration
            task.calculate_priority(start)

            if start < self.start_time or end > self.end_time or self.has_conflict(start, end):
                task.status = "missed"
                self.missed_tasks.append(task)
                continue

            self._record(task, start, end)
            if task in unscheduled_tasks:
                unscheduled_tasks.remove(task)

    def find_time_slot(self, task: Task) -> bool:
        if isinstance(task.time_window, int):
            start = int(task.time_window)
            end = start + task.duration
            if start < self.start_time or end > self.end_time or self.has_conflict(start, end):
                return False
            self._record(task, start, end)
            return True

        if isinstance(task.time_window, tuple):
            window_start, window_end = task.time_window
            candidate = max(self.current_time, window_start)
            latest_end = min(window_end, self.end_time)
        else:
            candidate = self.current_time
            latest_end = self.end_time

        while candidate + task.duration <= latest_end:
            end = candidate + task.duration
            if not self.has_conflict(candidate, end):
                self._record(task, candidate, end)
                self.current_time = end
                return True
            candidate += 15

        return False

    def run(self) -> list[dict[str, object]]:
        unscheduled = [task for task in self.tasks if task.status == "not_yet_started"]
        self.schedule_fixed_time_tasks(unscheduled)
        unscheduled = [task for task in unscheduled if task.status == "not_yet_started"]

        while self.current_time < self.end_time and unscheduled:
            self.heap = MaxHeapq()
            for task in unscheduled:
                if self.dependencies_completed(task):
                    task.calculate_priority(self.current_time)
                    self.heap.heappush((task.priority, task))

            if len(self.heap) == 0:
                future_fixed = [
                    int(entry["start_time"])
                    for entry in self.schedule
                    if int(entry["start_time"]) > self.current_time
                ]
                self.current_time = min(future_fixed) if future_fixed else self.current_time + 60
                continue

            _, task = self.heap.heappop()
            if self.find_time_slot(task):
                unscheduled.remove(task)
            else:
                task.status = "missed"
                self.missed_tasks.append(task)
                unscheduled.remove(task)

        for task in unscheduled:
            if task.status == "not_yet_started":
                task.status = "missed"
                self.missed_tasks.append(task)

        self.schedule.sort(key=lambda entry: int(entry["start_time"]))
        return self.schedule

    @staticmethod
    def format_time(minutes: int) -> str:
        return f"{minutes // 60:02d}:{minutes % 60:02d}"

    def print_schedule(self) -> None:
        for entry in self.schedule:
            start = self.format_time(int(entry["start_time"]))
            end = self.format_time(int(entry["end_time"]))
            print(f"{start}-{end}  {entry['description']}")
