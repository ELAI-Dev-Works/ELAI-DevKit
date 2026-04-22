from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTreeWidget, QTreeWidgetItem, 
    QPushButton, QHBoxLayout, QMessageBox, QLabel
)
from PySide6.QtCore import Qt
import os

class ExamplesDialog(QDialog):
    def __init__(self, parent=None, examples_path=None):
        super().__init__(parent)
        self.lang = parent.lang if hasattr(parent, 'lang') else None
        
        title = self.lang.get('examples_dialog_title') if self.lang else "Patch Examples"
        self.setWindowTitle(title)
        
        self.examples_path = examples_path
        self.selected_content = None
        self.resize(600, 450)
        
        layout = QVBoxLayout(self)
        
        info_label = QLabel(self.lang.get('examples_dialog_info') if self.lang else "Select an example to load:")
        layout.addWidget(info_label)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        layout.addWidget(self.tree)
        
        self._populate_tree()
        
        btn_layout = QHBoxLayout()
        load_text = self.lang.get('load_btn_text') if self.lang else "Load"
        self.load_btn = QPushButton(load_text)
        self.load_btn.clicked.connect(self._on_load)
        self.load_btn.setEnabled(False)
        
        cancel_text = self.lang.get('cancel_btn_text') if self.lang else "Cancel"
        self.cancel_btn = QPushButton(cancel_text)
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.load_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
        self.tree.currentItemChanged.connect(self._on_selection_change)
        self.tree.itemDoubleClicked.connect(self._on_double_click)

    def _populate_tree(self):
        if not self.examples_path or not os.path.exists(self.examples_path):
            return

        # List directories (Categories)
        for item in sorted(os.listdir(self.examples_path)):
            item_path = os.path.join(self.examples_path, item)
            if os.path.isdir(item_path):
                category_item = QTreeWidgetItem([item.replace('_', ' ').title()])
                category_item.setFlags(category_item.flags() & ~Qt.ItemIsSelectable) # Make folder non-selectable for loading
                self.tree.addTopLevelItem(category_item)
                category_item.setExpanded(True)
                
                # Scan files in folder
                files_found = False
                for f in sorted(os.listdir(item_path)):
                    if f.endswith('.devpatch'):
                        files_found = True
                        file_item = QTreeWidgetItem([f])
                        file_item.setData(0, Qt.UserRole, os.path.join(item_path, f))
                        category_item.addChild(file_item)
                
                # If no patches in folder, maybe hide it or show empty
                if not files_found:
                    category_item.setHidden(True)

            elif item.endswith('.devpatch'):
                 # Root level patches
                 file_item = QTreeWidgetItem([item])
                 file_item.setData(0, Qt.UserRole, item_path)
                 self.tree.addTopLevelItem(file_item)

    def _on_selection_change(self, current, previous):
        if current and current.data(0, Qt.UserRole):
            self.load_btn.setEnabled(True)
        else:
            self.load_btn.setEnabled(False)

    def _on_double_click(self, item, column):
        if item.data(0, Qt.UserRole):
            self._on_load()

    def _on_load(self):
        item = self.tree.currentItem()
        if not item: return
        path = item.data(0, Qt.UserRole)
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.selected_content = f.read()
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load example: {e}")

    def get_content(self):
        return self.selected_content