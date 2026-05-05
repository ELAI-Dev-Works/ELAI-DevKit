import unittest
import sys
from systems.async_thread.tasks import SubprocessStreamTask
from systems.async_thread.thread_control import ThreadControl

class TestSubprocessStreamTask(unittest.TestCase):
    def test_subprocess_stream(self):
        tc = ThreadControl()
        yields = []
        cmd =[sys.executable, "-u", "-c", "import sys; print('STREAM_1'); print('STREAM_2'); sys.stdout.flush()"]
        task = SubprocessStreamTask(cmd)

        worker = tc.run_in_background(task, yield_callback=yields.append, use_qt=False)
        res = worker.future.result(timeout=15)

        self.assertEqual(res, 0)
        self.assertTrue(any("STREAM_1" in y for y in yields))
        self.assertTrue(any("STREAM_2" in y for y in yields))
        tc.shutdown()

if __name__ == '__main__':
    unittest.main()