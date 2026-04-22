from ..interface import DevPatcherInterface

class DevPatcherCoreWindow(DevPatcherInterface):
    """
    Core integration for DevPatcher (V2 Architecture).
    """
    def __init__(self, context):
        app_instance = context.extension_manager.extensions['dev_patcher']['instance']
        super().__init__(context, app_instance)