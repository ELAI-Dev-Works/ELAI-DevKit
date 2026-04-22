import tomllib
from PySide6.QtWidgets import QWidget, QFormLayout, QPlainTextEdit, QLabel

default_settings = """
supported_extensions = ".py .in .js .ts .jsx .tsx .html .css .scss .sass .json .yaml .yml .toml .ini .cfg .conf .md .txt .svg .sql .sh .bat .ps1 .dockerfile .gitignore .csv .log .xml .c .cpp .h .hpp .java .kt .swift .go .rs .rb .php .pl .r .scala .dart .lua .m .mm .vue .svelte .as .gd .tscn .tres .res .godot .import .scn .gde .gdc .gdshader .gdns .gdext .mod .cl .rpy .asm .inc .exdoc .cdoc .devpatch"
"""

class ProjectTextPackerSettingsWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.app = main_window.extension_manager.extensions['project_text_packer']['instance']
        self.lang = main_window.lang
        self.state_on_open = {}
        self.defaults = tomllib.loads(default_settings)

        layout = QFormLayout(self)
        self.extensions_input = QPlainTextEdit()
        self.extensions_input.setFixedHeight(80)
        self.extensions_label = QLabel()
        layout.addRow(self.extensions_label, self.extensions_input)

        self.retranslate_ui()

    def retranslate_ui(self):
        self.extensions_label.setText(self.lang.get('packer_extensions_label'))
        self.extensions_input.setProperty("no_custom_tooltip", True)
        self.extensions_input.setToolTip(self.lang.get('packer_extensions_tooltip'))

    def store_initial_state(self):
        settings = self.main_window.settings_manager.get_setting(
            ['apps', 'project_text_packer', 'settings'], self.defaults
        )
        self.state_on_open = settings
        extensions_str = settings.get('supported_extensions', '')
        self.extensions_input.setPlainText(extensions_str)

    def apply_settings(self):
        self.state_on_open = self.get_settings_to_save()

    def get_settings_to_save(self):
        return {
            'supported_extensions': self.extensions_input.toPlainText()
        }

    def revert_settings(self):
        extensions_str = self.state_on_open.get('supported_extensions', '')
        self.extensions_input.setPlainText(extensions_str)

    def reset_to_defaults(self):
        default_ext = self.defaults.get('supported_extensions', '')
        self.extensions_input.setPlainText(default_ext)