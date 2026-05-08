import unittest
import time
import sys
import asyncio
from systems.async_thread.async_control import AsyncControl

class TestAsyncControl(unittest.TestCase):
    def test_01_async_execution(self):
        ac = AsyncControl()
        result_box =[]

        async def my_coro():
            await asyncio.sleep(0.05)
            return "ASYNC_OK"

        future = ac.run_coroutine(my_coro(), callback=result_box.append)
        res = future.result(timeout=10)
        time.sleep(0.05)  # Wait for callback

        self.assertEqual(res, "ASYNC_OK")
        self.assertIn("ASYNC_OK", result_box)
        ac.shutdown()

    def test_02_async_gather(self):
        ac = AsyncControl()
        async def coro1(): return 1
        async def coro2(): return 2

        future = ac.gather([coro1(), coro2()])
        res = future.result(timeout=10)
        self.assertEqual(res, [1, 2])
        ac.shutdown()

    def test_03_async_timeout(self):
        ac = AsyncControl()
        async def slow_coro():
            await asyncio.sleep(2)
            return "done"

        future = ac.run_with_timeout(slow_coro(), timeout=1)
        with self.assertRaises(Exception): # Catches asyncio.TimeoutError safely
            future.result(timeout=10)
        ac.shutdown()

    def test_04_async_run_in_executor(self):
        ac = AsyncControl()
        def blocking_task():
            time.sleep(0.1)
            return "blocked_done"

        future = ac.run_in_executor(blocking_task)
        res = future.result(timeout=10)
        self.assertEqual(res, "blocked_done")
        ac.shutdown()

    def test_05_async_subprocess(self):
        ac = AsyncControl()
        if sys.platform == 'win32':
            cmd =["cmd.exe", "/c", "echo SUBPROCESS_OK"]
        else:
            cmd = ["echo", "SUBPROCESS_OK"]
        future = ac.run_subprocess(cmd)
        res = future.result(timeout=30)
        self.assertEqual(res.returncode, 0)
        self.assertIn("SUBPROCESS_OK", res.stdout)
        ac.shutdown()

if __name__ == '__main__':
    unittest.main()