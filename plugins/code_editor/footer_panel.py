from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel

class EditorFooter(QFrame):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.setFixedHeight(16)
        self.setObjectName("EditorFooter")

        self.setStyleSheet("""
            #EditorFooter {
                background-color: #0ea5e9;
                color: white;
            }
            QLabel {
                color: white;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11px;
                padding: 0 10px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.lang_label = QLabel("Plain Text")
        self.pos_label = QLabel("Ln 1, Col 1")
        self.chars_label = QLabel("0 chars")

        layout.addWidget(self.chars_label)
        layout.addWidget(self.pos_label)
        layout.addStretch()
        layout.addWidget(self.lang_label)

    def update_stats(self):
        text = self.editor.toPlainText()
        chars = len(text)
        self.chars_label.setText(f"{chars} chars")

        lang = "Plain Text"
        if "<@|" in text or "---end---" in text:
            lang = "DPCL (DevPatch Command Language)"
        elif "import " in text or "def " in text or "class " in text and ":" in text:
            lang = "Python"
        elif "function" in text or "=>" in text or "const " in text or "let " in text:
            lang = "JavaScript / TypeScript"
        elif "<html>" in text or "</div>" in text:
            lang = "HTML"
        elif text.strip().startswith("{") and ":" in text:
            lang = "JSON"

        self.lang_label.setText(lang)

    def update_cursor(self):
        cursor = self.editor.textCursor()
        ln = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        self.pos_label.setText(f"Ln {ln}, Col {col}")

    def update_theme_colors(self, palette):
        bg = palette.get("background_light", "#1e1e1e")
        text = palette.get("text_dim", "#888888")
        border = palette.get("border", "#333333")
        self.setStyleSheet(f"""
            #EditorFooter {{
                background-color: {bg};
                color: {text};
                border-top: 1px solid {border};
                border-left: 1px solid {border};
            }}
            QLabel {{
                color: {text};
                font-family: 'Segoe UI', sans-serif;
                font-size: 11px;
                padding: 0 10px;
            }}
        """)