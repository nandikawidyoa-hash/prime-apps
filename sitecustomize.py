"""
Global site customization for PRIME APPS
Ensures reliable module resolution across virtual 9p filesystem mounts.
"""
import sys
import os
import importlib.util
import importlib.abc

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))

class DirectWorkspaceFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        parts = fullname.split(".")
        rel_path = os.path.join(WORKSPACE_DIR, *parts)
        init_path = os.path.join(rel_path, "__init__.py")
        if os.path.isfile(init_path):
            spec = importlib.util.spec_from_file_location(fullname, init_path, submodule_search_locations=[rel_path])
            return spec
        file_path = rel_path + ".py"
        if os.path.isfile(file_path):
            spec = importlib.util.spec_from_file_location(fullname, file_path)
            return spec
        return None

if DirectWorkspaceFinder not in [type(f) for f in sys.meta_path]:
    sys.meta_path.insert(0, DirectWorkspaceFinder())
