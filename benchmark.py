import random
import time

from scheduler import Scheduler, Task


def generate_tasks(num_tasks: int, seed: int = 42) -> list[Task]:
    rng = random.Random(seed + num_tasks)
    tasks: list[Task] = []

    for i in range(1, num_tasks + 1):
        duration = rng.choice([15, 30, 45, 60, 90])

        if rng.random() < 0.2:
            start = rng.randint(8 * 60, 19 * 60)
            end = min(start + rng.randint(60, 180), 22 * 60)
            time_window = (start, end)
        else:
            time_window = None

        max_dependencies = min(3, i - 1)
        dependencies = (
            rng.sample(range(1, i), k=rng.randint(0, max_dependencies))
            if max_dependencies > 0
            else []
        )

        tasks.append(
            Task(
                i,
                f"Task {i}",
                duration,
                dependencies=dependencies,
                time_window=time_window,
            )
        )

    return tasks


def main() -> None:
    print("tasks,seconds")
    for num_tasks in [10, 20, 50, 100, 200, 400, 600, 800, 1000]:
        tasks = generate_tasks(num_tasks)
        scheduler = Scheduler(tasks)

        start = time.perf_counter()
        scheduler.run()
        elapsed = time.perf_counter() - start

        print(f"{num_tasks},{elapsed:.6f}")


if __name__ == "__main__":
    main()
