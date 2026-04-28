from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, 
    QListWidgetItem, QComboBox, QLabel, QMessageBox
)
from PySide6.QtCore import Qt

class RestoreBackupDialog(QDialog):
    def __init__(self, main_window, backups, initial_mode):
        super().__init__(main_window)
        self.lang = main_window.lang
        self.backups = backups
        self.selected_backup = None
        self.selected_mode = initial_mode
        
        self.setWindowTitle(self.lang.get('restore_modal_title', 'Restore from Backup'))
        self.resize(600, 400)
        self._init_ui()

        from systems.gui.utils.windows import center_window
        center_window(self, main_window)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        self.list_widget = QListWidget()
        for b in self.backups:
            item = QListWidgetItem(b['display'])
            item.setData(Qt.ItemDataRole.UserRole, b)
            self.list_widget.addItem(item)
        
        if not self.backups:
            self.list_widget.addItem(self.lang.get('restore_no_backups', 'No backups available.'))
            self.list_widget.setEnabled(False)
            
        layout.addWidget(self.list_widget)
        
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel(self.lang.get('restore_mode_label', 'Restore Mode:')))
        self.mode_combo = QComboBox()
        self.mode_combo.addItem(self.lang.get('restore_mode_changes'), "changes")
        self.mode_combo.addItem(self.lang.get('restore_mode_full'), "full")
        
        idx = self.mode_combo.findData(self.selected_mode)
        if idx >= 0: self.mode_combo.setCurrentIndex(idx)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)
        
        btn_layout = QHBoxLayout()
        self.restore_btn = QPushButton(self.lang.get('restore_btn'))
        self.restore_btn.clicked.connect(self._on_restore)
        self.restore_btn.setEnabled(bool(self.backups))
        
        self.cancel_btn = QPushButton(self.lang.get('cancel_btn_text', 'Cancel'))
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.restore_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
    def _on_restore(self):
        item = self.list_widget.currentItem()
        if not item: return
        
        reply = QMessageBox.question(
            self, self.lang.get('restore_modal_title', 'Restore from Backup'), 
            self.lang.get('restore_confirm_msg', 'Are you sure you want to restore?'), 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.selected_backup = item.data(Qt.ItemDataRole.UserRole)
            self.selected_mode = self.mode_combo.currentData()
            self.accept()
            
    def get_selected(self):
        return self.selected_backup, self.selected_mode