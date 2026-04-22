import re
import html
from PySide6.QtGui import QTextDocument

class MarkdownStyler:
    """
    Helper class to render Markdown with custom styled code blocks and CSS.
    """
    def __init__(self, theme_manager, lang_manager=None):
        self.theme_manager = theme_manager
        self.lang = lang_manager
        self.code_blocks = {}
        self.inline_blocks = {}

    def _get_palette(self):
        try:
            import importlib
            module_path = f"systems.gui.themes.color.{self.theme_manager.current_color_scheme}"
            mod = importlib.import_module(module_path)
            return mod.palette
        except:
            return {
                "background": "#2b2b2b", "text": "#f0f0f0",
                "background_light": "#3c3c3c", "border": "#555",
                "button": "#4a4a4a", "selection": "#29b8db"
            }

    def _process_headers(self, text):
        """
        Scans for Markdown headers (#), generates anchors, and builds TOC data.
        Returns: (modified_text, toc_list)
        toc_list = [(level, title, anchor_id), ...]
        """
        toc_list = []
        new_lines = []
    
        # Regex for headers (1-6 hashes)
        header_pattern = re.compile(r"^(#{1,6})\s+(.*)")
    
        lines = text.splitlines()
        for i, line in enumerate(lines):
            match = header_pattern.match(line)
            if match:
                hashes, title = match.groups()
                level = len(hashes)
                clean_title = title.strip()
    
                # Generate simple ID: header-index
                anchor_id = f"header-{len(toc_list)}"
    
                # Inject anchor HTML before the header
                anchor_tag = f"<a name=\"{anchor_id}\"></a>"
    
                new_lines.append(anchor_tag)
                new_lines.append(line)
    
                toc_list.append((level, clean_title, anchor_id))
            else:
                new_lines.append(line)
    
        return "\n".join(new_lines), toc_list
    
    def render(self, markdown_text):
        """
        Converts Markdown to styled HTML with interactive code blocks.
        Returns: (html_content, css, toc_data)
        """
        self.code_blocks = {}
        self.inline_blocks = {}
    
        # --- Step 1: Pre-process Code Blocks (Fenced) ---
        # Regex matches ```lang ... ``` or just ``` ... ```
        # We replace them with a safe alphanumeric marker to avoid Markdown formatting
        block_pattern = re.compile(r"^```(?P<lang>\w+)?\s*\n(?P<code>.*?)```", re.DOTALL | re.MULTILINE)

        def replace_block(match):
            code = match.group('code')
            block_id = len(self.code_blocks)
            self.code_blocks[str(block_id)] = code
            return f"MERKBLOCK{block_id}MERK"

        text_stage_1 = block_pattern.sub(replace_block, markdown_text)

        # --- Step 2: Pre-process Inline Code ---
        # Matches `code`
        inline_pattern = re.compile(r"`([^`]+)`")

        def replace_inline(match):
            code = match.group(1)
            block_id = len(self.inline_blocks)
            self.inline_blocks[str(block_id)] = code
            return f"MERKINLINE{block_id}MERK"

        text_stage_2 = inline_pattern.sub(replace_inline, text_stage_1)

        # --- Step 3: Enforce Hard Line Breaks ---
        # Replace single newlines with "  \n" to force Markdown to render them as breaks.
        # We do this AFTER extracting code blocks so we don't mess up code formatting.
        text_stage_3 = text_stage_2.replace('\n', '  \n')

        # --- Step 4: Convert to HTML ---
        doc = QTextDocument()
        doc.setMarkdown(text_stage_3)
        base_html = doc.toHtml()

        colors = self._get_palette()
        color_scheme = self.theme_manager.current_color_scheme
        is_dark = color_scheme in ('dark', 'ocean')

        # --- Step 5: Restore and Style Inline Code ---
        # Inline code colors
        inline_bg = "#181818" if is_dark else "#e6e6e6"
        # Soft blue-blue: darker than cyan, lighter than pure blue.
        inline_text = "#6495ED" if is_dark else "#0055aa"

        for bid, code in self.inline_blocks.items():
            escaped = html.escape(code)
            replacement = (
                f"<span style='font-family: Consolas, monospace; font-weight: bold; "
                f"background-color: {inline_bg}; color: {inline_text}; "
                f"padding: 2px 5px; border-radius: 4px;'>{escaped}</span>"
            )
            base_html = base_html.replace(f"MERKINLINE{bid}MERK", replacement)

        # --- Step 6: Restore and Style Code Blocks ---
        # Block colors
        cb_bg = "#151515" if is_dark else "#f2f2f2"
        cb_header_bg = "#252525" if is_dark else "#d9d9d9"
        cb_border = "#444" if is_dark else "#ccc"
        cb_text = "#e0e0e0" if is_dark else "#333"
        link_color = "#5caeff" if is_dark else "#0066cc"
        
        # Translate Link text
        copy_text = "COPY CODE"
        if self.lang:
            copy_text = self.lang.get('doc_copy_code_link')
        
        for bid, code in self.code_blocks.items():
            # Replace newlines with <br> to ensure they are rendered correctly in Qt's HTML engine
            escaped = html.escape(code).replace('\n', '<br>')
        
            # HTML Table for the code window look
            code_html = (
                f"<table width='100%' cellspacing='0' cellpadding='0' style='margin-top: 15px; margin-bottom: 15px; border: 1px solid {cb_border};'>"
                f"<tr><td bgcolor='{cb_header_bg}' style='padding: 6px 12px; border-bottom: 1px solid {cb_border};'>"
                f"<div align='right'><a href='action:copy_{bid}' style='text-decoration:none; color:{link_color}; font-family: Segoe UI; font-weight:bold; font-size: 10pt;'>{copy_text}</a></div>"
                f"</td></tr>"
                f"<tr><td bgcolor='{cb_bg}' style='padding: 12px;'>"
                f"<div style='font-family: Consolas, monospace; font-size: 11pt; color: {cb_text}; margin: 0; white-space: pre-wrap;'>{escaped}</div>"
                f"</td></tr>"
                f"</table>"
            )

            # Use Regex to replace the marker even if it's wrapped in paragraph tags
            regex = re.compile(fr"(<p[^>]*>\s*)?MERKBLOCK{bid}MERK(\s*</p>)?")
            base_html = regex.sub(lambda x: code_html, base_html)

        # --- Step 7: Post-process HTML for TOC Headers ---
        # Inject IDs into h1-h6 tags for navigation (Moved outside loop to handle text without code blocks)
        final_html, toc_data = self._inject_header_anchors(base_html)

        return final_html, self._generate_css(colors), toc_data
    
    def _inject_header_anchors(self, html_content):
        """
        Scans HTML for <hN> tags, injects <a name="...">, and builds TOC.
        """
        toc_list = []
    
        def replace_header(match):
            tag_name = match.group(1) # h1, h2...
            attrs = match.group(2)
            text = match.group(3)
    
            anchor_id = f"header-{len(toc_list)}"
            level = int(tag_name[1])
            clean_title = re.sub(r'<[^>]+>', '', text).strip() # Strip tags for TOC display
    
            toc_list.append((level, clean_title, anchor_id))
    
            # Inject anchor inside the header
            return f"<{tag_name}{attrs}><a name=\"{anchor_id}\"></a>{text}</{tag_name}>"
    
        # Regex to match <h1 ...>Content</h1>
        # Group 1: tag (h1-h6)
        # Group 2: attributes (optional)
        # Group 3: content
        pattern = re.compile(r"<(h[1-6])([^>]*)>(.*?)</\1>", re.IGNORECASE | re.DOTALL)
    
        modified_html = pattern.sub(replace_header, html_content)
        return modified_html, toc_list
    
    def _generate_css(self, c):
        return f"""
            body {{
                font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
                font-size: 11pt;
                color: {c['text']};
                background-color: {c['background']};
                line-height: 1.6;
            }}
            h1 {{ font-size: 22pt; font-weight: bold; color: {c.get('selection', '#29b8db')}; margin-top: 20px; margin-bottom: 15px; border-bottom: 2px solid {c['border']}; padding-bottom: 8px; }}
            h2 {{ font-size: 18pt; font-weight: bold; color: {c['text']}; margin-top: 20px; margin-bottom: 12px; border-bottom: 1px solid {c['border']}; padding-bottom: 5px; }}
            h3 {{ font-size: 15pt; font-weight: bold; color: {c['text']}; margin-top: 18px; margin-bottom: 8px; }}
            h4, h5, h6 {{ font-size: 12pt; font-weight: bold; color: {c['text']}; margin-top: 15px; margin-bottom: 5px; }}
            p {{ line-height: 1.6; margin-bottom: 12px; }}
            a {{ color: {c['selection']}; text-decoration: none; font-weight: 500; }}
            ul, ol {{ margin-bottom: 12px; margin-top: 0px; padding-left: 20px; }}
            li {{ margin-bottom: 6px; line-height: 1.5; }}
            blockquote {{
                margin: 15px 0;
                padding: 10px 15px;
                background-color: {c.get('background_light', '#333')};
                border-left: 4px solid {c['selection']};
                color: {c.get('text_dim', '#ccc')};
                font-style: italic;
            }}
            hr {{
                border: 0;
                border-bottom: 1px solid {c['border']};
                margin: 20px 0;
            }}
            table {{
                border-collapse: collapse;
                margin-bottom: 15px;
                border: 1px solid {c['border']};
                width: 100%;
            }}
            th, td {{
                border: 1px solid {c['border']};
                padding: 8px 12px;
                text-align: left;
            }}
            th {{
                background-color: {c.get('background_light', '#333')};
                font-weight: bold;
            }}
        """

    def get_code_content(self, block_id):
        return self.code_blocks.get(str(block_id))