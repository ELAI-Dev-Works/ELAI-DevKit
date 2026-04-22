import sys
from PySide6.QtCore import qInstallMessageHandler, QtMsgType
from .logger import log_qt_message

def qt_message_handler(mode, context, message):
    """
    Captures Qt internal messages (qDebug, qWarning, etc.) and logs them.
    This helps diagnose PySide6/C++ issues that don't raise Python exceptions.
    """
    msg_type_str = "Debug"
    if mode == QtMsgType.QtInfoMsg: msg_type_str = "Info"
    elif mode == QtMsgType.QtWarningMsg: msg_type_str = "Warning"
    elif mode == QtMsgType.QtCriticalMsg: msg_type_str = "Critical"
    elif mode == QtMsgType.QtFatalMsg: msg_type_str = "Fatal"

    # Context info (file, line, function)
    context_str = ""
    if context and context.file:
        context_str = f"({context.file}:{context.line}, {context.function})"

    # Log to file
    log_qt_message(msg_type_str, message, context_str)

    # Also print to stderr so it appears in console
    full_msg = f"[Qt {msg_type_str}] {message} {context_str}"
    print(full_msg, file=sys.stderr)

def setup_qt_handling():
    qInstallMessageHandler(qt_message_handler)
    print("[ErrorHandler] Qt message handler installed.")