import os
import zipfile
import subprocess
import datetime
from typing import List, Dict, Tuple

def get_available_backups(project_path: str, method: str = 'all') -> List[Dict]:
    backups =[]
    if not project_path or not os.path.exists(project_path):
        return backups

    if method in ['zip', 'all']:
        parent_dir = os.path.dirname(project_path)
        project_name = os.path.basename(project_path)
        if os.path.exists(parent_dir):
            for f in os.listdir(parent_dir):
                if f.startswith(f"{project_name}_backup_") and f.endswith(".zip"):
                    file_path = os.path.join(parent_dir, f)
                    mtime = os.path.getmtime(file_path)
                    dt = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                    backups.append({
                        'type': 'zip',
                        'id': file_path,
                        'display': f"[ZIP] {dt} - {f}",
                        'timestamp': mtime
                    })

    if method in ['git', 'all']:
        git_dir = os.path.join(project_path, '.git')
        if os.path.exists(git_dir):
            try:
                res = subprocess.run(["git", "log", "--pretty=format:%H|%ct|%cd|%s", "--date=short"], cwd=project_path, capture_output=True, text=True)
                if res.returncode == 0 and res.stdout:
                    for line in res.stdout.splitlines():
                        parts = line.split('|', 3)
                        if len(parts) == 4:
                            backups.append({
                                'type': 'git',
                                'id': parts[0],
                                'display': f"[GIT] {parts[2]} - {parts[0][:7]} : {parts[3]}",
                                'timestamp': float(parts[1])
                            })
            except Exception:
                pass

    backups.sort(key=lambda x: x['timestamp'], reverse=True)
    return backups

def restore_backup(project_path: str, backup_info: Dict, mode: str) -> Tuple[bool, str]:
    b_type = backup_info['type']
    b_id = backup_info['id']

    try:
        if b_type == 'zip':
            with zipfile.ZipFile(b_id, 'r') as zip_ref:
                if mode == 'changes' and '.devpatcher_changes.txt' in zip_ref.namelist():
                    changes_data = zip_ref.read('.devpatcher_changes.txt').decode('utf-8')
                    extracted_count = 0
                    deleted_count = 0

                    for line in changes_data.splitlines():
                        line = line.strip()
                        if not line: continue

                        if '|' in line:
                            action, path = line.split('|', 1)
                        else:
                            action, path = 'replace', line

                        abs_path = os.path.join(project_path, path)

                        if action == 'replace':
                            zip_path = path.replace('\\', '/')
                            if zip_path in zip_ref.namelist():
                                zip_ref.extract(zip_path, project_path)
                                extracted_count += 1
                        elif action == 'delete':
                            if os.path.exists(abs_path):
                                if os.path.isdir(abs_path):
                                    shutil.rmtree(abs_path)
                                else:
                                    os.remove(abs_path)
                                deleted_count += 1
                        elif action == 'delete_dir':
                            if os.path.isdir(abs_path):
                                shutil.rmtree(abs_path)
                                deleted_count += 1

                    return True, f"Restored {extracted_count} files, deleted {deleted_count} created items."
                else:
                    zip_ref.extractall(project_path)
                    return True, "Restored all files from ZIP (Full Replace)."

        elif b_type == 'git':
            if mode == 'changes':
                res = subprocess.run(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", b_id], cwd=project_path, capture_output=True, text=True)
                if res.returncode == 0 and res.stdout:
                    files_to_restore =[f.strip() for f in res.stdout.splitlines() if f.strip()]
                    if files_to_restore:
                        subprocess.run(["git", "checkout", b_id, "--"] + files_to_restore, cwd=project_path, capture_output=True, check=True)
                        return True, f"Restored {len(files_to_restore)} changed files from Git commit."
                    return True, "No files were changed in that commit."
                else:
                    subprocess.run(["git", "checkout", b_id, "--", "."], cwd=project_path, capture_output=True, check=True)
                    return True, "Restored working tree to Git commit (Fallback Full)."
            else:
                subprocess.run(["git", "checkout", b_id, "--", "."], cwd=project_path, capture_output=True, check=True)
                return True, "Restored working tree to Git commit (Full Replace)."

        return False, "Unknown backup type."
    except Exception as e:
        return False, str(e)