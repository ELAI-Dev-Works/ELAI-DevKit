import os
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import Qt, QSize

class IconManager:
    """
    Dynamic Icon Manager compatible with the Extension System.
    Uses 'uid.icon_name' syntax (e.g., 'core.home', 'dev_patcher.refresh').
    """
    _app_root = None
    _extension_manager = None
    _cache_svg = {}
    _cache_icon = {}
    _cache_pixmap = {}

    @classmethod
    def clear_cache(cls):
        """Clears the icon cache to free memory or force reload."""
        cls._cache_svg.clear()
        cls._cache_icon.clear()
        cls._cache_pixmap.clear()

    @classmethod
    def init_paths(cls, app_root, extension_manager=None):
        cls._app_root = app_root
        cls._extension_manager = extension_manager

    @classmethod
    def _resolve_path(cls, icon_ref: str) -> str:
        """Resolves 'uid.filename' or 'uid:filename' to an absolute path."""
        if '.' in icon_ref:
            uid, icon_name = icon_ref.split('.', 1)
        elif ':' in icon_ref:
            uid, icon_name = icon_ref.split(':', 1)
        else:
            uid = 'core'
            icon_name = icon_ref

        if not icon_name.endswith('.svg'):
            icon_name += '.svg'

        # 1. Check Core
        if uid == 'core' and cls._app_root:
            return os.path.join(cls._app_root, 'assets', 'icons', icon_name)

        # 2. Check Extension Manager
        if cls._extension_manager and uid in cls._extension_manager.extensions:
            ext_path = cls._extension_manager.extensions[uid]['path']
            return os.path.join(ext_path, 'assets', 'icons', icon_name)

        # 3. Fallback manual search if manager isn't ready or UID not loaded
        if cls._app_root:
            app_path = os.path.join(cls._app_root, 'apps', uid, 'assets', 'icons', icon_name)
            if os.path.exists(app_path): return app_path

            ext_path = os.path.join(cls._app_root, 'extensions', 'custom_apps', uid, 'assets', 'icons', icon_name)
            if os.path.exists(ext_path): return ext_path

            ext_cmd_path = os.path.join(cls._app_root, 'extensions', 'custom_commands', uid, 'assets', 'icons', icon_name)
            if os.path.exists(ext_cmd_path): return ext_cmd_path

        return None

    @classmethod
    def get_svg(cls, icon_ref: str) -> str:
        if icon_ref in cls._cache_svg:
            return cls._cache_svg[icon_ref]

        path = cls._resolve_path(icon_ref)
        if path and os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    cls._cache_svg[icon_ref] = content
                    return content
            except Exception as e:
                print(f"IconManager Warning: Error reading icon {path}: {e}")

        print(f"IconManager Warning: Icon not found for ref '{icon_ref}'")
        return '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"><path d="M0 0h24v24H0z" fill="red"/></svg>'

    @classmethod
    def get_pixmap(cls, icon_ref: str, color: str = "#ffffff", size: int = None) -> QPixmap:
        """
        Returns a QPixmap with the specific color and size.
        """
        cache_key = f"pixmap_{icon_ref}_{color}_{size}"
        if cache_key in cls._cache_pixmap:
            return cls._cache_pixmap[cache_key]

        svg_str = cls.get_svg(icon_ref)
        colored_svg = svg_str.replace("currentColor", color).encode('utf-8')

        renderer = QSvgRenderer(colored_svg)

        if size:
            render_size = QSize(size, size)
        else:
            # Default to high resolution for clear QIcon downscaling
            render_size = QSize(128, 128)

        pixmap = QPixmap(render_size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.render(painter)
        painter.end()

        cls._cache_pixmap[cache_key] = pixmap
        return pixmap

    @classmethod
    def get_icon(cls, icon_ref: str, color="#ffffff", size: int = None) -> QIcon:
        """
        Returns a standard QIcon of the requested color.
        """
        cache_key = f"icon_{icon_ref}_{color}_{size}"
        if cache_key in cls._cache_icon:
            return cls._cache_icon[cache_key]

        pixmap = cls.get_pixmap(icon_ref, color, size)
        icon = QIcon(pixmap)
        cls._cache_icon[cache_key] = icon
        return icon

    @classmethod
    def get_stateful_icon(cls, icon_ref: str, normal_color: str, active_color: str = None, disabled_color: str = None, size: int = None) -> QIcon:
        """
        Returns a QIcon with different colors for different states (Normal, Active, Disabled).
        Great for QPushButtons to handle hover/pressed states automatically.
        """
        cache_key = f"stateful_{icon_ref}_{normal_color}_{active_color}_{disabled_color}_{size}"
        if cache_key in cls._cache_icon:
            return cls._cache_icon[cache_key]

        icon = QIcon()

        # Normal State
        norm_pix = cls.get_pixmap(icon_ref, color=normal_color, size=size)
        icon.addPixmap(norm_pix, QIcon.Mode.Normal, QIcon.State.Off)

        # Active (Hover / Pressed) State
        if active_color:
            act_pix = cls.get_pixmap(icon_ref, color=active_color, size=size)
            icon.addPixmap(act_pix, QIcon.Mode.Active, QIcon.State.Off)
            icon.addPixmap(act_pix, QIcon.Mode.Selected, QIcon.State.Off)

        # Disabled State
        if disabled_color:
            dis_pix = cls.get_pixmap(icon_ref, color=disabled_color, size=size)
            icon.addPixmap(dis_pix, QIcon.Mode.Disabled, QIcon.State.Off)

        cls._cache_icon[cache_key] = icon
        return icon