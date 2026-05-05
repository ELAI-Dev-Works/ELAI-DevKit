import unittest
from systems.async_thread.exec_priority import TaskPriority, get_qt_priority
from PySide6.QtCore import QThread

class TestExecPriority(unittest.TestCase):
    def test_task_priority_values(self):
        self.assertEqual(TaskPriority.LOW, 0)
        self.assertEqual(TaskPriority.NORMAL, 1)
        self.assertEqual(TaskPriority.HIGH, 2)
        self.assertEqual(TaskPriority.CRITICAL, 3)

    def test_get_qt_priority(self):
        self.assertEqual(get_qt_priority(TaskPriority.LOW), QThread.Priority.LowPriority)
        self.assertEqual(get_qt_priority(TaskPriority.NORMAL), QThread.Priority.NormalPriority)
        self.assertEqual(get_qt_priority(TaskPriority.HIGH), QThread.Priority.HighPriority)
        self.assertEqual(get_qt_priority(TaskPriority.CRITICAL), QThread.Priority.HighestPriority)

if __name__ == '__main__':
    unittest.main()