"""
SurakshaPath AI — Embedded Cooperative Task Scheduler.

Single-threaded, non-blocking task runner designed specifically for MicroPython.

Design Rules:
  - ZERO threading, asyncio, or multiprocessing dependencies.
  - Periodic task registration with configurable millisecond intervals.
  - Deterministic execution using ticks_ms() / ticks_diff().
  - Suitable for resource-constrained microcontrollers (ESP32/RP2040).
"""

from __future__ import annotations

from typing import Callable, List, Dict, Optional
from firmware.micropython.compat import get_ticks_ms, ticks_diff


class Task:
    """A scheduled cooperative task.

    Attributes:
        name:        Human-readable task identifier.
        interval_ms: Task execution frequency in milliseconds.
        callback:    Function to execute when interval expires.
        last_run_ms: Last tick count when task was executed.
        enabled:     True if task is active.
    """

    def __init__(self, name: str, interval_ms: int, callback: Callable[[], None]) -> None:
        self.name = name
        self.interval_ms = max(1, interval_ms)
        self.callback = callback
        self.last_run_ms = 0
        self.enabled = True


class CooperativeScheduler:
    """Single-threaded cooperative task scheduler."""

    def __init__(self) -> None:
        """Initialize CooperativeScheduler."""
        self._tasks: List[Task] = []
        self._virtual_ticks_ms: Optional[int] = None

    def add_task(self, name: str, interval_ms: int, callback: Callable[[], None]) -> Task:
        """Register a new periodic task.

        Args:
            name: Task identifier name.
            interval_ms: Interval between executions in milliseconds.
            callback: Function to invoke when timer triggers.

        Returns:
            The registered Task object.
        """
        task = Task(name=name, interval_ms=interval_ms, callback=callback)
        self._tasks.append(task)
        return task

    def remove_task(self, name: str) -> bool:
        """Remove a task by name."""
        initial_len = len(self._tasks)
        self._tasks = [t for t in self._tasks if t.name != name]
        return len(self._tasks) < initial_len

    def set_task_enabled(self, name: str, enabled: bool) -> bool:
        """Enable or disable a task by name."""
        for t in self._tasks:
            if t.name == name:
                t.enabled = enabled
                return True
        return False

    def run_once(self, current_time_ms: Optional[int] = None) -> int:
        """Check all tasks and execute any expired tasks once.

        Args:
            current_time_ms: Optional explicit tick count (for testing/simulation).

        Returns:
            Number of tasks executed during this run.
        """
        now = current_time_ms if current_time_ms is not None else get_ticks_ms()
        executed_count = 0

        for task in self._tasks:
            if not task.enabled:
                continue

            elapsed = ticks_diff(now, task.last_run_ms)
            if elapsed >= task.interval_ms or task.last_run_ms == 0:
                task.last_run_ms = now
                try:
                    task.callback()
                    executed_count += 1
                except Exception as e:
                    print(f"[SCHEDULER ERR] Task '{task.name}' raised exception: {e}")

        return executed_count

    def step(self, elapsed_ms: int) -> int:
        """Advance virtual clock by `elapsed_ms` and run expired tasks.

        Useful for unit tests and simulation ticks.

        Args:
            elapsed_ms: Milliseconds to advance.

        Returns:
            Total tasks executed during step.
        """
        if self._virtual_ticks_ms is None:
            self._virtual_ticks_ms = get_ticks_ms()
        
        self._virtual_ticks_ms += elapsed_ms
        return self.run_once(current_time_ms=self._virtual_ticks_ms)
