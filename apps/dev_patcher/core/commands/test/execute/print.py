from typing import Tuple
from typing import List

def run(args: list, content: str, fs_handler) -> Tuple[bool, str]:
    """
    Executes the '-print' action for the TEST command.

    :param args: The original list of arguments.
    :param content: The content block of the command.
    :param fs_handler: The file system handler.
    :return: A tuple (success, message).
    """
    processed_content = content.replace("@ROOT", fs_handler.root)
    return True, processed_content

def tests(vfs) -> List[Tuple[str, bool, str]]:
    success, msg = run(['-print'], 'Hello @ROOT!', vfs)
    passed = success and msg == f"Hello {vfs.root}!"
    return[("Print replaces @ROOT", passed, msg)]
