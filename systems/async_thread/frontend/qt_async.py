from PySide6.QtCore import QTimer
import asyncio

class QtAsyncIntegration:
    """
    Provides bridging mechanisms to run async code inside Qt loops.
    For more complex systems, libraries like `qasync` are recommended, 
    but this provides standard async offloading without extra dependencies.
    """
    @staticmethod
    def process_async_task(coro):
        """
        Creates a task and runs it. Works best if a qasync event loop is active.
        If standard asyncio is used, it should be passed to the backend `PythonAsyncLoop`.
        """
        return asyncio.create_task(coro)