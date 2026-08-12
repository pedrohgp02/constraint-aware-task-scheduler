from scheduler import Scheduler, Task


def main() -> None:
    tasks = [
        Task(1, "Morning class", 90, time_window=8 * 60),
        Task(2, "Lunch", 60, time_window=(12 * 60, 14 * 60)),
        Task(3, "Research", 60),
        Task(4, "Write report", 90, dependencies=[3]),
        Task(5, "Gym", 60, time_window=(16 * 60, 18 * 60)),
    ]

    scheduler = Scheduler(tasks, start_time=7 * 60, end_time=19 * 60)
    scheduler.run()
    scheduler.print_schedule()

    if scheduler.missed_tasks:
        print("\nMissed tasks:")
        for task in scheduler.missed_tasks:
            print(f"- {task.description}")


if __name__ == "__main__":
    main()
