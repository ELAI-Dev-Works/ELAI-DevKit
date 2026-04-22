from PySide6.QtGui import QAction

def setup(context_menu_manager, gui_instance):
    """
    Registers context menu extensions for DevPatcher.
    """
    
    def extend_patch_input_menu(menu, widget):
        cursor = widget.textCursor()
        selected_text = cursor.selectedText().strip()
        
        # Check if the selection looks like a patch command
        # Basic check: starts with <@| and ends with ---end---
        # Note: selectedText returns unicode chars U+2029 for paragraph separators, 
        # so simple strip() might not be enough for multi-line logic if strict equality is needed.
        # But for 'contains', it is safer.
        if "<@|" in selected_text and "---end---" in selected_text:
            
            action_text = gui_instance.lang.get('context_wrap_raw')
            action = QAction(action_text, widget)
            
            def wrap_selection():
                # We need to operate on the cursor
                c = widget.textCursor()
                if not c.hasSelection(): 
                    return
                
                start = c.selectionStart()
                end = c.selectionEnd()
                
                # Insert {!END} at the end
                c.setPosition(end)
                c.insertText("{!END}")
                
                # Insert {!RUN} at the start
                c.setPosition(start)
                c.insertText("{!RUN}")
                
            action.triggered.connect(wrap_selection)
            
            # Add before "Select All" or at the top
            menu.insertAction(menu.actions()[0], action)
            menu.insertSeparator(menu.actions()[1])

    # Register the patch_input widget (QTextEdit)
    context_menu_manager.register_widget(gui_instance.patch_input, extend_patch_input_menu)