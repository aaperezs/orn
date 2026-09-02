"""Drift Killer: valida que el contrato blueprint<->runtime esté alineado.

Compara:
  - editor/widgets/event_constants.py   -> ACTION_TYPES, CONDITION_TYPES
  - orm/systems/stack_manager.py        -> elif accion == "..." en _ejecutar_accion
  - orm/systems/action_registry.py      -> @register_action("...")

Si hay IDs en el runtime que no están en el editor (o viceversa), imprime
una tabla comparativa y termina con SystemExit(1). Si no hay drift, exit 0.

Uso:
  python scripts/validate_event_contract.py
"""

from __future__ import annotations

import ast
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

EDITOR_CONSTANTS = os.path.join(REPO_ROOT, "editor", "widgets", "event_constants.py")
STACK_MANAGER = os.path.join(REPO_ROOT, "orm", "systems", "stack_manager.py")
ACTION_REGISTRY = os.path.join(REPO_ROOT, "orm", "systems", "action_registry.py")

# Acciones internas del runtime (no son blueprints de usuario): se ignoran.
RUNTIME_INTERNAL = {
    "_arbol_choice",
    "accion_botton",
    "comando_automatico",
    "esperar",
    "bloquear_eventos",
    "auto_caminar",
    "trigger_restock",
}

# Alias legacy que el runtime soporta pero el editor NO debe mostrar
# (son redundantes con la acción canónica).
RUNTIME_ALIASES = {
    "start_dialog",      # alias de start_dialogue
    "iniciar_dialogo",   # alias de start_dialogue
}


# ── Extracción desde el editor ─────────────────────────────

def _extract_list_from_module(path: str, name: str) -> list[str]:
    """Lee una lista literal de strings definida a nivel de módulo."""
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    if isinstance(node.value, ast.List):
                        out = []
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                out.append(elt.value)
                        return out
    return []


def get_editor_actions() -> list[str]:
    return _extract_list_from_module(EDITOR_CONSTANTS, "ACTION_TYPES")


def get_editor_conditions() -> list[str]:
    return _extract_list_from_module(EDITOR_CONSTANTS, "CONDITION_TYPES")


# ── Extracción desde el runtime ────────────────────────────

def _extract_runtime_strings(path: str, var: str) -> list[str]:
    """Extrae todos los `var == "..."` de un archivo (ramas de dispatch)."""
    with open(path, encoding="utf-8") as f:
        src = f.read()
    pattern = re.compile(rf'{var}\s*==\s*"([^"]+)"')
    return sorted(set(pattern.findall(src)))


def get_registry_actions() -> list[str]:
    """Extrae IDs de @register_action del action_registry."""
    with open(ACTION_REGISTRY, encoding="utf-8") as f:
        src = f.read()
    # Also check action files in orm/systems/actions/ and subdirectories
    actions_dir = os.path.join(REPO_ROOT, "orm", "systems", "actions")
    all_src = src
    if os.path.isdir(actions_dir):
        for root, dirs, files in os.walk(actions_dir):
            for fname in files:
                if fname.endswith(".py") and fname != "__init__.py":
                    fpath = os.path.join(root, fname)
                    with open(fpath, encoding="utf-8") as f:
                        all_src += "\n" + f.read()
    pattern = re.compile(r'@register_action\("([^"]+)"\)')
    return sorted(set(pattern.findall(all_src)))


def get_runtime_actions() -> list[str]:
    """Combina acciones del registry + elif chain, excluyendo internas y aliases."""
    registry = set(get_registry_actions())
    elif_actions = set(_extract_runtime_strings(STACK_MANAGER, "accion"))
    # Also extract from "elif accion in (...)" blocks
    with open(STACK_MANAGER, encoding="utf-8") as f:
        src = f.read()
    for match in re.finditer(r'elif\s+accion\s+in\s*\(([^)]+)\)', src):
        ids = re.findall(r'"(\w+)"', match.group(1))
        elif_actions.update(ids)

    all_runtime = registry | elif_actions
    # Remove internals, aliases, and pending complex actions
    all_runtime -= RUNTIME_INTERNAL
    all_runtime -= RUNTIME_ALIASES
    return sorted(all_runtime)


def get_runtime_conditions() -> list[str]:
    return _extract_runtime_strings(STACK_MANAGER, "ct")


# ── Reporte ────────────────────────────────────────────────

def _print_table(title: str, only_runtime: list[str], only_editor: list[str]) -> None:
    if only_runtime:
        print(f"\n  Solo en RUNTIME ({len(only_runtime)}):")
        for a in only_runtime:
            print(f"    [RUNTIME] {a}")
    if only_editor:
        print(f"\n  Solo en EDITOR ({len(only_editor)}):")
        for a in only_editor:
            print(f"    [EDITOR]  {a}")


def _validate(kind: str, editor_ids: list[str], runtime_ids: list[str]) -> int:
    only_runtime = sorted(set(runtime_ids) - set(editor_ids))
    only_editor = sorted(set(editor_ids) - set(runtime_ids))
    print(f"=== {kind}: editor={len(editor_ids)} runtime={len(runtime_ids)} ===")
    _print_table(kind, only_runtime, only_editor)
    print()
    return len(only_runtime) + len(only_editor)


def main() -> int:
    editor_actions = get_editor_actions()
    runtime_actions = get_runtime_actions()
    editor_conds = get_editor_conditions()
    runtime_conds = get_runtime_conditions()

    n_actions = _validate("ACCIONES", editor_actions, runtime_actions)
    n_conds = _validate("CONDICIONES", editor_conds, runtime_conds)

    total = n_actions + n_conds
    if total == 0:
        print("[OK] Contrato alineado: sin drift entre editor y runtime.")
        return 0
    print(f"[DRIFT] {total} discrepancias detectadas. Corregir antes de continuar.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
