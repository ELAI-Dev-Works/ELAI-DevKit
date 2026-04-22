def setup(key_manager, gui_instance):
    """
    Registers keyboard shortcuts for DevPatcher.
    """
    # Example: F5 to execute patch
    key_manager.register_shortcut("F5", gui_instance.patch_workflow_manager.execute_patch_workflow, gui_instance)