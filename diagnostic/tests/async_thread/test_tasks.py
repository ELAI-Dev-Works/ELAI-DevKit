import unittest
import sys
from systems.async_thread.tasks import SubprocessStreamTask
from systems.async_thread.thread_control import ThreadControl

class TestSubprocessStreamTask(unittest.TestCase):
    def test_subprocess_stream(self):
        tc = ThreadControl()
        yields = []
        if sys.platform == 'win32':
            cmd =["cmd.exe", "/c", "echo STREAM_1& echo STREAM_2"]
        else:
            cmd =["sh", "-c", "echo STREAM_1; echo STREAM_2"]
        task = SubprocessStreamTask(cmd)

        worker = tc.run_in_background(task, yield_callback=yields.append, use_qt=False)
        res = worker.future.result(timeout=30)

        self.assertEqual(res, 0)
        self.assertTrue(any("STREAM_1" in y for y in yields))
        self.assertTrue(any("STREAM_2" in y for y in yields))
        tc.shutdown()

if __name__ == '__main__':
    unittest.main()