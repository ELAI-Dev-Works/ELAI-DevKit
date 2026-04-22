from systems.settings.manager import SettingsManager
from systems.language.manager import LanguageManager
from systems.extension.manager import ExtensionManager
from systems.gui.themes.manager import ThemeManager

class AppContext:
    """
    Holds the shared state and managers of the application.
    Allows passing initialized managers between the LaunchWindow and MainWindow.
    """
    def __init__(self, app_root_path, main_window_proxy):
        self.app_root_path = app_root_path
        self.main_window = None # Placeholder for the actual MainWindow instance
    
        # Initialize Managers
        self.settings_manager = SettingsManager(self.app_root_path)
        # Inject into proxy immediately so ExtensionManager can find it
        main_window_proxy.settings_manager = self.settings_manager
    
        self.lang = LanguageManager(self.app_root_path)
        main_window_proxy.lang = self.lang
    
        # ThemeManager expects a window to apply styles to path_label,
        # so we pass the proxy (LaunchWindow or MainWindow)
        self.theme_manager = ThemeManager(main_window_proxy)
        main_window_proxy.theme_manager = self.theme_manager
    
        # Load language setting
        core_settings = self.settings_manager.get_setting(['core'], {})
        self.lang.set_language(core_settings.get('language', 'en'))
    
        # Extension System
        self.extension_manager = ExtensionManager(main_window_proxy)
        main_window_proxy.extension_manager = self.extension_manager
        # Inject context into proxy immediately so V2 extensions can access it during init
        main_window_proxy.context = self
    
        self.extension_manager.discover_extensions()
        self.extension_manager.load_extensions()
        self.extension_manager.initialize_extensions()
        self.lang.load_extension_languages(self.extension_manager)