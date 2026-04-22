from PySide6.QtCore import QObject, Signal, QThread
from typing import List, Tuple, Any
import os
import time
import datetime

from .patch_checking import plan_dynamic_patch
from .patcher import run_patch
from .fs_handler import RealFileSystem, VirtualFileSystem


class PatchWorker(QObject):
    """
    QObject worker to handle long-running patch tasks.
    """
    progress_log = Signal(str)
    command_result = Signal(bool, str, tuple)
    simulation_finished = Signal(bool, dict)
    execution_finished = Signal(list, float)
    error = Signal(str)

    def __init__(self, commands: List[Tuple], target_path: str, experimental_flags: dict,
                 ignore_dirs: list, ignore_files: list, mode: str, lang, parent=None):
        super().__init__(parent)
        self.commands = commands
        self.target_path = target_path
        self.experimental_flags = experimental_flags
        self.ignore_dirs = ignore_dirs
        self.ignore_files = ignore_files
        self.mode = mode
        self.lang = lang

    def run(self):
        try:
            if self.mode == 'simulate':
                self._run_simulation()
            elif self.mode == 'execute':
                self._run_execution()
            else:
                self.error.emit(f"Unknown worker mode: {self.mode}")
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self.error.emit(f"Critical error in worker thread: {e}\n{tb}")

    def _run_simulation(self):
        # plan_dynamic_patch returns a generator
        sim_gen = plan_dynamic_patch(self.commands, self.target_path,
                                     self.experimental_flags, self.ignore_dirs, self.lang)
    
        final_result = {}
        success = True
    
        try:
            for i, item in enumerate(sim_gen):
                if isinstance(item, tuple) and item[0] == 'finished':
                    final_result = item[1]
                    break
                elif isinstance(item, tuple) and item[0] == 'analysis_failure':
                    fail_msg = item[1][1] if len(item[1]) > 1 else str(item[1])
                    self.progress_log.emit(f"Analysis Failure: {fail_msg}")
                    success = False
                else:
                    self.progress_log.emit(str(item))
    
        except Exception as e:
            raise e
    
        # Check for skipped commands
        if final_result.get('skipped'):
            success = False
    
        self.simulation_finished.emit(success, final_result)

    def _run_execution(self):
        start_total = time.time()
    
        # Important here: it is safer to create a RealFileSystem inside a thread
        real_fs = RealFileSystem(self.target_path)
        log_gen = run_patch(self.commands, real_fs, self.experimental_flags)
    
        failed_commands = []
    
        try:
            for i, (success, message, command) in enumerate(log_gen):
                if command:
                    self.command_result.emit(success, message, command)
                    if not success:
                        failed_commands.append((command, message))
        except Exception as e:
            raise e
    
        end_total = time.time()
        total_duration = end_total - start_total
    
        self.execution_finished.emit(failed_commands, total_duration)