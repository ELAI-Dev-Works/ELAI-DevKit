def get_stylesheet(colors: dict) -> str:
    """Returns the QSS for the classic theme using the provided color palette."""
    return f"""
    QWidget {{
        background-color: {colors["background"]};
        color: {colors["text"]};
    }}
    QTabWidget::pane {{
        border-top: 1px solid {colors["border"]};
    }}
    QTabBar::tab {{
        background: {colors["tab_unselected_bg"]};
        border: 1px solid {colors["border"]};
        border-bottom: none;
        padding: 6px;
        min-width: 80px;
    }}
    QTabBar::tab:selected {{
        background: {colors["tab_selected_bg"]};
        border: 1px solid {colors["border"]};
        border-bottom: 1px solid {colors["tab_selected_border"]};
    }}
    QTabBar::tab:!selected {{
        margin-top: 2px;
    }}
    QTabBar::tab:!selected:hover {{
        background: {colors["tab_unselected_hover"]};
    }}
    #settingsOverlay {{
        background-color: {colors["overlay"]};
    }}
    #settingsContentBox {{
        background-color: {colors["background_light"]};
        border: 1px solid {colors["border"]};
        border-radius: 8px;
    }}
    QMainWindow {{
        background-color: {colors["background"]};
    }}
    QTextEdit, QPlainTextEdit {{
        background-color: {colors["background_light"]};
        color: {colors["text"]};
        border: 1px solid {colors["border"]};
        selection-background-color: {colors["selection"]};
    }}
    QPushButton {{
        background-color: {colors["button"]};
        border: 1px solid {colors["border"]};
        padding: 5px;
        min-height: 15px;
    }}
    QPushButton:hover {{
        background-color: {colors["button_hover"]};
    }}
    QPushButton:pressed {{
        background-color: {colors["button_pressed"]};
    }}
    QLabel {{
        color: {colors["text"]};
    }}
    QGroupBox {{
        border: 1px solid {colors["border"]};
        margin-top: 1em;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px 0 5px;
    }}
    QCheckBox {{
        color: {colors["text"]};
    }}
    QLineEdit, QComboBox {{
        background-color: {colors["background_light"]};
        border: 1px solid {colors["border"]};
        padding: 2px;
    }}
    QFrame {{
        border: none;
    }}
    QMessageBox, QDialog {{
        background-color: {colors["background"]};
    }}
    """