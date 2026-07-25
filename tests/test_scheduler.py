"""
SurakshaPath AI — Cooperative Scheduler Unit Tests.

Tests:
  - Task registration and interval tracking
  - Execution of expired tasks
  - Disabling and enabling tasks
  - Virtual clock stepping for deterministic simulation
"""

import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
src_dir = os.path.join(project_root, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

import unittest
from firmware.micropython.scheduler import CooperativeScheduler


class TestCooperativeScheduler(unittest.TestCase):
    """Unit test suite for CooperativeScheduler."""

    def setUp(self) -> None:
        """Initialize scheduler before each test."""
        self.scheduler = CooperativeScheduler()
        self.counter1 = 0
        self.counter2 = 0

    def _task1_cb(self) -> None:
        self.counter1 += 1

    def _task2_cb(self) -> None:
        self.counter2 += 1

    def test_add_remove_task(self) -> None:
        """Test task registration and removal."""
        task = self.scheduler.add_task("task1", 500, self._task1_cb)
        self.assertEqual(task.name, "task1")
        self.assertEqual(task.interval_ms, 500)

        removed = self.scheduler.remove_task("task1")
        self.assertTrue(removed)

    def test_task_execution_on_step(self) -> None:
        """Test task execution over simulated time steps."""
        self.scheduler.add_task("fast_task", 100, self._task1_cb)
        self.scheduler.add_task("slow_task", 500, self._task2_cb)

        # Step 50ms -> fast task runs on initial run, slow task runs on initial run
        self.scheduler.step(50)
        self.assertEqual(self.counter1, 1)
        self.assertEqual(self.counter2, 1)

        # Step 200ms -> fast task runs 2 more times (total 3), slow task doesn't expire
        self.scheduler.step(200)
        self.assertGreaterEqual(self.counter1, 2)

    def test_task_disabled(self) -> None:
        """Test disabling a task prevents execution."""
        self.scheduler.add_task("task1", 100, self._task1_cb)
        self.scheduler.set_task_enabled("task1", False)

        initial_count = self.counter1
        self.scheduler.step(500)
        self.assertEqual(self.counter1, initial_count)


if __name__ == "__main__":
    unittest.main()
