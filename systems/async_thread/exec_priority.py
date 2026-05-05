from enum import IntEnum

class TaskPriority(IntEnum):
    """Unified Task Priorities for both Python and Qt executors."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

def get_qt_priority(priority: TaskPriority) -> int:
    """Maps TaskPriority to QThread.Priority values."""
    from PySide6.QtCore import QThread
    mapping = {
        TaskPriority.LOW: QThread.Priority.LowPriority,
        TaskPriority.NORMAL: QThread.Priority.NormalPriority,
        TaskPriority.HIGH: QThread.Priority.HighPriority,
        TaskPriority.CRITICAL: QThread.Priority.HighestPriority
    }
    return mapping.get(priority, QThread.Priority.NormalPriority)