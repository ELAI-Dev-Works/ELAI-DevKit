import os
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPainter

# --- Icon File Names ---
ICON_CODE = "code.svg"
ICON_LOGO = "ELAI-DevKit_logo.svg"
ICON_DETACH = "detach.svg"
ICON_BOOK = "book.svg"
ICON_WRENCH = "wrench.svg"
ICON_TOOLTIP = "tooltip.svg"
ICON_MAIN_SETTINGS = "main_settings.svg" # New
ICON_QUICK_SETTINGS = "quick_settings.svg" # Renamed
ICON_EXTENSIONS = "extensions.svg"
ICON_HOME = "home.svg"
ICON_BACK = "back.svg"

_cache = {}

def get_svg_content(icon_name: str) -> str:
    """Loads SVG content from a file and caches it."""
    if icon_name in _cache:
        return _cache[icon_name]

    try:
        # Build path relative to this file's location
        base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_dir, 'icons', icon_name)

        with open(icon_path, 'r', encoding='utf-8') as f:
            content = f.read()
            _cache[icon_name] = content
            return content
    except FileNotFoundError:
        print(f"Warning: Icon file not found: {icon_name}")
        # Return a placeholder SVG to avoid crashes
        return '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"><path d="M0 0h24v24H0z" fill="red"/></svg>'


def svg_to_icon(svg_str: str, color="#ffffff") -> QIcon:
    """Helper to convert SVG string to QIcon with a specific color."""
    colored_svg = svg_str.replace("currentColor", color).encode('utf-8')

    renderer = QSvgRenderer(colored_svg)
    pixmap = QPixmap(renderer.defaultSize())
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return QIcon(pixmap)