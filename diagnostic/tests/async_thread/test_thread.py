import unittest
import time
import sys
from PySide6.QtCore import QCoreApplication, QEventLoop, QTimer
from systems.async_thread.thread_control import ThreadControl

class TestThreadSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # We need a QCoreApplication instance to process QThread events and Signals
        if not QCoreApplication.instance():
            cls.app = QCoreApplication(sys.argv)
        else:
            cls.app = QCoreApplication.instance()

    def test_01_dedicated_python_thread(self):
        tc = ThreadControl()
        res_box, yields = [],[]

        def task():
            yield "step1"
            yield "step2"
            return "done"

        thread = tc.run_dedicated_thread(task, callback=res_box.append, yield_callback=yields.append, use_qt=False)
        thread.join(timeout=10)
        self.assertFalse(thread.is_alive(), "Python thread timed out")
        time.sleep(0.1)

        self.assertTrue(len(res_box) > 0, "Callback was not executed")
        self.assertEqual(res_box[0], "done")
        self.assertEqual(yields,["step1", "step2"])

    def test_02_dedicated_qt_thread(self):
        tc = ThreadControl()
        res_box, yields = [],[]

        def task():
            yield "qt_step1"
            yield "qt_step2"
            return "qt_done"

        thread = tc.run_dedicated_thread(task, callback=res_box.append, yield_callback=yields.append, use_qt=True)

        loop = QEventLoop()
        thread.result_ready.connect(loop.quit)
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
        thread.wait(2000) # Properly join thread to avoid QThread Destroyed warnings

        self.assertTrue(len(res_box) > 0, "Qt thread callback was not executed")
        self.assertEqual(res_box[0], "qt_done")
        self.assertEqual(yields,["qt_step1", "qt_step2"])

    def test_03_python_worker_basic(self):
        tc = ThreadControl()
        result_box =[]
        worker = tc.run_in_background(lambda a, b: a + b, callback=result_box.append, use_qt=False, a=5, b=7)
        res = worker.future.result(timeout=10)
        time.sleep(0.1)
        self.assertEqual(res, 12)
        self.assertEqual(result_box[0], 12)

    def test_04_qt_worker_basic(self):
        tc = ThreadControl()
        result_box =[]
        worker = tc.run_in_background(lambda: "QT_OK", callback=result_box.append, use_qt=True)
        loop = QEventLoop()
        worker.signals.finished.connect(loop.quit)
        QTimer.singleShot(2000, loop.quit)
        loop.exec()
        self.assertIn("QT_OK", result_box)

    def test_05_python_worker_yield(self):
        tc = ThreadControl()
        yields =[]
        def task():
            yield 1
            yield 2
            return 3
        worker = tc.run_in_background(task, yield_callback=yields.append, use_qt=False)
        res = worker.future.result(timeout=10)
        self.assertEqual(res, 3)
        self.assertEqual(yields, [1, 2])

    def test_06_qt_worker_yield(self):
        tc = ThreadControl()
        yields, result_box = [],[]
        def task():
            yield "A"
            yield "B"
            return "C"
        worker = tc.run_in_background(task, yield_callback=yields.append, callback=result_box.append, use_qt=True)
        loop = QEventLoop()
        worker.signals.finished.connect(loop.quit)
        QTimer.singleShot(2000, loop.quit)
        loop.exec()
        self.assertEqual(yields, ["A", "B"])
        self.assertIn("C", result_box)

    def test_07_cancellation(self):
        tc = ThreadControl()
        def long_task(worker_ref=None):
            for _ in range(20):
                if getattr(worker_ref, 'is_cancelled', False): return "CANCELLED"
                time.sleep(0.1)
            return "FINISHED"
        worker = tc.run_in_background(long_task, use_qt=False, inject_worker_ref=True)
        time.sleep(0.2)
        worker.cancel()
        res = worker.future.result(timeout=3)
        self.assertEqual(res, "CANCELLED")

    def test_08_thread_pool_limit(self):
        tc = ThreadControl()
        def sleep_task():
            time.sleep(0.2)
            
        workers =[tc.run_in_background(sleep_task, use_qt=False) for _ in range(10)]
        status = tc.get_status()
        self.assertGreater(status["py_active_threads"], 0)
        self.assertGreaterEqual(status["py_pending_tasks"], 0)
        for w in workers:
            w.future.result(timeout=10)
        tc.shutdown()

if __name__ == '__main__':
    unittest.main()