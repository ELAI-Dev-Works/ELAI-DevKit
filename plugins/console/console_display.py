# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QTextEdit, QMenu, QApplication
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QCursor


class ConsoleDisplay(QTextEdit):
    """A QTextEdit that makes URLs clickable and adds context menu actions."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setProperty("no_custom_tooltip", True)
        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Ctrl+Click opens the link
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                url = self.anchorAt(event.pos())
                if url:
                    QDesktopServices.openUrl(QUrl(url))
                    event.accept()
                    return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            url = self.anchorAt(event.pos())
            if url:
                QDesktopServices.openUrl(QUrl(url))
                event.accept()
                return
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        url = self.anchorAt(event.pos())
        if url:
            menu.addSeparator()
            open_action = menu.addAction("Open in Browser")
            open_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
        menu.exec(event.globalPos())

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)