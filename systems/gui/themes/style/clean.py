def get_stylesheet(colors: dict) -> str:
    """Returns the QSS for a modern, flatter theme using the provided color palette."""
    return f"""
    QWidget {{
        background-color: {colors["background"]};
        color: {colors["text"]};
        font-size: 10pt;
        font-family: Segoe UI;
    }}
    QTabWidget::pane {{
        border: none;
        border-top: 2px solid {colors["button"]};
    }}
    QTabBar::tab {{
        background: transparent;
        border: none;
        border-bottom: 2px solid transparent;
        padding: 8px 12px;
        min-width: 80px;
    }}
    QTabBar::tab:selected {{
        background: {colors["background_light"]};
        border-bottom: 2px solid {colors["selection"]};
    }}
    QTabBar::tab:!selected:hover {{
        background: {colors["button_hover"]};
    }}
    #settingsOverlay {{
        background-color: {colors["overlay"]};
    }}
    #settingsContentBox {{
        background-color: {colors["background"]};
        border: 1px solid {colors["border"]};
        border-radius: 6px;
    }}
    QMainWindow, QDialog {{
        background-color: {colors["background"]};
    }}
    QTextEdit, QPlainTextEdit, QLineEdit, QComboBox {{
        background-color: {colors["background_light"]};
        color: {colors["text"]};
        border: 1px solid {colors["border"]};
        selection-background-color: {colors["selection"]};
        border-radius: 4px;
        padding: 4px;
    }}
    QPushButton {{
        background-color: {colors["button"]};
        border: 1px solid {colors["border"]};
        padding: 6px 10px;
        min-height: 18px;
        border-radius: 4px;
    }}
    QPushButton:hover {{
        background-color: {colors["button_hover"]};
        border: 1px solid {colors["selection"]};
    }}
    QPushButton:pressed {{
        background-color: {colors["button_pressed"]};
    }}
    QLabel {{
        color: {colors["text"]};
        background-color: transparent;
    }}
    QGroupBox {{
        border: 1px solid {colors["border"]};
        margin-top: 1em;
        border-radius: 4px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px 0 5px;
    }}
    QCheckBox {{
        color: {colors["text"]};
        background-color: transparent;
    }}
    QFrame {{
        border: none;
    }}
    QMessageBox {{
        background-color: {colors["background_light"]};
    }}
    """