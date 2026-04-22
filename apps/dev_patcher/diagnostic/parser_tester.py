import os
import sys

# Ensure the root path is in sys.path to allow importing core modules
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from apps.dev_patcher.core.parser import parse_patch_content

def test_basic_parsing():
    text = "<@|TEST -print\nHello World\n---end---"
    cmds = parse_patch_content(text)
    assert len(cmds) == 1, f"Expected 1 command, got {len(cmds)}"
    assert cmds[0][0] == 'TEST', f"Expected 'TEST', got {cmds[0][0]}"
    assert cmds[0][1] == ['-print'], f"Expected ['-print'], got {cmds[0][1]}"
    assert cmds[0][2] == 'Hello World', f"Expected 'Hello World', got {repr(cmds[0][2])}"

def test_single_line_comments():
    # Comments outside commands are completely ignored.
    # Comments inside commands are intentionally preserved in the content
    # to prevent deletion of target Python code comments.
    text = "<-@ Just a comment @->\n<@|TEST -print\nLine 1\n<-@ Inline comment @->\nLine 2\n---end---"
    cmds = parse_patch_content(text)
    assert len(cmds) == 1
    assert cmds[0][2] == 'Line 1\n<-@ Inline comment @->\nLine 2', f"Expected preserved comments, got {repr(cmds[0][2])}"

def test_multi_line_comments():
    # Multi-line comments hide commands enclosed inside them.
    text = "Line 0\n#@#\n<@|TEST -ignore_me\nHello\n---end---\n#@#\n<@|TEST -print\nLine 1\n#@#\nignored 1\n#@#\nLine 2\n---end---"
    cmds = parse_patch_content(text)
    assert len(cmds) == 1
    assert cmds[0][1] == ['-print']
    assert cmds[0][2] == 'Line 1\n#@#\nignored 1\n#@#\nLine 2', f"Got {repr(cmds[0][2])}"

def test_raw_mode_execution():
    # Raw mode should treat DPCL syntax as plain text, including preventing
    # structural tags from triggering parses. Variable @APP-ROOT is safely preserved.
    text = "{!RUN}<@|MANAGE -write @APP-ROOT/doc.md\n# Title\n<@|TEST -print\n<-@ comment @->\n---end---\n@APP-ROOT is safe\n---end---{!END}"
    cmds = parse_patch_content(text)
    assert len(cmds) == 1
    assert cmds[0][0] == 'MANAGE'
    assert cmds[0][1] == ['-write', '@APP-ROOT/doc.md']
    
    expected_content = "# Title\n<@|TEST -print\n<-@ comment @->\n---end---\n@APP-ROOT is safe"
    assert cmds[0][2] == expected_content, f"Expected raw content preservation, got {repr(cmds[0][2])}"

def test_markers_and_blocks():
    text = "<@|EDIT -insert main.py\n---scope---\ndef main():\n---old---\n{code_start|content|code_end}\n---new---\n    pass\n---end---"
    cmds = parse_patch_content(text)
    assert len(cmds) == 1
    assert cmds[0][0] == 'EDIT'
    assert '---scope---' in cmds[0][2]
    assert '---old---' in cmds[0][2]
    assert '{code_start|content|code_end}' in cmds[0][2]
    assert '---new---' in cmds[0][2]

def test_precise_patching_stripping():
    text = "<@|EDIT -v2 -replace main.py\n---old---\n 12| x = 1\n---new---\n 12| x = 2\n---end---"
    flags = {"enabled": True, "lineno": True}
    cmds = parse_patch_content(text, experimental_flags=flags)
    assert len(cmds) == 1
    assert '12|' not in cmds[0][2]
    assert 'x = 1' in cmds[0][2]
    assert 'x = 2' in cmds[0][2]

def run_tests():
    tests =[
        ("Basic Command Parsing", test_basic_parsing),
        ("Single-line Comments Handling", test_single_line_comments),
        ("Multi-line Comments Handling", test_multi_line_comments),
        ("Raw Mode Execution ({!RUN} ... {!END})", test_raw_mode_execution),
        ("Markers and Blocks Preservation", test_markers_and_blocks),
        ("Precise Patching Line Number Stripping", test_precise_patching_stripping)
    ]

    passed = 0
    failed =[]

    print("Starting DevPatcher Parser Unit Tests...")
    for name, test_func in tests:
        try:
            test_func()
            print(f"  [PASS] {name}")
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {name}: {e}")
            failed.append((name, str(e)))
        except Exception as e:
            import traceback
            print(f"  [ERROR] {name}: {e}")
            failed.append((name, str(e)))

    print(f"\nParser Tests Summary: {passed}/{len(tests)} passed.")
    if failed:
        print("\nFailed Tests:")
        for name, err in failed:
            print(f"  - {name}: {err}")
        sys.exit(1)
    sys.exit(0)

if __name__ == '__main__':
    run_tests()