import os
import shutil

class DocBuilder:
    """
    Scans for .exdoc, .csdoc, and .cdoc files to generate organized documentation.
    Outputs to apps/dev_patcher/doc/categories/.
    """
    def __init__(self, root_path):
        self.root_path = root_path
        self.doc_base_dir = os.path.join(root_path, "apps", "dev_patcher", "doc")
        self.core_apps_dir = os.path.join(root_path, "apps")
        self.custom_dir = os.path.join(root_path, "extensions", "custom_commands")
        
        # Global placeholders
        self.global_data = {
            'order_list': [],
            'vars_list': []
        }

    def build(self):
        print("[DocBuilder] Starting documentation build...")

        self._prepare_output_dir()

        # 1. Global Scan: Collect shared data (variables, order) from ALL docs
        self._gather_global_data()

        # 2. Generate Root Doc (DevPatcher.md - Index)
        dev_patcher_dir = os.path.join(self.core_apps_dir, "dev_patcher")
        root_doc_path = os.path.join(dev_patcher_dir, "DevPatcher.exdoc")
        if os.path.exists(root_doc_path):
            self._process_page(root_doc_path, self.doc_base_dir, "DevPatcher.md")

        # 3. Generate Syntax.md (Aggregated Commands)
        # We look specifically for syntax.csdoc to be the container
        syntax_doc_path = os.path.join(dev_patcher_dir, "core", "commands", "syntax.csdoc")
        if os.path.exists(syntax_doc_path):
            self._generate_syntax_page(syntax_doc_path)

        print("[DocBuilder] Build complete.")

    def _generate_syntax_page(self, syntax_path):
        """
        Generates the main Syntax.md file which includes the content of syntax.csdoc
        followed by all discovered commands and their arguments.
        """
        # Parse the base Syntax file
        base_data = self._parse_doc_file(syntax_path)
        content_parts = [base_data['content']]

        # Collect all commands
        all_docs = self._scan_all_doc_files()
        commands = [d for d in all_docs if 'command' in d['meta'].get('type', '')]
        
        # Sort commands by order/number
        commands.sort(key=lambda x: self._get_number(x['meta']))

        for cmd in commands:
            cmd_content = cmd['content']
            cmd_path = cmd['path']
            
            # --- Argument Processing ---
            # Scan for arguments related to this command
            args = self._scan_arguments_for_command(cmd_path)
            args.sort(key=lambda x: self._get_number(x['meta']))

            # 1. Build {args_list} replacement string (Bullet points)
            args_list_str = ""
            if args:
                desc_list = [a['meta']['args_desc'] for a in args if a['meta'].get('args_desc')]
                args_list_str = "\n".join(desc_list)

            # 2. Build {args_var} replacement string
            args_var_str = ""
            if args:
                var_list = [a['meta']['variables'] for a in args if a['meta'].get('variables')]
                args_var_str = "\n".join(var_list)

            # 3. Inject placeholders into Command Content
            if '{args_list}' in cmd_content:
                cmd_content = cmd_content.replace('{args_list}', args_list_str)
            
            # NOTE: {args_var} is often used for a variables SECTION. 
            if '{args_var}' in cmd_content:
                cmd_content = cmd_content.replace('{args_var}', args_var_str)

            # 4. Append Argument MARKDOWN content (Detailed docs)
            # Many arguments have detailed <md> blocks (usage examples etc).
            # We append these to the command content.
            for arg in args:
                if arg['content'].strip():
                    cmd_content += f"\n\n{arg['content']}"

            # Separator for commands
            content_parts.append("\n---\n")
            content_parts.append(cmd_content)

        # Join everything
        full_content = "\n".join(content_parts)

        # Inject Global Placeholders
        full_content = self._inject_global_placeholders(full_content)

        # Determine output path based on category in syntax.csdoc
        category = base_data['meta'].get('category', 'commands_and_syntax').strip()
        out_dir = os.path.join(self.doc_base_dir, "categories", category)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "syntax.md") # Force name to syntax.md or based on file

        try:
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(full_content)
        except Exception as e:
            print(f"[DocBuilder] Failed to write syntax page: {e}")

    def _scan_arguments_for_command(self, cmd_path):
        """Scans for .cdoc files in the command's directory and 'execute' subdirectory."""
        cmd_dir = os.path.dirname(cmd_path)
        # Just searching cmd_dir recursively is sufficient as it covers 'execute' and other subdirs.
        
        args_data = []
        seen_paths = set()

        for root, _, files in os.walk(cmd_dir):
            for f in files:
                if f.endswith('.cdoc') and f != os.path.basename(cmd_path):
                    full_path = os.path.join(root, f)
                    
                    # Prevent duplicates if search logic changes or links exist
                    if full_path in seen_paths:
                        continue
                    seen_paths.add(full_path)

                    data = self._parse_doc_file(full_path)
                    t = data['meta'].get('type', '')
                    if 'argument' in t or 'modifier' in t or 'sub-argument' in t:
                        args_data.append(data)
        return args_data

    def _prepare_output_dir(self):
        cat_dir = os.path.join(self.doc_base_dir, "categories")
        if os.path.exists(cat_dir):
            shutil.rmtree(cat_dir)
        os.makedirs(cat_dir, exist_ok=True)

    def _gather_global_data(self):
        """Scans everything to populate global placeholders like {command_order}."""
        all_files = self._scan_all_doc_files()
        
        # Sort files by 'number' meta for correct ordering
        all_files.sort(key=lambda x: self._get_number(x['meta']))

        for doc in all_files:
            meta = doc['meta']
            # Collect Command Order
            if meta.get('order'):
                self.global_data['order_list'].append(meta['order'])

            # Collect Global Variables
            # Exclude arguments/modifiers to prevent duplication in the global {command_var} list,
            # as they are already shown in their specific command sections.
            doc_type = meta.get('type', '')
            if 'argument' in doc_type or 'modifier' in doc_type or 'sub-argument' in doc_type:
                continue

            if meta.get('variables'):
                self.global_data['vars_list'].append(meta['variables'])

    def _process_page(self, src_path, out_dir, filename):
        """Reads source, injects Global placeholders, writes MD. Used for Index pages."""
        data = self._parse_doc_file(src_path)
        content = data['content']

        # Inject Global Placeholders
        content = self._inject_global_placeholders(content)

        # Write
        out_path = os.path.join(out_dir, filename)
        try:
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            print(f"[DocBuilder] Failed to write {out_path}: {e}")

    def _inject_global_placeholders(self, text):
        if '{command_order}' in text:
            text = text.replace('{command_order}', "\n".join(self.global_data['order_list']))
        if '{command_var}' in text:
            text = text.replace('{command_var}', "\n".join(self.global_data['vars_list']))
        return text

    def _inject_command_placeholders(self, text, cmd_path):
        """
        Locally scans for arguments related to this command to fill {args_list} and {args_var}.
        """
        if '{args_list}' not in text and '{args_var}' not in text:
            return text

        # Scan the directory of the command for arguments
        cmd_dir = os.path.dirname(cmd_path)
        
        # We look in the command's own dir and 'execute' subdir
        search_dirs = [cmd_dir]
        exec_dir = os.path.join(cmd_dir, 'execute')
        if os.path.exists(exec_dir):
            search_dirs.append(exec_dir)

        args_meta = []
        
        # Recursive scan for .cdoc files that are arguments
        for s_dir in search_dirs:
            for root, _, files in os.walk(s_dir):
                for f in files:
                    if f.endswith('.cdoc') and f != os.path.basename(cmd_path):
                        # It's a potential argument file
                        a_data = self._parse_doc_file(os.path.join(root, f))
                        t = a_data['meta'].get('type', '')
                        if 'argument' in t or 'modifier' in t:
                            args_meta.append(a_data)

        # Sort arguments
        args_meta.sort(key=lambda x: self._get_number(x['meta']))

        # Build replacement strings
        args_desc_list = []
        args_vars_list = []

        for item in args_meta:
            meta = item['meta']
            if meta.get('args_desc'):
                args_desc_list.append(meta['args_desc'])
            if meta.get('variables'):
                args_vars_list.append(meta['variables'])

        # Inject
        if '{args_list}' in text:
            text = text.replace('{args_list}', "\n".join(args_desc_list))
        
        # Note: {args_var} in a command doc usually wants ONLY that command's vars.
        # But if the user wants global vars included, they should use {command_var}.
        if '{args_var}' in text:
             text = text.replace('{args_var}', "\n".join(args_vars_list))

        return text

    def _scan_all_doc_files(self):
        """Recursively finds all doc files in apps and extensions."""
        files = []
        roots = [
            os.path.join(self.core_apps_dir, "dev_patcher", "core", "commands"),
            self.custom_dir
        ]

        for r in roots:
            if not os.path.exists(r): continue
            for root, _, filenames in os.walk(r):
                for f in filenames:
                    if f.endswith('.cdoc') or f.endswith('.csdoc'):
                        path = os.path.join(root, f)
                        data = self._parse_doc_file(path)
                        data['path'] = path
                        files.append(data)
        return files

    def _parse_doc_file(self, path):
        meta = {}
        content_lines = []
        current_block = None
        target_lang = 'en'
        reading_content = False
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for line in lines:
                stripped = line.strip()
                
                # Metadata
                if '=' in stripped and not reading_content and not current_block:
                    if stripped.startswith('#') or not stripped: continue
                    parts = stripped.split('=', 1)
                    if len(parts) == 2:
                        meta[parts[0].strip()] = parts[1].strip()
                    continue
                
                # Language block
                if stripped.startswith('<lang['):
                    l = stripped[6:-2]
                    reading_content = (l == target_lang)
                    continue
                
                if not reading_content:
                    continue
                    
                # Block tags
                # Whitelist valid blocks to prevent false positives (e.g., comments or code examples)
                valid_blocks = {'md', 'args_desc', 'order', 'variables', 'categories'}

                if stripped.startswith('<') and stripped.endswith('>') and not stripped.startswith('</'):
                    tag = stripped[1:-1]
                    if tag in valid_blocks:
                        current_block = tag
                        continue

                if stripped.startswith('</') and stripped.endswith('>'):
                    tag = stripped[2:-1]
                    if tag == current_block:
                        current_block = None
                        continue
                
                # Content Collection
                # We collect multi-line strings into meta for placeholders
                if current_block == 'md':
                    content_lines.append(line.rstrip())
                elif current_block:
                    # For all other blocks (order, variables, args_desc), accumulate text
                    if current_block not in meta:
                        meta[current_block] = ""
                    meta[current_block] += line

        except Exception as e:
            print(f"[DocBuilder] Parse error {path}: {e}")
            
        return {
            'meta': meta,
            'content': "\n".join(content_lines)
        }

    def _get_number(self, meta):
        val = meta.get('number', '999').strip()
        if val == '#': return 10000
        try:
            return int(val)
        except:
            return 999