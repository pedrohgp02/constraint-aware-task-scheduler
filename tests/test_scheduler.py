import pytest

from scheduler import MaxHeapq, Scheduler, Task


def test_max_heap_returns_descending_priorities():
    heap = MaxHeapq()
    tasks = [Task(1, "A", 10), Task(2, "B", 10), Task(3, "C", 10)]
    heap.heappush((5, tasks[0]))
    heap.heappush((10, tasks[1]))
    heap.heappush((7, tasks[2]))

    assert [heap.heappop()[0], heap.heappop()[0], heap.heappop()[0]] == [10, 7, 5]


def test_max_heap_empty_pop_raises():
    heap = MaxHeapq()
    with pytest.raises(IndexError):
        heap.heappop()


def test_reference_schedule_is_input_order_invariant():
    tasks_a = [
        Task(1, "Task A", 60, time_window=(8 * 60, 10 * 60)),
        Task(2, "Task B", 30, time_window=(8 * 60, 9 * 60)),
        Task(3, "Task C", 45),
    ]
    tasks_b = [
        Task(3, "Task C", 45),
        Task(1, "Task A", 60, time_window=(8 * 60, 10 * 60)),
        Task(2, "Task B", 30, time_window=(8 * 60, 9 * 60)),
    ]

    schedule_a = Scheduler(tasks_a, start_time=7 * 60, end_time=12 * 60).run()
    schedule_b = Scheduler(tasks_b, start_time=7 * 60, end_time=12 * 60).run()

    simplified_a = [(x["task_id"], x["start_time"], x["end_time"]) for x in schedule_a]
    simplified_b = [(x["task_id"], x["start_time"], x["end_time"]) for x in schedule_b]
    assert simplified_a == simplified_b


def test_dependency_is_scheduled_before_dependent_task():
    tasks = [
        Task(1, "Research", 60),
        Task(2, "Write report", 60, dependencies=[1]),
    ]
    schedule = Scheduler(tasks, start_time=8 * 60, end_time=12 * 60).run()
    ids = [entry["task_id"] for entry in schedule]
    assert ids == [1, 2]


def test_conflicting_fixed_time_task_is_missed():
    tasks = [
        Task(1, "Class", 60, time_window=9 * 60),
        Task(2, "Meeting", 60, time_window=9 * 60),
    ]
    scheduler = Scheduler(tasks, start_time=8 * 60, end_time=12 * 60)
    schedule = scheduler.run()

    assert len(schedule) == 1
    assert len(scheduler.missed_tasks) == 1
