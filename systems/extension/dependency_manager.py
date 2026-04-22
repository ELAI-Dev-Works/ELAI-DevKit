import os

class DependencyManager:
    """
    Handles dependency resolution, conflict checking, and requirements tracking.
    """
    def __init__(self, extensions_meta):
        self.extensions = extensions_meta

    def resolve_load_order(self):
        """
        Sorts extensions based on dependencies (topological sort).
        Returns: (ordered_list, extensions_dict)
        """
        sorted_list = []
        satisfied = set()
        
        # Filter enabled extensions
        active_exts = {k: v for k, v in self.extensions.items() if v.get('enabled', True)}
        
        # Check conflicts first
        self._check_conflicts(active_exts)

        # Create a map of dependencies
        deps_map = {name: set(meta.get('dependencies', [])) for name, meta in active_exts.items()}

        # Iteratively find extensions with no unsatisfied dependencies
        while len(sorted_list) < len(active_exts):
            resolved_this_round = []
            for name, deps in deps_map.items():
                if name in satisfied:
                    continue
                
                # Check if all dependencies are satisfied (and exist/enabled)
                # We filter deps to only those that are expected to be loaded by the system
                real_deps = [d for d in deps if d in self.extensions] # Check against all known exts
                
                if set(real_deps).issubset(satisfied):
                    resolved_this_round.append(name)

            if not resolved_this_round:
                # Circular dependency or missing dependency
                unresolved = {k: v for k, v in deps_map.items() if k not in satisfied}
                print(f"[Dependency] ERROR: Could not resolve dependencies. Unresolved: {unresolved}")
                # Disable unresolved extensions to allow the rest to load
                for name in unresolved:
                    if name in self.extensions:
                        print(f"[Dependency] Disabling '{name}' due to dependency issues.")
                        self.extensions[name]['enabled'] = False
                break

            for name in resolved_this_round:
                sorted_list.append(name)
                satisfied.add(name)

        return sorted_list

    def _check_conflicts(self, active_exts):
        """Disables extensions that conflict with others."""
        for name, meta in active_exts.items():
            conflicts = meta.get('conflicts', [])
            for conflict_name in conflicts:
                if conflict_name in active_exts:
                    print(f"[Dependency] CONFLICT DETECTED: '{name}' conflicts with '{conflict_name}'.")
                    print(f"[Dependency] Disabling '{name}' to maintain stability.")
                    self.extensions[name]['enabled'] = False
                    return # Stop checking this extension

    def get_python_requirements(self, ext_name):
        """
        Reads requirements.txt from the extension folder if it exists.
        Returns a list of requirement strings.
        """
        if ext_name not in self.extensions:
            return []
            
        path = self.extensions[ext_name]['path']
        req_path = os.path.join(path, "requirements.txt")
        
        if os.path.exists(req_path):
            try:
                with open(req_path, 'r', encoding='utf-8') as f:
                    return [line.strip() for line in f if line.strip() and not line.startswith('#')]
            except Exception as e:
                print(f"[Dependency] Error reading requirements for {ext_name}: {e}")
        return []