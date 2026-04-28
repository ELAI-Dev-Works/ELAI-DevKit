import tomllib

# This variable was moved from gui/main_settings.py to break a circular import
# between main_settings.py and extension_manager_widget.py.
main_default_settings_str = """
[core]
language = "en"

[core.theme]
color_scheme = "dark"
theme = "sleek"

[core.ui]
always_show_tooltips = false
font_size = 10

[core.extensions]
dev_patcher_enabled = true
project_text_packer_enabled = true
project_launcher_enabled = true
project_builder_enabled = true
"""

main_default_settings = tomllib.loads(main_default_settings_str)