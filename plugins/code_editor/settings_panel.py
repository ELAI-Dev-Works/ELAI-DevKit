from PySide6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QWidget, QLabel, QCheckBox, QSpinBox, QHBoxLayout, QPlainTextEdit
from PySide6.QtCore import QSize, QRect, Qt
from PySide6.QtWidgets import QTextEdit
from PySide6.QtGui import QColor, QTextCursor
from systems.gui.icons import IconManager

class EditorSettingsPanel(QFrame):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.setObjectName("EditorSettingsPanel")
        self.setStyleSheet("""
            #EditorSettingsPanel {
                border-right: 1px solid rgba(128, 128, 128, 0.3);
            }
        """)

        self.closed_width = 30
        self.open_width = 220
        self.is_open = False
        self.active_panel = None   # 'settings' or 'search'

        # --- Settings button (wrench) ---
        self.settings_btn = QPushButton(self)
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.setIcon(IconManager.get_icon("core.wrench", "#858585"))
        self.settings_btn.setIconSize(QSize(18, 18))
        self.settings_btn.setStyleSheet("""
            QPushButton { border: none; background: transparent; border-radius: 4px; margin: 4px; }
            QPushButton:hover { background-color: rgba(128, 128, 128, 0.2); }
        """)
        self.settings_btn.clicked.connect(lambda: self.toggle_panel('settings'))

        # --- Search button (magnifying glass) ---
        self.search_btn = QPushButton(self)
        self.search_btn.setCursor(Qt.PointingHandCursor)
        self.search_btn.setIcon(IconManager.get_icon("core.search", "#858585"))
        self.search_btn.setIconSize(QSize(18, 18))
        self.search_btn.setStyleSheet("""
            QPushButton { border: none; background: transparent; border-radius: 4px; margin: 4px; }
            QPushButton:hover { background-color: rgba(128, 128, 128, 0.2); }
        """)
        self.search_btn.clicked.connect(lambda: self.toggle_panel('search'))

        # --- Maximize button ---
        self.maximize_btn = QPushButton(self)
        self.maximize_btn.setCursor(Qt.PointingHandCursor)
        self.maximize_btn.setIcon(IconManager.get_icon("core.maximize", "#858585"))
        self.maximize_btn.setIconSize(QSize(18, 18))
        self.maximize_btn.setStyleSheet("""
            QPushButton { border: none; background: transparent; border-radius: 4px; margin: 4px; }
            QPushButton:hover { background-color: rgba(128, 128, 128, 0.2); }
        """)
        self.maximize_btn.clicked.connect(self.editor.open_maximized)

        # --- Settings content ---
        self.settings_content = QWidget(self)
        content_layout = QVBoxLayout(self.settings_content)
        content_layout.setContentsMargins(10, 10, 10, 10)

        title_label = QLabel("Editor Settings")
        title_label.setStyleSheet("font-weight: bold;")
        content_layout.addWidget(title_label)

        wrap_checkbox = QCheckBox("Word Wrap")
        wrap_checkbox.stateChanged.connect(editor.toggle_word_wrap)
        content_layout.addWidget(wrap_checkbox)

        font_layout = QHBoxLayout()
        font_label = QLabel("Font Size:")
        font_spinbox = QSpinBox()
        font_spinbox.setRange(6, 48)
        font_spinbox.setValue(10)
        font_spinbox.valueChanged.connect(editor.change_font_size)
        font_layout.addWidget(font_label)
        font_layout.addWidget(font_spinbox)
        content_layout.addLayout(font_layout)

        content_layout.addStretch()

        # --- Search content ---
        self.search_content = QWidget(self)
        search_layout = QVBoxLayout(self.search_content)
        search_layout.setContentsMargins(10, 10, 10, 10)

        search_label = QLabel("Multi‑line search")
        search_label.setStyleSheet("font-weight: bold;")
        search_layout.addWidget(search_label)

        self.search_input = QPlainTextEdit()
        self.search_input.setPlaceholderText("Search text…")
        self.search_input.setTabChangesFocus(True)
        search_layout.addWidget(self.search_input)

        # ** Search button **
        self.search_exec_btn = QPushButton("Search")
        self.search_exec_btn.clicked.connect(self.perform_search)
        search_layout.addWidget(self.search_exec_btn)

        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("◀ Prev")
        self.prev_btn.clicked.connect(self.search_prev)
        self.next_btn = QPushButton("Next ▶")
        self.next_btn.clicked.connect(self.search_next)
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.next_btn)
        search_layout.addLayout(nav_layout)

        clear_btn = QPushButton("Clear & highlight")
        clear_btn.clicked.connect(self.clear_search)
        search_layout.addWidget(clear_btn)

        search_layout.addStretch()

        # Hide both content panels initially
        self.settings_content.setVisible(False)
        self.search_content.setVisible(False)

        self.setMinimumWidth(self.closed_width)

        # Search state
        self._search_matches = []    # list of (start_pos, end_pos) tuples
        self._current_match_idx = -1

    # ---------- Panel toggling ----------
    def toggle_panel(self, panel_name):
        if self.is_open and self.active_panel == panel_name:
            self._close_panel()
        else:
            self._open_panel(panel_name)

    def _open_panel(self, panel_name):
        self.active_panel = panel_name
        self.is_open = True
        target = self.open_width
        if hasattr(self.editor, 'animation'):
            self.editor.animation.stop()
            self.editor.animation.setStartValue(self.editor.current_panel_width)
            self.editor.animation.setEndValue(target)
            self.editor.animation.start()
        else:
            self.editor.current_panel_width = target
            self.editor.update_margins_and_geometry()

        self.settings_content.setVisible(panel_name == 'settings')
        self.search_content.setVisible(panel_name == 'search')
        if panel_name == 'search':
            self.search_input.setFocus()

    def _close_panel(self):
        self.is_open = False
        self.active_panel = None
        target = self.closed_width
        if hasattr(self.editor, 'animation'):
            self.editor.animation.stop()
            self.editor.animation.setStartValue(self.editor.current_panel_width)
            self.editor.animation.setEndValue(target)
            self.editor.animation.start()
        else:
            self.editor.current_panel_width = target
            self.editor.update_margins_and_geometry()

        self.settings_content.setVisible(False)
        self.search_content.setVisible(False)
        self._clear_highlights()

    # ---------- Geometry ----------
    def update_geometry(self, cr):
        footer_height = self.editor.footer.height() if hasattr(self.editor, 'footer') else 0
        hbar = self.editor.horizontalScrollBar()
        hbar_h = hbar.height() if hbar.isVisible() else 0
        panel_height = cr.height() - footer_height - hbar_h

        self.setGeometry(QRect(cr.left(), cr.top(), self.editor.current_panel_width, cr.height()))

        btn_y = 0
        self.settings_btn.setGeometry(QRect(0, btn_y, self.closed_width, 30))
        btn_y += 30
        self.search_btn.setGeometry(QRect(0, btn_y, self.closed_width, 30))
        btn_y += 30

        self.maximize_btn.setGeometry(QRect(0, panel_height - 30, self.closed_width, 30))

        content_width = self.open_width - self.closed_width
        self.settings_content.setGeometry(QRect(self.closed_width, 0, content_width, cr.height()))
        self.search_content.setGeometry(QRect(self.closed_width, 0, content_width, cr.height()))

    # ---------- Search logic ----------
    def perform_search(self):
        query = self.search_input.toPlainText()
        if not query.strip():
            self._clear_highlights()
            return
        self._update_search_highlighting(query)

    def _update_search_highlighting(self, query):
        self._clear_highlights()
        doc = self.editor.document()
        content = doc.toPlainText()
        self._search_matches.clear()

        if not query.strip():
            return

        # Use string find to locate all occurrences, supporting multi-line
        start_pos = 0
        query_len = len(query)
        while True:
            pos = content.find(query, start_pos)
            if pos == -1:
                break
            self._search_matches.append((pos, pos + query_len))
            start_pos = pos + query_len  # continue after the match to find next

        # Apply extra selections
        extra_selections = []
        for start, end in self._search_matches:
            match_cursor = QTextCursor(doc)
            match_cursor.setPosition(start)
            match_cursor.setPosition(end, QTextCursor.KeepAnchor)
            sel = QTextEdit.ExtraSelection()
            sel.format.setBackground(Qt.yellow)
            sel.format.setForeground(Qt.black)
            sel.cursor = match_cursor
            extra_selections.append(sel)

        # ** Merge with the editor's current extra selections (e.g. line highlight) **
        original_extras = self.editor.extraSelections()
        original_extras = [e for e in original_extras if e.format.background().color() != QColor(Qt.yellow)]  # remove previous search highlights
        original_extras.extend(extra_selections)
        self.editor.setExtraSelections(original_extras)

        self._current_match_idx = 0 if self._search_matches else -1
        if self._current_match_idx != -1:
            self._jump_to_match(0)

    def _jump_to_match(self, idx):
        if not self._search_matches:
            return
        start, end = self._search_matches[idx]
        doc = self.editor.document()
        cursor = QTextCursor(doc)
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        self.editor.setTextCursor(cursor)
        self.editor.ensureCursorVisible()

    def _clear_highlights(self):
        self._search_matches.clear()
        self._current_match_idx = -1
        # Restore the editor's own extra selections (line highlight etc.)
        if hasattr(self.editor, 'update_extra_selections'):
            self.editor.update_extra_selections()
        else:
            self.editor.setExtraSelections([])

    def search_next(self):
        if not self._search_matches:
            return
        self._current_match_idx = (self._current_match_idx + 1) % len(self._search_matches)
        self._jump_to_match(self._current_match_idx)

    def search_prev(self):
        if not self._search_matches:
            return
        self._current_match_idx = (self._current_match_idx - 1) % len(self._search_matches)
        self._jump_to_match(self._current_match_idx)

    def clear_search(self):
        self.search_input.clear()
        self._clear_highlights()