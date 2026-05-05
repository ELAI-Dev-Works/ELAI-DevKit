# This module acts as a compatibility layer and public API for the console plugin.
# The implementation has been split into separate modules for better organization.

from .palette import ANSI_COLORS, ANSI_COLORS_BRIGHT, BG_DEFAULT
from .console_display import ConsoleDisplay
from .history_dialog import FullHistoryDialog
from .console_widget import ConsoleWidget

__all__ = [
    "ANSI_COLORS",
    "ANSI_COLORS_BRIGHT",
    "BG_DEFAULT",
    "ConsoleDisplay",
    "FullHistoryDialog",
    "ConsoleWidget",
]