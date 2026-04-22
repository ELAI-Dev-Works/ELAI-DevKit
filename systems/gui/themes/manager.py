from PySide6.QtWidgets import QApplication
import importlib
import os

class ThemeManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.current_color_scheme = 'dark'
        self.current_theme = 'clean'
        self.current_palette = {}

    def _load_module(self, module_type, name):
        """Dynamically loads a color or style module."""
        try:
            module_path = f"systems.gui.themes.{module_type}.{name}"
            return importlib.import_module(module_path)
        except ImportError as e:
            print(f"Error loading {module_type} '{name}': {e}")
            return None

    def get_available_color_schemes(self):
        """Returns a list of available color schemes."""
        return self._scan_themes('color')

    def get_available_themes(self):
        """Returns a list of available themes."""
        return self._scan_themes('style')

    def _scan_themes(self, type_name):
        themes = []
        try:
            base_dir = os.path.dirname(__file__)
            theme_dir = os.path.join(base_dir, type_name)
            if os.path.exists(theme_dir):
                for f in os.listdir(theme_dir):
                    if f.endswith('.py') and not f.startswith('__'):
                        themes.append(f[:-3])
        except Exception as e:
            print(f"Error scanning themes: {e}")
        return sorted(themes)

    def apply_theme(self, color_scheme_name: str, theme_name: str):
        """Applies a theme by combining a color palette and a style."""
        app = QApplication.instance()

        color_module = self._load_module('color', color_scheme_name)
        style_module = self._load_module('style', theme_name)

        if not color_module or not hasattr(color_module, 'palette'):
            print(f"Failed to load palette for color scheme: {color_scheme_name}. Reverting to dark.")
            color_module = self._load_module('color', 'dark')

        if not style_module or not hasattr(style_module, 'get_stylesheet'):
            print(f"Failed to load stylesheet for theme: {theme_name}. Reverting to clean.")
            style_module = self._load_module('style', 'clean')

        self.current_color_scheme = color_scheme_name
        self.current_theme = theme_name

        if color_module:
            self.current_palette = color_module.palette

        if style_module and color_module:
            stylesheet = style_module.get_stylesheet(color_module.palette)
            app.setStyleSheet(stylesheet)

        if hasattr(app, '_tooltip_enhancer'):
            app._tooltip_enhancer.update_theme_colors(self.current_palette)


        self.update_path_label_style()

    def update_path_label_style(self):
        """Updates the color of the path label based on the current theme and if a path is selected."""
        if not hasattr(self.main_window, 'path_label'):
            return

        colors = self.current_palette
        if not colors: return
        label_color = colors.get("text_dim", "#aaa") if not self.main_window.root_path else colors.get("text", "#f0f0f0")

        self.main_window.path_label.setStyleSheet(f"color: {label_color}; background-color: transparent;")