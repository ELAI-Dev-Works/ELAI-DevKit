import os
import zipfile
import datetime
import subprocess
from typing import Tuple, List, Optional

from systems.project.ignore_handler import IgnoreHandler


class BackupBuilder:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.actions =[]

    def use(self, action: str, path: str = ""):
        if path:
            path = path.replace('@ROOT/', '').replace('@ROOT\\', '').replace('@ROOT', '').strip('\'"')
            if path.startswith('/') or path.startswith('\\'): 
                path = path[1:]

        action_tuple = (action, path)
        if action_tuple not in self.actions:
            self.actions.append(action_tuple)

def create_backup(project_path: str, ignore_dirs: Optional[List[str]] = None, ignore_files: Optional[List[str]] = None, backup_actions: Optional[List[Tuple[str, str]]] = None) -> Tuple[bool, str]:
    """
    Creates a .zip archive of the entire project folder, ignoring specified files and folders.
    The archive name includes the date and time.
    :param project_path: The path to the folder to be archived.
    :param ignore_dirs: A list of directory names/patterns to ignore (e.g., ['.venv', '__pycache__']).
    :param ignore_files: A list of file names/patterns to ignore (e.g.,['.gitignore', '*.pyc']).
    :return: A tuple (success, message/file path).
    """
    try:
        if not os.path.isdir(project_path):
            return False, f"Backup path is not a folder: {project_path}"
        handler = IgnoreHandler(ignore_dirs or [], ignore_files or[], context='git')
        has_files = False
        for root, dirs, files in os.walk(project_path):
            dirs[:] =[d for d in dirs if d != '.git' and not handler.is_ignored(d, is_dir=True)]
            for file in files:
                if not handler.is_ignored(file, is_dir=False):
                    has_files = True
                    break
            if has_files:
                break

        if not has_files:
            return True, "Project is empty. Git commit skipped."

        handler = IgnoreHandler(ignore_dirs or[], ignore_files or[], context='backup')
        has_files = False
        for root, dirs, files in os.walk(project_path):
            dirs[:] =[d for d in dirs if d != '.git' and not handler.is_ignored(d, is_dir=True)]
            for file in files:
                if not handler.is_ignored(file, is_dir=False):
                    has_files = True
                    break
            if has_files:
                break

        if not has_files:
            return True, "Project is empty. Backup skipped."

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        project_name = os.path.basename(project_path)
        backup_filename = f"{project_name}_backup_{timestamp}.zip"

        parent_dir = os.path.dirname(project_path)
        archive_path = os.path.join(parent_dir, backup_filename)

        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if backup_actions:
                lines =[f"{a}|{p}" for a, p in backup_actions]
                zipf.writestr('.devpatcher_changes.txt', "\n".join(lines))
            for root, dirs, files in os.walk(project_path):
                # Exclude directories from further traversal using the new handler
                dirs[:] = [d for d in dirs if not handler.is_ignored(d, is_dir=True)]

                # Exclude files using the new handler
                for file in files:
                    if handler.is_ignored(file, is_dir=False):
                        continue

                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, project_path)
                    zipf.write(file_path, arcname)

        return True, archive_path

    except Exception as e:
        return False, f"Failed to create backup: {e}"

def create_git_backup(project_path: str, commit_message: str, ignore_dirs: list, ignore_files: list, backup_actions: list = None) -> Tuple[bool, str]:
    try:
        if not os.path.isdir(project_path):
            return False, f"Backup path is not a folder: {project_path}"

        git_dir = os.path.join(project_path, '.git')
        if not os.path.exists(git_dir):
            subprocess.run(["git", "init"], cwd=project_path, capture_output=True, text=True, check=True)

        handler = IgnoreHandler(ignore_dirs or [], ignore_files or[], context='git')
        exclude_path = os.path.join(git_dir, 'info', 'exclude')

        if os.path.exists(os.path.dirname(exclude_path)):
            existing_excludes = ""
            if os.path.exists(exclude_path):
                with open(exclude_path, 'r', encoding='utf-8') as f:
                    existing_excludes = f.read()

            with open(exclude_path, 'a', encoding='utf-8') as f:
                for p in handler.ignore_dir_patterns:
                    if f"{p}/" not in existing_excludes and p not in existing_excludes:
                        f.write(f"\n{p}/")
                for p in handler.ignore_file_patterns:
                    if p not in existing_excludes:
                        f.write(f"\n{p}")

        subprocess.run(["git", "add", "."], cwd=project_path, capture_output=True, text=True, check=True)

        status = subprocess.run(["git", "status", "--porcelain"], cwd=project_path, capture_output=True, text=True)
        if not status.stdout.strip():
            return True, "No changes to commit."

        subprocess.run(["git", "commit", "-m", commit_message], cwd=project_path, capture_output=True, text=True, check=True)

        return True, "Git commit created successfully."

    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.strip() if e.stderr else str(e)
        return False, f"Git command failed: {err_msg}"
    except Exception as e:
        return False, f"Failed to create git backup: {e}"