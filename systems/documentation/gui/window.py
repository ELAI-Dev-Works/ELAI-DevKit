from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QTextBrowser, QSplitter, QLabel, QPushButton, QApplication, QFrame, QToolTip,
    QLineEdit, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, QSize, QUrl
from PySide6.QtGui import QCursor

from systems.documentation.manager import DocManager
from systems.gui.icons import IconManager
from systems.gui.utils.markdown_styler import MarkdownStyler


class DocumentationWindow(QMainWindow):
    def __init__(self, context, parent=None, on_home=None):
        super().__init__(parent)
        self.context = context
        self.lang = context.lang
        self.doc_manager = DocManager(context.app_root_path)
        self.on_home_callback = on_home
        
        # Helper for markdown rendering
        self.styler = MarkdownStyler(context.theme_manager, context.lang)
        
        self.resize(1100, 750)
        self._init_ui()
        self._load_docs()
        self.retranslate_ui()
        self._apply_theme_styles()

    def retranslate_ui(self):
        self.setWindowTitle(self.lang.get('launcher_btn_docs'))
        self.tree.setHeaderLabel(self.lang.get('docs_nav_title'))

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
    
        # --- Top Bar ---
        top_bar = QFrame()
        top_bar.setFixedHeight(50)
        top_bar.setObjectName("DocTopBar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(15, 0, 15, 0)
    
        if self.on_home_callback:
            back_btn = QPushButton(self.lang.get('btn_back_to_launcher'))
            # Dynamic icon color
            p = self.context.theme_manager.current_palette
            icon_color = p.get("icon_default", "#eee")
            back_btn.setIcon(IconManager.get_icon("core.home", icon_color))
            back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            back_btn.clicked.connect(self.go_home)
            back_btn.setStyleSheet("""
                QPushButton { border: none; font-weight: bold; text-align: left; padding: 5px; }
                QPushButton:hover { background-color: rgba(128,128,128, 0.2); border-radius: 4px; }
            """)
            top_layout.addWidget(back_btn)
    
        top_layout.addStretch()
    
        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Find in page...")
        self.search_input.setFixedWidth(200)
        self.search_input.returnPressed.connect(self._find_next)
        top_layout.addWidget(self.search_input)
    
        self.find_next_btn = QPushButton("↓")
        self.find_next_btn.setProperty("no_custom_tooltip", True)
        self.find_next_btn.setToolTip(self.lang.get('docs_find_next_tooltip'))
        self.find_next_btn.setFixedWidth(30)
        self.find_next_btn.clicked.connect(self._find_next)
        top_layout.addWidget(self.find_next_btn)

        self.find_prev_btn = QPushButton("↑")
        self.find_prev_btn.setProperty("no_custom_tooltip", True)
        self.find_prev_btn.setToolTip(self.lang.get('docs_find_prev_tooltip'))
        self.find_prev_btn.setFixedWidth(30)
        self.find_prev_btn.clicked.connect(self._find_prev)
        top_layout.addWidget(self.find_prev_btn)
    
        layout.addWidget(top_bar)
    
        # --- Main Content Splitter ---
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setChildrenCollapsible(False)
    
        # 1. Navigation Tree
        self.tree = QTreeWidget()
        self.tree.setObjectName("DocNavTree")
        self.tree.setIndentation(20)
        self.tree.setAnimated(True)
        self.tree.itemClicked.connect(self._on_item_clicked)
        splitter.addWidget(self.tree)
    
        # Content Splitter (Content | TOC)
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
    
        # 2. Content Area
        content_widget = QWidget()
        content_widget.setObjectName("DocContentArea")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 20, 30, 20)
    
        self.content_title = QLabel("")
        self.content_title.setWordWrap(True)
        self.content_title.setStyleSheet("font-size: 24pt; font-weight: 600; margin-bottom: 20px;")
        content_layout.addWidget(self.content_title)
    
        self.browser = QTextBrowser()
        self.browser.setOpenLinks(False)
        self.browser.anchorClicked.connect(self._on_anchor_clicked)
        self.browser.setFrameShape(QFrame.Shape.NoFrame)
        content_layout.addWidget(self.browser)
    
        content_splitter.addWidget(content_widget)
    
        # 3. Table of Contents (Right)
        self.toc_list = QListWidget()
        self.toc_list.setObjectName("DocTOC")
        self.toc_list.setFixedWidth(200)
        self.toc_list.itemClicked.connect(self._on_toc_clicked)
        content_splitter.addWidget(self.toc_list)
    
        # Hide TOC by default until loaded
        self.toc_list.hide()
    
        # Add content splitter to main splitter
        splitter.addWidget(content_splitter)
    
        # Ratios
        splitter.setStretchFactor(0, 1) # Nav Tree
        splitter.setStretchFactor(1, 4) # Content + TOC
        content_splitter.setStretchFactor(0, 4) # Content
        content_splitter.setStretchFactor(1, 1) # TOC
    
        layout.addWidget(splitter)

    def _apply_theme_styles(self):
        """Applies advanced CSS for the window components."""
        # Load palette dynamically
        try:
            import importlib
            mod = importlib.import_module(f"gui.themes.color.{self.context.theme_manager.current_color}")
            c = mod.palette
        except:
            # Fallback defaults
            c = {"background": "#2b2b2b", "background_light": "#3c3c3c", "text": "#f0f0f0", "border": "#555", "selection": "#29b8db"}

        color_scheme = self.context.theme_manager.current_color_scheme
        is_dark = color_scheme in ('dark', 'ocean')
        tree_bg = c['background_light'] if is_dark else "#e9e9e9"
        
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {c['background']}; }}
            #DocTopBar {{
                background-color: {c['background']};
                border-bottom: 1px solid {c['border']};
            }}
            #DocNavTree {{
                background-color: {tree_bg};
                border: none;
                font-size: 11pt;
                color: {c['text']};
                padding-top: 10px;
                outline: 0;
            }}
            QHeaderView::section {{
                background-color: {c['background']};
                color: {c['text']};
                border: none;
                border-bottom: 1px solid {c['border']};
                padding: 8px;
                font-weight: bold;
            }}
            #DocNavTree::item {{
                padding: 6px;
                border-radius: 4px;
                margin-left: 5px;
                margin-right: 5px;
            }}
            #DocNavTree::item:hover {{
                background-color: rgba(128, 128, 128, 0.1);
            }}
            #DocNavTree::item:selected {{
                background-color: {c['selection']};
                color: white;
            }}
            QSplitter::handle {{
                background-color: {c['border']};
            }}
            #DocContentArea {{
                background-color: {c['background']};
            }}
                QLabel {{ color: {c['text']}; }}
                QTextBrowser {{ background-color: {c['background']}; border: none; }}
                #DocTOC {{
                    background-color: {tree_bg};
                    border: none;
                    border-left: 1px solid {c['border']};
                    font-size: 10pt;
                    color: {c['text_dim'] if 'text_dim' in c else c['text']};
                    padding-top: 10px;
                    outline: 0;
                }}
                #DocTOC::item:hover {{
                    background-color: rgba(128, 128, 128, 0.1);
                    color: {c['text']};
                }}
                #DocTOC::item:selected {{
                    background-color: transparent;
                    color: {c['selection']};
                }}
                QLineEdit {{
                    background-color: {c['background_light']};
                    color: {c['text']};
                    border: 1px solid {c['border']};
                    border-radius: 4px;
                    padding: 4px;
                }}
                QScrollBar:vertical {{
                    background: {c['background']};
                    width: 12px;
                    margin: 0px;
                }}
                QScrollBar::handle:vertical {{
                    background: {c['border']};
                    min-height: 20px;
                    border-radius: 5px;
                    margin: 2px;
                }}
                QScrollBar::handle:vertical:hover {{
                    background: {c.get('selection', '#29b8db')};
                }}
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                    height: 0px;
                }}
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                    background: none;
                }}
                QScrollBar:horizontal {{
                    background: {c['background']};
                    height: 12px;
                    margin: 0px;
                }}
                QScrollBar::handle:horizontal {{
                    background: {c['border']};
                    min-width: 20px;
                    border-radius: 5px;
                    margin: 2px;
                }}
                QScrollBar::handle:horizontal:hover {{
                    background: {c.get('selection', '#29b8db')};
                }}
                QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                    width: 0px;
                }}
                QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                    background: none;
                }}
            """)

    def _load_docs(self):
        project_path = None
        # The context might have a reference to the main_window instance.
        # This instance has the currently selected root_path.
        if self.context.main_window and self.context.main_window.root_path:
            project_path = self.context.main_window.root_path
        else:
            # Fallback for when docs are opened from launcher:
            # Check for custom_commands in the app's own directory.
            project_path = self.context.app_root_path

        docs = self.doc_manager.scan_docs(project_path)
        self.tree.clear()

        # Custom Font for tree header
        header_font = self.tree.font()
        header_font.setBold(True)
        self.tree.headerItem().setFont(0, header_font)

        # Sort categories to ensure consistent tree order
        for category in sorted(docs.keys()):
            pages = docs[category]
            
            # Split category path: "Core Apps/Dev Patcher/Sub Category"
            cat_parts = category.split('/')
            
            # Start from the invisible root
            current_parent = self.tree.invisibleRootItem()
            
            # Iterate through path segments to build/find tree nodes
            for part in cat_parts:
                found_item = self._find_item(current_parent, part)
                if not found_item:
                    found_item = QTreeWidgetItem([part])
                    # Add to tree (either as top level or child)
                    if current_parent == self.tree.invisibleRootItem():
                        self.tree.addTopLevelItem(found_item)
                    else:
                        current_parent.addChild(found_item)
                    
                    found_item.setExpanded(True)
                
                current_parent = found_item

            # Add pages to the final category node
            for title in sorted(pages.keys()):
                path = pages[title]
                page_item = QTreeWidgetItem([title])
                page_item.setData(0, Qt.ItemDataRole.UserRole, path)
                # Use a specific icon for files if needed, or default
                current_parent.addChild(page_item)

    def _find_item(self, parent, text):
        for i in range(parent.childCount()):
            child = parent.child(i)
            if child.text(0) == text:
                return child
        return None

    def _on_item_clicked(self, item, column):
        file_path = item.data(0, Qt.ItemDataRole.UserRole)
        if file_path:
            self._display_file(item.text(0), file_path)
        else:
            # If a folder is clicked, expand/collapse
            item.setExpanded(not item.isExpanded())

    def _display_file(self, title, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
    
            self.content_title.setText(title)
    
            # Use the styler to convert Markdown -> HTML with Code Blocks and TOC data
            html_content, css, toc_data = self.styler.render(content)
    
            self.browser.document().setDefaultStyleSheet(css)
            self.browser.setHtml(html_content)
    
            # Update TOC
            self._update_toc(toc_data)
    
        except Exception as e:
            self.browser.setPlainText(f"Error loading file: {e}")
    
    def _update_toc(self, toc_data):
        self.toc_list.clear()
        if not toc_data:
            self.toc_list.hide()
            return
    
        self.toc_list.show()
        for level, title, anchor in toc_data:
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, anchor)
            # Simple visual indentation using spaces
            if level > 1:
                item.setText("  " * (level-1) + title)
            self.toc_list.addItem(item)
    
    def _on_toc_clicked(self, item):
        anchor = item.data(Qt.ItemDataRole.UserRole)
        if anchor:
            self.browser.scrollToAnchor(anchor)
    
    def _find_next(self):
        text = self.search_input.text()
        if not text: return
        self.browser.find(text)
    
    def _find_prev(self):
        text = self.search_input.text()
        if not text: return
        self.browser.find(text, QTextBrowser.FindFlag.FindBackward)

    def _on_anchor_clicked(self, url):
        """Handle clicks on links in the text browser."""
        url_str = url.toString()

        # 1. Handle Internal Anchors (#header-id)
        if not url.scheme() and url.fragment():
            self.browser.scrollToAnchor(url.fragment())
            return

        # 2. Handle Copy Action
        if url_str.startswith("action:copy_"):
            block_id = url_str.split("_")[1]
            code = self.styler.get_code_content(block_id)
            if code:
                # Remove trailing newline for copy convenience
                QApplication.clipboard().setText(code.strip())
                QToolTip.showText(QCursor.pos(), self.lang.get('doc_copied_tooltip'), self.browser)
            return

        # 3. Handle normal external links
        if url.scheme() in ('http', 'https'):
            from PySide6.QtGui import QDesktopServices
            QDesktopServices.openUrl(url)

    def go_home(self):
        self.close()
        if self.on_home_callback:
            self.on_home_callback()