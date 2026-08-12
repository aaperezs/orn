import os


def _project_root():
    try:
        from editor.project import get_current_project
        p = get_current_project()
        if p is not None:
            return p.root
    except Exception:
        pass
    return None


def runtime_root():
    """Raiz del proyecto actual; si no hay proyecto, la raiz del runtime (orm)."""
    root = _project_root()
    if root:
        return root
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def data_dir(*parts):
    return os.path.join(runtime_root(), "data", *parts)


def assets_dir(*parts):
    return os.path.join(runtime_root(), "assets", *parts)


def levels_dir(*parts):
    return os.path.join(runtime_root(), "levels", *parts)
