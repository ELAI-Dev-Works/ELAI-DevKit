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
ICON_MAIN_SETTINGS = "main_settings.svg"
ICON_QUICK_SETTINGS = "quick_settings.svg"
ICON_EXTENSIONS = "extensions.svg"
ICON_HOME = "home.svg"
ICON_BACK = "back.svg"

# --- New Icons ---
ICON_BOOKMARKS = "bookmarks.svg"
ICON_RESTART = "restart.svg"
ICON_REFRESH = "refresh.svg"
ICON_CATEGORIES = "categories.svg"
ICON_PLUS = "plus.svg"
ICON_EDIT = "edit.svg"

_cache = {}

def _find_icon_path(icon_name: str) -> str:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    # Paths to search
    search_paths =[
        os.path.join(base_dir, 'assets', 'icons')
    ]
    
    apps_dir = os.path.join(base_dir, 'apps')
    if os.path.exists(apps_dir):
        for app in os.listdir(apps_dir):
            search_paths.append(os.path.join(apps_dir, app, 'assets', 'icons'))
            
    ext_dir = os.path.join(base_dir, 'extensions', 'custom_apps')
    if os.path.exists(ext_dir):
        for ext in os.listdir(ext_dir):
            search_paths.append(os.path.join(ext_dir, ext, 'assets', 'icons'))
            
    for path in search_paths:
        full_path = os.path.join(path, icon_name)
        if os.path.exists(full_path):
            return full_path
            
    return None

def get_svg_content(icon_name: str) -> str:
    """Loads SVG content from a file and caches it."""
    if icon_name in _cache:
        return _cache[icon_name]

    icon_path = _find_icon_path(icon_name)
    if icon_path:
        try:
            with open(icon_path, 'r', encoding='utf-8') as f:
                content = f.read()
                _cache[icon_name] = content
                return content
        except Exception as e:
            print(f"Warning: Error reading icon file {icon_path}: {e}")

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
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter)
    painter.end()

    return QIcon(pixmap)