from .backend.python_async import PythonAsyncLoop
import asyncio

class AsyncControl:
    """Unified API for asynchronous execution."""
    
    def __init__(self):
        self.py_async = PythonAsyncLoop()

    def run_coroutine(self, coro, callback=None):
        """
        Schedules a coroutine. 
        Returns a concurrent.futures.Future that can be awaited or checked.
        """
        future = self.py_async.run_coroutine(coro)
        if callback:
            future.add_done_callback(lambda f: callback(f.result()))
        return future

    def run_with_timeout(self, coro, timeout: float, callback=None):
        """Runs a coroutine with a specified timeout."""
        async def _wrapper():
            return await asyncio.wait_for(coro, timeout=timeout)
        return self.run_coroutine(_wrapper(), callback)

    def gather(self, coros: list, callback=None):
        """Runs multiple coroutines concurrently and waits for all to finish."""
        async def _wrapper():
            return await asyncio.gather(*coros)
        return self.run_coroutine(_wrapper(), callback)

    def run_in_executor(self, func, callback=None, *args, **kwargs):
        """Runs a synchronous blocking function in a background executor within the async loop."""
        import functools
        async def _wrapper():
            loop = asyncio.get_running_loop()
            bound_func = functools.partial(func, *args, **kwargs)
            return await loop.run_in_executor(None, bound_func)
        return self.run_coroutine(_wrapper(), callback)

    def run_subprocess(self, cmd: list, cwd: str = None, callback=None):
        """
        Safely runs a subprocess asynchronously and returns (returncode, stdout, stderr).
        Uses `to_thread` for extreme stability across all OS EventLoops.
        """
        import subprocess
        async def _wrapper():
            return await asyncio.to_thread(
                subprocess.run, cmd, cwd=cwd, capture_output=True, text=True, errors='replace'
            )
        return self.run_coroutine(_wrapper(), callback)

    def shutdown(self):
        self.py_async.stop()