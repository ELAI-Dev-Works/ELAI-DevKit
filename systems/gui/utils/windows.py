from PySide6.QtWidgets import QApplication

def center_window(window, parent=None):
    """Centers a window on its parent or the primary screen."""
    if parent and parent.isVisible():
        center_point = parent.geometry().center()
    else:
        screen = QApplication.primaryScreen().availableGeometry()
        center_point = screen.center()

    geo = window.geometry()
    geo.moveCenter(center_point)
    window.setGeometry(geo)