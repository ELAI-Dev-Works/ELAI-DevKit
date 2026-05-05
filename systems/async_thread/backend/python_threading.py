import threading
from typing import Callable

class PythonThreadManager:
    """Provides utility methods for raw Python threading."""

    @staticmethod
    def run_in_thread(target: Callable, name: str = None, daemon: bool = True, 
                      result_cb: Callable = None, error_cb: Callable = None, 
                      yield_cb: Callable = None, *args, **kwargs) -> threading.Thread:
        """Runs a standard python thread with callback support for generators."""
        import inspect

        def _wrapper():
            try:
                from systems.error_handler.thread_tracer import ThreadTracer
                mod_name = getattr(target, '__module__', 'unknown_module')
                func_name = getattr(target, '__name__', 'unknown_function')
                ThreadTracer.log_action(mod_name, func_name, "Python Thread dedicated execution started")

                res = target(*args, **kwargs)
                if inspect.isgenerator(res):
                    last_val = None
                    try:
                        while True:
                            item = next(res)
                            if yield_cb: yield_cb(item)
                            last_val = item
                    except StopIteration as e:
                        if e.value is not None:
                            res = e.value
                        else:
                            res = last_val
                    if result_cb: result_cb(res)
                else:
                    if result_cb: result_cb(res)
                ThreadTracer.log_action(mod_name, func_name, "Python Thread dedicated execution finished successfully")
            except Exception as e:
                try:
                    from systems.error_handler.thread_tracer import ThreadTracer
                    mod_name = getattr(target, '__module__', 'unknown_module')
                    func_name = getattr(target, '__name__', 'unknown_function')
                    ThreadTracer.log_action(mod_name, func_name, f"Python Thread dedicated execution failed: {e}")
                except Exception:
                    pass
                if error_cb: error_cb(e)
                else: raise e

        thread = threading.Thread(target=_wrapper, name=name, daemon=daemon)
        thread.start()
        return thread