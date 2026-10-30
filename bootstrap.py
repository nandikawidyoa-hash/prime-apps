"""
Bootstrap module resolver for PRIME APPS webstore.
Ensures seamless import resolution on 9p mounts across packages and namespaces.
"""
import sys
import os
import importlib.util
import importlib.machinery
import importlib.abc

WORKSPACE_DIR = os.path.abspath(os.path.dirname(__file__) if "__file__" in globals() else os.getcwd())

class DirectWorkspaceFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        parts = fullname.split(".")
        rel_path = os.path.join(WORKSPACE_DIR, *parts)
        init_path = os.path.join(rel_path, "__init__.py")
        if os.path.isfile(init_path):
            return importlib.util.spec_from_file_location(fullname, init_path, submodule_search_locations=[rel_path])
        if os.path.isdir(rel_path):
            spec = importlib.machinery.ModuleSpec(fullname, None, is_package=True)
            spec.submodule_search_locations = [rel_path]
            return spec
        file_path = rel_path + ".py"
        if os.path.isfile(file_path):
            return importlib.util.spec_from_file_location(fullname, file_path)
        return None

# Ensure it is at the front of sys.meta_path
sys.meta_path = [f for f in sys.meta_path if not isinstance(f, DirectWorkspaceFinder)]
sys.meta_path.insert(0, DirectWorkspaceFinder())
