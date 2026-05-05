from .thread_control import ThreadControl
from .tasks import SubprocessStreamTask
from .process_utils import ProcessManager
from .async_control import AsyncControl
from .bridge import SignalBridge

class AsyncThreadManager:
    """
    Global manager for the ELAI-DevKit multi-threading and async architecture.
    Initializes and exposes unified controls.
    """
    def __init__(self, context):
        self.context = context
        
        # Sub-controllers
        self.thread = ThreadControl()
        self.async_exec = AsyncControl()
        self.bridge = SignalBridge()


        # Utilities
        self.SubprocessTask = SubprocessStreamTask
        self.process_utils = ProcessManager


    def shutdown(self):
        """Safely tears down background thread pools and event loops."""
        self.thread.shutdown()
        self.async_exec.shutdown()