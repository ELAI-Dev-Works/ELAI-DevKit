import os
import sys
import shutil
import zipfile
import time
import subprocess
import tempfile
import traceback

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, Toplevel, Text, Button, Label
    HAS_TK = True
except ImportError:
    HAS_TK = False

def show_custom_error(title: str, message: str, details: str):
    """
    Displays a custom error window with copyability.
    """
    if not HAS_TK:
        print(f"\n[CRITICAL ERROR] {title}\n{message}\nDetails:\n{details}\n")
        return

    try:
        dialog = Toplevel()
        dialog.title(title)
        dialog.minsize(400, 200)

        main_label = Label(dialog, text=message, wraplength=380, justify="left", font=("Segoe UI", 10))
        main_label.pack(pady=(10, 5), padx=10, fill="x")

        text_area = Text(dialog, wrap="word", height=8, width=60, font=("Courier New", 9))
        text_area.insert("1.0", details)
        text_area.config(state="disabled")
        text_area.pack(pady=5, padx=10, expand=True, fill="both")

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=(5, 10), padx=10, fill="x")

        def copy_to_clipboard():
            dialog.clipboard_clear()
            dialog.clipboard_append(details)
            copy_button.config(text="Copied!")
            dialog.after(1500, lambda: copy_button.config(text="Copy"))

        copy_button = Button(button_frame, text="Copy", command=copy_to_clipboard)
        copy_button.pack(side="left", padx=(0, 10))

        ok_button = Button(button_frame, text="Close", command=dialog.destroy)
        ok_button.pack(side="right")
        ok_button.focus_set()

        dialog.transient(dialog.master)
        dialog.grab_set()
        dialog.wait_window()
    except:
        # Fallback if GUI fails completely
        print(f"ERROR: {title}\n{message}\n{details}")

def run_external_restore(target_path, zip_path):
    """
    Executed by the temporary script. Waits for the lock to release, then restores.
    """
    root = tk.Tk()
    root.withdraw() # Hide main window

    try:
        # 1. Wait for the original process to exit
        time.sleep(3)

        # 2. Safety check
        if not os.path.exists(zip_path):
            raise FileNotFoundError(f"Backup file not found: {zip_path}")

        # 3. Clean target directory
        # We need to be careful not to delete the temp script itself, but it is in %TEMP%, so it's safe.
        if os.path.exists(target_path):
            try:
                shutil.rmtree(target_path)
            except PermissionError:
                # Retry once after a short delay
                time.sleep(2)
                shutil.rmtree(target_path)

        # 4. Create fresh directory
        os.makedirs(target_path, exist_ok=True)

        # 5. Extract
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_path)

        messagebox.showinfo(
            "Restoration Complete", 
            "The application has been successfully restored.\nYou can now restart the application."
        )

    except Exception as e:
        error_details = traceback.format_exc()
        show_custom_error(
            "Restoration Failed",
            f"An error occurred during the restoration process:\n{e}",
            error_details
        )
    finally:
        # The temp file will be cleaned up by the OS eventually, 
        # or we can try to schedule its deletion (hard to do from itself).
        pass

def spawn_temp_process(target_path, zip_path):
    """
    Copies this script to temp and runs it detached.
    """
    try:
        # 1. Get path to current script
        current_script = os.path.abspath(__file__)
        
        # 2. Create temp path
        temp_dir = tempfile.gettempdir()
        temp_script = os.path.join(temp_dir, f"elai_restore_{int(time.time())}.py")
        
        # 3. Copy self
        shutil.copy2(current_script, temp_script)
        
        # 4. Launch detached
        python_exe = sys.executable
        
        # Arguments for the new process
        args = [python_exe, temp_script, "--target", target_path, "--zip", zip_path]
        
        # Launch independently
        if sys.platform == "win32":
            subprocess.Popen(args, creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            # POSIX
            subprocess.Popen(args, start_new_session=True)
            
        return True
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to spawn recovery process: {e}")
        return False

def run_ui_mode():
    """
    Standard mode: User interacts to select backup.
    """
    root = tk.Tk()
    root.withdraw()

    app_root_path = os.path.dirname(os.path.abspath(__file__))

    user_choice = messagebox.askyesno(
        "PatcherApp Launch Error",
        "It was not possible to launch the main application.\n\n"
        "Do you want to restore it from a backup?"
    )

    if not user_choice:
        return

    backup_path = filedialog.askopenfilename(
        title="Select .zip backup for recovery",
        filetypes=[("Zip archives", "*.zip"), ("All files", "*.*")],
        initialdir=os.path.dirname(app_root_path)
    )

    if not backup_path:
        return

    # Handover to temp process
    if spawn_temp_process(app_root_path, backup_path):
        # We exit successfully so launch.py can close
        sys.exit(0)

def run_console_mode():
    """
    Fallback mode for Linux/Headless environments where Tkinter is missing.
    """
    print("\n" + "="*50)
    print("      ELAI-DevKit Recovery Utility (Console)")
    print("="*50)
    print("\nIt was not possible to launch the main application.")

    while True:
        choice = input("\nDo you want to restore it from a backup? [y/n]: ").strip().lower()
        if choice == 'n':
            return
        if choice == 'y':
            break

    app_root_path = os.path.dirname(os.path.abspath(__file__))
    default_dir = os.path.dirname(app_root_path)

    print(f"\nPlease enter the full path to the .zip backup file.")
    print(f"Default search directory: {default_dir}")

    while True:
        backup_path = input("Backup Path: ").strip()
        # Remove quotes if user dragged and dropped file
        backup_path = backup_path.strip('"\'')

        if not backup_path:
            print("Operation cancelled.")
            return

        if os.path.exists(backup_path) and os.path.isfile(backup_path) and backup_path.lower().endswith('.zip'):
            break
        else:
            print("[ERROR] File not found or not a .zip archive. Try again.")

    print(f"\n[INFO] Starting recovery from: {backup_path}")
    if spawn_temp_process(app_root_path, backup_path):
        sys.exit(0)


if __name__ == "__main__":
    # Check if we are in worker mode
    if len(sys.argv) > 4 and sys.argv[1] == "--target" and sys.argv[3] == "--zip":
        target = sys.argv[2]
        zip_file = sys.argv[4]
        run_external_restore(target, zip_file)
    else:
        if HAS_TK:
            run_ui_mode()
        else:
            run_console_mode()