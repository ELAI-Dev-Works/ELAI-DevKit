from systems.settings.manager import SettingsManager
from systems.language.manager import LanguageManager
from systems.extension.manager import ExtensionManager
from systems.gui.themes.manager import ThemeManager
from systems.async_thread.manager import AsyncThreadManager
from systems.memory.manager import MemoryManager
from systems.fs.manager import FileSystemManager

class ExtensionContextProxy:
    """
    A proxy context for extensions. Delegates most attributes to the global AppContext,
    but provides isolated instances of MemoryManager and AsyncThreadManager to prevent
    an extension crash/hang from bringing down the core toolkit.
    """
    def __init__(self, global_context, extension_name):
        self._global_context = global_context
        self.extension_name = extension_name

        # Create isolated managers for this extension
        from systems.memory.manager import MemoryManager
        from systems.async_thread.manager import AsyncThreadManager

        self.memory = MemoryManager(global_context.app_root_path)
        # Isolated thread pool
        self.async_thread_manager = AsyncThreadManager(self)

    def __getattr__(self, name):
        # Delegate missing attributes to the global context
        return getattr(self._global_context, name)

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

        # Initialize Global File System Manager
        self.fs = FileSystemManager(self.app_root_path)
        main_window_proxy.fs = self.fs

        # Initialize Memory & Caching System
        # Initialize Memory & Caching System
        self.memory = MemoryManager(self.app_root_path)
        main_window_proxy.memory = self.memory
        self.fs.memory = self.memory

        # Initialize Core Security Systems & IPC Hub
        from systems.security.manager import SecurityManager
        self.security_manager = SecurityManager(self.app_root_path)
        main_window_proxy.security_manager = self.security_manager


        # Inject into proxy immediately so ExtensionManager can find it
        main_window_proxy.settings_manager = self.settings_manager
    
        self.lang = LanguageManager(self.app_root_path)
        main_window_proxy.lang = self.lang
    
        # ThemeManager expects a window to apply styles to path_label,
        # so we pass the proxy (LaunchWindow or MainWindow)
        self.theme_manager = ThemeManager(main_window_proxy)
        main_window_proxy.theme_manager = self.theme_manager

        # Async and Threading System
        self.async_thread_manager = AsyncThreadManager(self)
        main_window_proxy.async_thread_manager = self.async_thread_manager

    
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