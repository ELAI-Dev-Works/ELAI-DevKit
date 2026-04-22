import re

class PatchCorrector:
    """
    Analyzes raw patch text for syntax errors and suggests corrections.
    """
    def __init__(self, patch_text: str, experimental_flags: dict, lang_manager):
        self.patch_text = patch_text
        self.flags = experimental_flags or {}
        self.lang = lang_manager
        self.issues = []

    def analyze(self):
        """
        Runs all checks and returns a list of found issues.
        """
        self.issues = []
        lines = self.patch_text.splitlines()

        # Run checks in a specific order
        self._check_global_markers(lines)
        self._check_all_commands()
        self._check_feature_suggestions()

        return self.issues

    def _add_issue(self, issue_data):
        """Adds a fully formed issue dictionary to the list."""
        self.issues.append(issue_data)

    def _check_global_markers(self, lines):
        """Checks for misplaced markers that have leading whitespace."""
        marker_pattern = re.compile(r"^(\s+)(---(?:old|new|end|scope|structure|project|file_end)---)")
        for line in lines:
            match = marker_pattern.match(line)
            if match:
                whitespace, marker = match.groups()
                original_line = line
                corrected_line = marker
                self._add_issue({
                    "original": original_line,
                    "corrected": corrected_line,
                    "description": self.lang.get('correction_whitespace_marker'),
                    "type": "syntax"
                })

    def _check_feature_suggestions(self):
        """Checks for usage of features that are not enabled."""
        if "---scope---" in self.patch_text and not self.flags.get('scope'):
            self._add_issue({
                "original": "---scope---",
                "corrected": "---scope---",
                "description": self.lang.get('correction_enable_scope'),
                "type": "suggestion",
                "feature": "scope"
            })

        if re.search(r"^\s*\d+\s*\|", self.patch_text, re.MULTILINE) and not self.flags.get('lineno'):
            self._add_issue({
                "original": "e.g., '12| code'",
                "corrected": "e.g., '12| code'",
                "description": self.lang.get('correction_enable_lineno'),
                "type": "suggestion",
                "feature": "lineno"
            })

    def _check_all_commands(self):
        """Iterates through command blocks and validates each one."""
        # This regex is non-greedy and handles nested-like structures better
        command_blocks = re.finditer(r"(<@\|.*?---end---)", self.patch_text, re.DOTALL)

        for block_match in command_blocks:
            full_block = block_match.group(1)

            # Extract header
            header_match = re.search(r"<@\|(.*?)\n", full_block)
            if not header_match: continue

            header = header_match.group(1).strip()
            parts = header.split()
            command_name = parts[0].upper()
            args = parts[1:]

            # Extract content
            content = full_block.split('\n', 1)[1].rsplit('---end---', 1)[0]

            validator_func = getattr(self, f"_validate_{command_name.lower()}", None)
            if validator_func:
                validator_func(full_block, command_name, args, content)

    def _validate_manage(self, full_block, command_name, args, content):
        if not args: return

        # Check argument order (flag should be first)
        if not args[0].startswith('-') and len(args) > 1 and args[1].startswith('-'):
            original_header = f"<@|{command_name} {' '.join(args)}"
            corrected_args = [args[1], args[0]] + args[2:]
            corrected_header = f"<@|{command_name} {' '.join(corrected_args)}"
            corrected_block = full_block.replace(original_header, corrected_header)
            self._add_issue({
                "original": full_block, "corrected": corrected_block,
                "description": self.lang.get('correction_manage_order'), "type": "syntax"
            })

        # Check -search syntax
        if args[0] == '-search':
            has_search_term = any(arg.startswith('<') and arg.endswith('>') for arg in args)
            if not has_search_term:
                header = f"<@|{command_name} {' '.join(args)}"
                corrected_header = f"{header} <keyword>"
                self._add_issue({
                    "original": full_block, "corrected": full_block.replace(header, corrected_header),
                    "description": self.lang.get('correction_manage_search_missing_keywords'),
                    "type": "syntax"
                })


    def _validate_edit(self, full_block, command_name, args, content):
        if "-replace" in args or "-insert" in args:
            if "---new---" not in content:
                # Insert a blank ---new--- block before ---end---
                corrected_content = content.replace("---end---", "---new---\n\n---end---", 1)
                self._add_issue({
                    "original": full_block, "corrected": full_block.replace(content, corrected_content),
                    "description": self.lang.get('correction_edit_missing_new'), "type": "syntax"
                })
        if "-remove" in args:
            if "---new---" in content:
                # Remove the ---new--- block and its content entirely
                corrected_content = re.sub(r"---new---.*?(?=---end---)", "", content, flags=re.DOTALL)
                self._add_issue({
                    "original": full_block, "corrected": full_block.replace(content, corrected_content),
                    "description": self.lang.get('correction_edit_remove_has_new'), "type": "syntax"
                })

    def _validate_project(self, full_block, command_name, args, content):
        header = f"<@|{command_name} {' '.join(args)}"

        # A more robust argument extractor that handles spaces inside < >
        def find_arg_value(arg_name, args_list):
            try:
                if arg_name not in args_list:
                    return None
                start_index = args_list.index(arg_name) + 1
                if start_index >= len(args_list):
                    return None  # No value after the arg name

                # Check if value is a single token like <value>
                if args_list[start_index].startswith('<') and args_list[start_index].endswith('>'):
                    return args_list[start_index]

                # Check for multi-token value like <My Project> or <(My Project)>
                if args_list[start_index].startswith('<'):
                    value_parts = []
                    # Start searching from the token after arg_name
                    for i in range(start_index, len(args_list)):
                        part = args_list[i]
                        value_parts.append(part)
                        if part.endswith('>'):
                            # Successfully found the end, join and return
                            return " ".join(value_parts)
                    # If loop finishes, we have an unclosed value, which is an error
                    return None

                return None
            except ValueError:
                # arg_name is not in the list
                return None

        if not find_arg_value('-run', args):
            self._add_issue({
                "original": full_block, "corrected": full_block.replace(header, f"{header} -run <main.py>"),
                "description": self.lang.get('correction_project_missing_run'),
                "type": "syntax"
            })

        if not find_arg_value('-requi', args):
            self._add_issue({
                "original": full_block, "corrected": full_block.replace(header, f"{header} -requi <None>"),
                "description": self.lang.get('correction_project_missing_requi'),
                "type": "syntax"
            })

        if '-name' in args:
            val = find_arg_value('-name', args)
            if not val:
                # Missing value
                name_index = args.index("-name")
                token_to_replace = ' '.join(args[name_index+1:]) if name_index + 1 < len(args) else ""
                self._add_issue({
                    "original": full_block, "corrected": full_block,
                    "description": self.lang.get('correction_project_missing_name'),
                    "type": "interactive",
                    "input_request": {
                        "label": "Enter a project name. For names with spaces, use <(Project Name)>:",
                        "token_to_replace": token_to_replace
                    }
                })
            else:
                # Check if spaces are present but parens are missing inside <...>
                inner = val[1:-1]
                if ' ' in inner and not (inner.startswith('(') and inner.endswith(')')):
                    corrected_val = f"<({inner})>"
                    self._add_issue({
                        "original": full_block,
                        "corrected": full_block.replace(val, corrected_val),
                        "description": "The -name argument contains spaces but is not wrapped in parentheses. The new format is <(Name With Spaces)>.",
                        "type": "syntax"
                    })