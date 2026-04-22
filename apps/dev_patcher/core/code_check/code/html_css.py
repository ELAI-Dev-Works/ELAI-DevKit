from ..error_output_block import generate_error_block

def check_html_css(content: str, lang_name: str) -> str:
    try:
        from tree_sitter_language_pack import get_parser
        parser = get_parser(lang_name)
        
        content_bytes = content.encode('utf-8', errors='ignore')
        tree = parser.parse(content_bytes)
        
        if tree.root_node.has_error:
            err_list = []
            first_error_line = None
            
            def find_errors(node):
                nonlocal first_error_line
                if node.type == 'ERROR' or node.is_missing:
                    line_num = node.start_point[0] + 1
                    col = node.start_point[1]
                    if first_error_line is None:
                        first_error_line = line_num
                    err_list.append(f"Syntax error near line {line_num}, col {col}")
                for child in node.children:
                    find_errors(child)

            find_errors(tree.root_node)

            err_msg = "\n".join(err_list[:5])
            if len(err_list) > 5:
                err_msg += f"\n...and {len(err_list)-5} more."
            if not err_msg:
                err_msg = "Syntax error detected."

            return generate_error_block(content, err_msg, first_error_line)
        return None
    except Exception as e:
        return generate_error_block(content, f"Tree-sitter parser error: {e}", None)