from .fs_handler import VirtualFileSystem
from .patcher import run_patch, _get_command_group_key
from .command_planner import plan_execution_order
from itertools import groupby

def simulate_patch_and_get_vfs(commands: list, root_path: str, experimental_flags=None, ignore_dirs: list = None):
    """
    Applies a patch to a Virtual File System and returns the resulting VFS state.
    This is used for the test run feature.
    """
    vfs = VirtualFileSystem(root_path, ignore_dirs=ignore_dirs, ignore_context='patcher')
    # The generator must be consumed for the patch to be applied.
    list(run_patch(commands, vfs, experimental_flags))
    return vfs


def plan_dynamic_patch(commands: list, root_path: str, experimental_flags=None, ignore_dirs: list = None, lang=None):
    """
    NEW: Performs a dynamic simulation to build a safe execution plan.
    It attempts to "rescue" commands that are valid in isolation but fail in batch.
    """
    if not lang:
        class MockLang:
            def get(self, key, **kwargs): return key.replace('_', ' ').title()
        lang = MockLang()

    if not commands:
        yield lang.get('simulation_no_commands')
        yield ('finished', {'plan': [], 'skipped': []})
        return

    # Helper to create hashable keys from command tuples by converting inner lists to tuples
    hashable_key = lambda cmd: (cmd[0], tuple(cmd[1]), cmd[2])
    
    # --- STAGE 1: GATHER DATA (INDIVIDUAL & BATCH RUNS) ---
    # Optimization: create VFS from disk only once
    initial_vfs = VirtualFileSystem(root_path, ignore_dirs=ignore_dirs)
    
    planned_commands = plan_execution_order(commands, root_path)
    edit_commands = [cmd for cmd in planned_commands if "EDIT_BATCH" in str(_get_command_group_key(cmd))]
    non_edit_commands = [cmd for cmd in planned_commands if "EDIT_BATCH" not in str(_get_command_group_key(cmd))]
    
    yield lang.get('simulation_stage1_start')
    # Create a base state by applying non-EDIT commands to the clone
    base_vfs = initial_vfs.clone()
    
    # Execute non-edit commands with logging
    stage1_passed = []
    stage1_failed = []
    
    for success, msg, cmd in run_patch(non_edit_commands, base_vfs, experimental_flags):
        status_str = lang.get('simulation_success') if success else lang.get('simulation_fail')
        cmd_name = cmd[0] if cmd else "UNKNOWN"
    
        # Format similar to execution log
        log_msg = f"[STAGE 1] {cmd_name}: {status_str}. {msg}"
        yield log_msg
    
        if cmd is not None:
            if success:
                stage1_passed.append(cmd)
            else:
                # If a base command fails (e.g. Security Violation), it's a critical failure for the plan
                stage1_failed.append((cmd, msg))
    
    yield lang.get('simulation_stage1_end')
    
    yield lang.get('simulation_stage2_start')
    # Pass 1: Individual check (uses base_vfs clones)
    pass1_results = {}
    for i, cmd in enumerate(edit_commands):
        yield lang.get('simulation_pass1_result').format(i + 1, len(edit_commands), cmd[0], "...")
        success, msg, _ = next(run_patch([cmd], base_vfs.clone(), experimental_flags))
        pass1_results[hashable_key(cmd)] = (success, msg, cmd)
        status_str = lang.get('simulation_success') if success else lang.get('simulation_fail')
        yield lang.get('simulation_pass1_result').format(i + 1, len(edit_commands), cmd[0], f"{status_str}. {msg}")
    
    yield lang.get('simulation_stage3_start')
    # Pass 2: Batch check (uses a clone of the original VFS)
    pass2_vfs = initial_vfs.clone()
    pass2_gen = run_patch(planned_commands, pass2_vfs, experimental_flags)
    pass2_results = {}
    pass2_edit_results_count = 0
    for success, msg, cmd in pass2_gen:
        if "EDIT_BATCH" in str(_get_command_group_key(cmd)):
            pass2_edit_results_count += 1
            pass2_results[hashable_key(cmd)] = (success, msg)
            status_str = lang.get('simulation_success') if success else lang.get('simulation_fail')
            yield lang.get('simulation_pass2_result').format(pass2_edit_results_count, len(edit_commands), cmd[0], f"{status_str}. {msg}")
        elif cmd: # non-edit commands
            pass2_results[hashable_key(cmd)] = (success, msg)
    
    
    # --- STAGE 2: DYNAMIC PLANNING & RESCUE ---
    yield "\n--- DYNAMIC ANALYSIS & EXECUTION PLANNING ---"
    final_plan = list(stage1_passed) # Only include successful commands from Stage 1
    skipped_commands = list(stage1_failed) # Preserve failures from Stage 1
    analysis_vfs = base_vfs.clone()
    
    for i, command in enumerate(edit_commands):
        cmd_tuple = hashable_key(command)
        p1_success, p1_msg, _ = pass1_results.get(cmd_tuple, (False, "Not found in Pass 1", None))
        p2_success, p2_msg = pass2_results.get(cmd_tuple, (False, "Not found in Pass 2"))
    
        if p1_success and p2_success: # GREEN
            yield f"[PLAN] Command #{i+1} is GREEN. Adding to plan."
            final_plan.append(command)
            list(run_patch([command], analysis_vfs, experimental_flags))
        elif p1_success and not p2_success: # YELLOW (CONFLICT) - RESCUE ATTEMPT
            yield f"[PLAN] Command #{i+1} is a CONFLICT. Attempting rescue..."
    
            temp_vfs = analysis_vfs.clone()
            list(run_patch([command], temp_vfs, experimental_flags))
    
            # Re-simulate the ENTIRE remaining chain of commands
            remaining_commands = edit_commands[i+1:]
            is_safe = True
            if remaining_commands:
                remaining_results = list(run_patch(remaining_commands, temp_vfs, experimental_flags))
                if any(not res[0] for res in remaining_results):
                    is_safe = False
                    failed_at_index = next((idx for idx, res in enumerate(remaining_results) if not res[0]), -1)
                    if failed_at_index != -1:
                        original_index = edit_commands.index(remaining_commands[failed_at_index])
                        yield f"  -> Rescue FAILED. Applying this command would break a subsequent command (approx. Command #{original_index + 1})."
    
            if is_safe:
                yield f"  -> Rescue SUCCESSFUL. Command added to plan."
                final_plan.append(command)
                analysis_vfs = temp_vfs
            else:
                skipped_commands.append((command, p2_msg))
        else: # RED or YELLOW (DEPENDENCY) - in Pass 2 they are treated the same
            # If it succeeded in batch, it means its dependency was met
            if p2_success:
                 yield f"[PLAN] Command #{i+1} is a DEPENDENCY. Adding to plan."
                 final_plan.append(command)
                 list(run_patch([command], analysis_vfs, experimental_flags))
            else: # RED
                yield f"[PLAN] Command #{i+1} is a critical ERROR. Skipping."
                skipped_commands.append((command, p1_msg))
    
    yield "\n[FINAL] Dynamic planning complete."
    if not skipped_commands:
        yield lang.get('simulation_final_ok')
    else:
        yield lang.get('simulation_final_warn')
        for cmd, reason in skipped_commands:
            yield ('analysis_failure', (cmd, f"[SKIPPED] {reason}"))
    
    yield ('finished', {'plan': final_plan, 'skipped': skipped_commands})