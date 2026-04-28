def get_stylesheet(colors: dict) -> str:
    """Returns the QSS for a sleek, modern theme with rounded corners."""
    return f"""
    QWidget {{
        background-color: {colors["background"]};
        color: {colors["text"]};
        font-family: 'Segoe UI', 'San Francisco', sans-serif;
    }}
    QTabWidget::pane {{
        border: 1px solid {colors["border"]};
        border-radius: 8px;
        top: -1px;
    }}
    QTabBar::tab {{
        background: transparent;
        border: none;
        padding: 8px 16px;
        margin-right: 4px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        font-weight: 500;
    }}
    QTabBar::tab:selected {{
        background: {colors["background_light"]};
        color: {colors["selection"]};
        border-bottom: 2px solid {colors["selection"]};
    }}
    QTabBar::tab:!selected:hover {{
        background: {colors["tab_unselected_hover"]};
    }}
    #settingsOverlay {{
        background-color: {colors["overlay"]};
    }}
    #settingsContentBox {{
        background-color: {colors["background"]};
        border: 1px solid {colors["border"]};
        border-radius: 12px;
    }}
    QMainWindow, QDialog {{
        background-color: {colors["background"]};
    }}
    QTextEdit, QPlainTextEdit, QLineEdit, QComboBox {{
        background-color: {colors["background_light"]};
        color: {colors["text"]};
        border: 1px solid {colors["border"]};
        selection-background-color: {colors["selection"]};
        border-radius: 6px;
        padding: 6px;
    }}
    QTextEdit:focus, QLineEdit:focus {{
        border: 1px solid {colors["selection"]};
    }}
    QPushButton {{
        background-color: {colors["button"]};
        border: 1px solid {colors["border"]};
        padding: 6px 12px;
        border-radius: 6px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: {colors["button_hover"]};
        color: white;
        border: 1px solid {colors["button_hover"]};
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
        border-radius: 8px;
        margin-top: 1.2em;
        padding-top: 10px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
        color: {colors["text"]};
        font-weight: bold;
    }}
    QCheckBox {{
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 4px;
        border: 1px solid {colors["border"]};
        background: {colors["background_light"]};
    }}
    QCheckBox::indicator:checked {{
        background: {colors["selection"]};
        border: 1px solid {colors["selection"]};
    }}
    QScrollBar:vertical {{
        background: {colors["background"]};
        width: 10px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {colors["border"]};
        min-height: 20px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {colors["button_hover"]};
    }}
    QMessageBox {{
        background-color: {colors["background"]};
    }}
    """