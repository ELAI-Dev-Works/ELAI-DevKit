from PySide6.QtCore import QObject, QEvent, Qt, QPoint, QTimer
from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QFrame, QApplication,
                               QPushButton, QCheckBox, QLineEdit, QAbstractButton,
                               QSpinBox, QDoubleSpinBox)
from PySide6.QtGui import QCursor
from systems.gui.icons import svg_to_icon, get_svg_content, ICON_TOOLTIP

def _addGUITooltip_method(self, tooltip_text):
    """
    Add a tooltip to this widget with an integrated icon.
    Returns self to allow chaining.
    """
    if self is None: return None

    self.setToolTip(tooltip_text)

    if self.property("no_custom_tooltip"):
        return self

    # Apply padding based on widget type to prevent content overlap
    style_needs_update = False
    new_style = self.styleSheet()

    if isinstance(self, QPushButton) and self.text():
        if "padding-right:" not in new_style:
            new_style += " padding-right: 24px;"
            style_needs_update = True
    elif isinstance(self, QCheckBox):
        if "padding-right:" not in new_style:
            new_style += " padding-right: 22px;"
            style_needs_update = True
    elif isinstance(self, (QLineEdit, QSpinBox, QDoubleSpinBox)):
        if "padding-right:" not in new_style:
            new_style += " padding-right: 22px;"
            style_needs_update = True
    
    if style_needs_update:
        self.setStyleSheet(new_style)

    app = QApplication.instance()
    if hasattr(app, '_tooltip_enhancer'):
        app._tooltip_enhancer._create_icon_for_widget(self)
    
    return self

class CustomTooltipWindow(QFrame):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("CustomTooltipWindow")
        self._update_style()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        self._label = QLabel()
        self._label.setWordWrap(True)
        layout.addWidget(self._label)

        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide)

    def show_text(self, text, pos):
        self._label.setText(text)
        self.adjustSize()
        # Determine the screen where the position is located
        screen = QApplication.screenAt(pos)
        if not screen:
            screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        
        if pos.x() + self.width() > screen_geometry.right():
            pos.setX(screen_geometry.right() - self.width() - 10)
        if pos.y() + self.height() > screen_geometry.bottom():
            pos.setY(screen_geometry.bottom() - self.height() - 10)
        self.move(pos)
        self.show()
        self.hide_timer.start(5000)

    def _update_style(self, bg_color="#2b2b2b", text_color="#f0f0f0", border_color="#0ea5e9"):
        self.setStyleSheet(f"""
            #CustomTooltipWindow {{
                background-color: {bg_color}; color: {text_color};
                border: 1px solid {border_color}; border-radius: 6px;
            }}
            QLabel {{ color: {text_color}; padding: 4px; font-size: 10pt; background: transparent; border: none; }}
        """)


    def mousePressEvent(self, event): self.hide()
    def enterEvent(self, event): self.hide_timer.stop()
    def leaveEvent(self, event): self.hide_timer.start(1000)

class TooltipIcon(QLabel):
    def __init__(self, parent=None, color="#d2dce1"):
        super().__init__(parent)
        self.setFixedSize(20, 20)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.target_widget = None
        self.popup = CustomTooltipWindow()
        self.raise_()
        try:
            pixmap = svg_to_icon(get_svg_content(ICON_TOOLTIP), color).pixmap(16, 16)
            self.setPixmap(pixmap)
        except:
            self.setText("?")
            self.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 10pt;")

    def mousePressEvent(self, event):
        if self.target_widget and self.target_widget.toolTip():
            QTimer.singleShot(50, lambda: self._show_popup())

    def _show_popup(self):
        if self.target_widget and self.target_widget.toolTip():
            pos = self.mapToGlobal(QPoint(0, self.height() + 2))
            self.popup.show_text(self.target_widget.toolTip(), pos)

