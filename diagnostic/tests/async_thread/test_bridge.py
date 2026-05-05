import unittest
import sys
from PySide6.QtCore import QCoreApplication, QEventLoop, QTimer
from systems.async_thread.bridge import SignalBridge

class TestSignalBridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QCoreApplication.instance():
            cls.app = QCoreApplication(sys.argv)
        else:
            cls.app = QCoreApplication.instance()

    def test_01_signal_bridge_generic(self):
        bridge = SignalBridge()
        res_box =[]
        bridge.subscribe("test_event", res_box.append)
        bridge.emit_safe("test_event", "Hello")

        loop = QEventLoop()
        QTimer.singleShot(100, loop.quit)
        loop.exec()

        self.assertIn("Hello", res_box)

    def test_02_signal_bridge_progress(self):
        bridge = SignalBridge()
        res_box =[]
        bridge.subscribe_progress("test_prog", lambda c, t: res_box.append((c, t)))
        bridge.emit_progress("test_prog", 5, 10)

        loop = QEventLoop()
        QTimer.singleShot(100, loop.quit)
        loop.exec()

        self.assertIn((5, 10), res_box)

    def test_03_signal_bridge_error(self):
        bridge = SignalBridge()
        res_box =[]
        bridge.subscribe_error("test_err", res_box.append)
        
        ex = ValueError("Test Exception Bridge")
        bridge.emit_error("test_err", ex)

        loop = QEventLoop()
        QTimer.singleShot(100, loop.quit)
        loop.exec()

        self.assertIn(ex, res_box)

if __name__ == '__main__':
    unittest.main()