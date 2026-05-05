from .base import BaseArchitecture
import os

class WebArchitecture(BaseArchitecture):
    def get_launch_command(self):
        target_launch_file = os.path.join(self.temp_dir, self.launch_file)

        auditor_js = os.path.join(self.temp_dir, "_elai_web_auditor.js")
        if os.path.exists(auditor_js) and os.path.exists(target_launch_file):
            try:
                with open(target_launch_file, 'r', encoding='utf-8') as f:
                    html = f.read()
                # Natively prevent external API calls & data exfiltration in the browser
                csp_tag = "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob:; connect-src 'self' ws://127.0.0.1:* http://127.0.0.1:*;\">"
                if "<head>" in html:
                    html = html.replace("<head>", f"<head>\n    {csp_tag}\n    <script src=\"_elai_web_auditor.js\"></script>")
                else:
                    html = f"{csp_tag}\n<script src=\"_elai_web_auditor.js\"></script>\n{html}"
                with open(target_launch_file, 'w', encoding='utf-8') as f:
                    f.write(html)
            except Exception:
                pass

        return f"HTML:{target_launch_file}"