class TooltipEnhancer(QObject):
    def __init__(self, app):
        super().__init__(app)
        self.tracked_widgets = {}
        self.position_update_timer = QTimer()
        self.hide_icon_timer = QTimer()
        self.hide_icon_timer.setSingleShot(True)
        self.hide_icon_timer.timeout.connect(self._hide_icon_delayed)
        self.icon_to_hide = None

        self.always_show = False
        self._load_initial_setting()

        self.icon_color = "#d2dce1"


        self.position_update_timer.setInterval(100)
        self.position_update_timer.timeout.connect(self._update_icon_positions)
        self.position_update_timer.start()

    def _calculate_icon_position(self, widget, icon_widget):

        rect = widget.rect()
        icon_size = 20
        x_local, y_local = 0, 0
        
        if isinstance(widget, QPushButton):
            is_small_icon_only = not widget.text() and not widget.icon().isNull() and widget.width() < 40
            if is_small_icon_only:
                # Place OUTSIDE small icon-only buttons (like Detach) to avoid overlap
                x_local = rect.width() + 3
                y_local = (rect.height() - icon_size) // 2
            else:
                # Place INSIDE text buttons and larger icon buttons (like Home)
                x_local = rect.width() - icon_size - 4
                y_local = (rect.height() - icon_size) // 2
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            # Place INSIDE spin boxes, but away from the arrows
            x_local = rect.width() - icon_size - 20
            y_local = (rect.height() - icon_size) // 2
        elif isinstance(widget, (QCheckBox, QLineEdit)):
            # Place INSIDE for checkboxes and line edits
            x_local = rect.width() - icon_size - 3
            y_local = (rect.height() - icon_size) // 2
        elif widget.metaObject().className() == 'LauncherButton':
            # Custom logic for large launcher buttons
            x_local = rect.width() - icon_size - 4
            y_local = 4
        else:
            # Default for other widgets: OUTSIDE
            x_local = rect.width() + 4
            y_local = (rect.height() - icon_size) // 2

        parent = widget.parentWidget()
        if parent and icon_widget.parentWidget() == parent:
            return widget.mapToParent(QPoint(x_local, y_local))
        return QPoint(x_local, y_local)

    def update_theme_colors(self, palette):
        self.icon_color = palette.get("icon_active", "#0ea5e9")
        bg_color = palette.get("background_light", "#2b2b2b")
        text_color = palette.get("text", "#f0f0f0")
        for icon in self.tracked_widgets.values():
            if icon:
                try:
                    pixmap = svg_to_icon(get_svg_content(ICON_TOOLTIP), self.icon_color).pixmap(16, 16)
                    icon.setPixmap(pixmap)
                    icon.popup._update_style(bg_color, text_color, self.icon_color)
                except:
                    pass


    def _hide_icon_delayed(self):
        if self.icon_to_hide and self.icon_to_hide.isVisible():
            self.icon_to_hide.hide()
        self.icon_to_hide = None

    def _load_initial_setting(self):
        try:
            import os
            import tomllib
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            settings_path = os.path.join(root_dir, 'config', 'settings.toml')
            if os.path.exists(settings_path):
                with open(settings_path, 'rb') as f:
                    data = tomllib.load(f)
                    self.always_show = data.get('core', {}).get('ui', {}).get('always_show_tooltips', False)
        except Exception:
            pass

    def _create_icon_for_widget(self, widget):
        if widget in self.tracked_widgets:
            existing_icon = self.tracked_widgets.pop(widget, None)
            if existing_icon:
                existing_icon.hide()
                existing_icon.deleteLater()
        if widget.property("no_custom_tooltip"):
            return None

        try:
            parent = widget.parentWidget() if widget.parentWidget() else widget
            icon = TooltipIcon(parent, color=self.icon_color)
            icon.target_widget = widget

            pos = self._calculate_icon_position(widget, icon)
            icon.move(pos)

            if self.always_show or widget.underMouse():
                icon.show()
                icon.raise_()
            else:
                icon.hide()

            self.tracked_widgets[widget] = icon
            return icon
        except Exception as e:
            print(f"Error creating tooltip icon for {widget}: {e}")
            return None

    def _update_icon_positions(self):
        widgets_to_remove = []
        for widget, icon in list(self.tracked_widgets.items()):
            try:
                if not widget or not widget.isVisible() or not icon:
                    if icon: icon.hide()
                    continue

                if not widget.toolTip():
                    widgets_to_remove.append(widget)
                    continue
                
                if icon.parentWidget() != widget.parentWidget():
                    widgets_to_remove.append(widget)
                    continue

                new_pos = self._calculate_icon_position(widget, icon)
                if icon.pos() != new_pos:
                    icon.move(new_pos)

                if self.always_show:
                    if not icon.isVisible():
                        icon.show()
                        icon.raise_()
                else:
                    is_hovered = widget.underMouse() or icon.underMouse()
                    if is_hovered:
                        # Hide previous icon immediately when hovering over a new one
                        if self.icon_to_hide and self.icon_to_hide != icon:
                            self.icon_to_hide.hide()
                        # Cancel hide timer if mouse returned
                        if self.hide_icon_timer.isActive():
                            self.hide_icon_timer.stop()
                            self.icon_to_hide = None
                        if not icon.isVisible():
                            icon.show()
                            icon.raise_()
                    elif not is_hovered and icon.isVisible():
                        # Start 0.5 second delay timer before hiding
                        if not self.hide_icon_timer.isActive():
                            self.icon_to_hide = icon
                            self.hide_icon_timer.start(500)
            except RuntimeError:
                widgets_to_remove.append(widget)

        for widget in widgets_to_remove:
            icon = self.tracked_widgets.pop(widget, None)
            if icon:
                try:
                    icon.hide()
                    icon.deleteLater()
                except RuntimeError: pass

    def eventFilter(self, obj, event):
        try:
            if isinstance(obj, QWidget) and not isinstance(obj, (TooltipIcon, CustomTooltipWindow)):
                if event.type() == QEvent.Type.Show:
                    if obj.toolTip() and obj.isEnabled() and obj not in self.tracked_widgets:
                        if not obj.property("no_custom_tooltip"):
                            self._create_icon_for_widget(obj)
    
                elif event.type() == QEvent.Type.ToolTip:
                    if not obj.property("no_custom_tooltip"):
                        return True
        except RuntimeError:
            return False
    
        try:
            return super().eventFilter(obj, event)
        except TypeError:
            return False

def setup_tooltip_enhancer(app):
    enhancer = TooltipEnhancer(app)
    app.installEventFilter(enhancer)
    app._tooltip_enhancer = enhancer

    QWidget.addGUITooltip = _addGUITooltip_method

    classes_to_patch = [QAbstractButton, QLabel, QLineEdit]
    for cls in classes_to_patch:
        if hasattr(cls, 'setText') and not getattr(cls.setText, '_chainable', False):
            orig_method = cls.setText
            def make_chainable(orig):
                def chainable_method(self, *args, **kwargs):
                    orig(self, *args, **kwargs)
                    return self
                chainable_method._chainable = True
                return chainable_method
            cls.setText = make_chainable(orig_method)

    return enhancer

__all__ =['setup_tooltip_enhancer']