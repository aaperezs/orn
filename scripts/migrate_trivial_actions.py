#!/usr/bin/env python3
"""Genera archivos de GameAction para las 37 acciones triviales del elif legacy.

Lee stack_manager.py, extrae el código de cada bloque elif identificado
como trivial, y genera un archivo .py en orm/systems/actions/ con la
clase equivalente que usa EventContext (ctx.state en vez de estado).
"""

import os
import re
import sys
import textwrap

ORM_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STACK_MANAGER = os.path.join(ORM_ROOT, "systems", "stack_manager.py")
ACTIONS_DIR = os.path.join(ORM_ROOT, "systems", "actions")

# Acciones triviales agrupadas por archivo de destino.
# Cada tupla: (nombre_archivo, [(action_id, class_name), ...])
TRIVIAL_ACTIONS = [
    ("display.py", [
        ("replace_sprite", "ReplaceSprite"),
        # remove_sprite: usa self._remover_entidades_en -> queda en elif
        ("cambiar_fondo", "CambiarFondo"),
    ]),
    ("player.py", [
        ("remove_escamas", "RemoveEscamas"),
        # give_moneda: usa self._moneda_dar -> queda en elif
        # remove_moneda: usa self._moneda_quitar -> queda en elif
        ("bloquear_mandos", "BloquearMandos"),
        ("cambiar_skin", "CambiarSkin"),
        ("avanzar", "Avanzar"),
        # auto_caminar: usa self._auto_direccion -> queda en elif
        ("despertar", "Despertar"),
    ]),
    # close_dialog: usa self._bloqueo_por -> queda en elif
    ("flags_extra.py", [
        ("clear_flag", "ClearFlag"),
    ]),
    ("boss.py", [
        ("mostrar_boss", "MostrarBoss"),
    ]),
    ("game_flow.py", [
        ("fin_demo", "FinDemo"),
    ]),
    ("audio_settings.py", [
        ("set_bgm_volume", "SetBgmVolume"),
        ("set_sfx_volume", "SetSfxVolume"),
        ("set_volume", "SetVolume"),
    ]),
    ("display_settings.py", [
        ("set_resolution", "SetResolution"),
    ]),
    ("ui.py", [
        ("open_save_menu", "OpenSaveMenu"),
        ("open_load_menu", "OpenLoadMenu"),
        ("close_shop", "CloseShop"),
        ("close_save_menu", "CloseSaveMenu"),
        ("mostrar_personaje", "MostrarPersonaje"),
        ("ocultar_personaje", "OcultarPersonaje"),
        ("ocultar_todos_personajes", "OcultarTodosPersonajes"),
    ]),
    ("shop_extras.py", [
        ("restock_shop", "RestockShop"),
        ("add_shop_stock", "AddShopStock"),
        ("modify_shop_price", "ModifyShopPrice"),
    ]),
    ("counters.py", [
        ("increment_contador", "IncrementContador"),
        ("set_contador", "SetContador"),
    ]),
]

# Mapeo de nombres de variables: en el elif se usa "estado" como nombre local.
# En GameAction.execute se debe usar ctx.state.
VAR_MAP = {
    "estado": "ctx.state",
}

# Patrones de import que se deben mover al top-level del archivo generado.
# Se buscan imports inline dentro de los bloques.
IMPORT_RE = re.compile(r"^\s+from\s+(\S+)\s+import\s+(.+)$", re.MULTILINE)


def read_stack_manager():
    with open(STACK_MANAGER, encoding="utf-8") as f:
        return f.read()


def extract_elif_blocks(source):
    """Extrae todos los bloques elif/if de _ejecutar_accion como dict[action_id -> code].

    Returns dict[str, str] mapping action_id -> raw code block (indented).
    """
    blocks = {}
    # Find _ejecutar_accion method
    method_start = source.find("def _ejecutar_accion(")
    if method_start == -1:
        raise RuntimeError("No se encontro _ejecutar_accion")

    body_start = source.find("\n", method_start)
    lines = source[body_start:].split("\n")
    current_action = None
    current_lines = []
    pending_elif_in_ids = []  # IDs from a pending "elif accion in (...)" multi-line

    for line in lines:
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        # Detect def at method level (4 spaces = class method)
        if stripped.startswith("def ") and indent == 4:
            if current_action and current_lines:
                blocks[current_action] = "\n".join(current_lines)
            break

        # Detect if/elif action == "single_id"
        m_if = re.match(r'\s*if\s+accion\s*==\s*"(\w+)"', line)
        m_elif = re.match(r'\s*elif\s+accion\s*==\s*"(\w+)"', line)

        if m_if or m_elif:
            if current_action and current_lines:
                blocks[current_action] = "\n".join(current_lines)
            current_action = (m_if or m_elif).group(1)
            current_lines = [line]
            pending_elif_in_ids = []
            continue

        # Detect elif accion in ( possibly multi-line
        m_elif_in = re.match(r'\s*elif\s+accion\s+in\s*\(', line)
        if m_elif_in:
            if current_action and current_lines:
                blocks[current_action] = "\n".join(current_lines)
            # Try to extract all IDs from this line (handles single-line tuple)
            ids = re.findall(r'"(\w+)"', line)
            if ids:
                # Check if tuple is complete on this line
                if ")" in line:
                    # Single-line tuple: skip this block entirely (internal actions)
                    current_action = None
                    current_lines = []
                    pending_elif_in_ids = []
                else:
                    # Multi-line tuple: collect IDs from subsequent lines
                    current_action = None
                    current_lines = []
                    pending_elif_in_ids = ids
            else:
                current_action = None
                current_lines = []
                pending_elif_in_ids = []
            continue

        # If we have pending elif_in IDs and this line contains more IDs
        if pending_elif_in_ids and '"' in line:
            more_ids = re.findall(r'"(\w+)"', line)
            pending_elif_in_ids.extend(more_ids)
            if ")" in line:
                # Tuple complete - these are internal actions, skip them
                current_action = None
                current_lines = []
                pending_elif_in_ids = []
            continue

        # If we have a current action, collect lines
        if current_action:
            current_lines.append(line)

    return blocks


def transform_block(block_code, action_id):
    """Transforma un bloque elif a código de execute() method.

    1. Quita la primera línea (if/elif accion == ...)
    2. Detecta la indentación base y la remueve
    3. Reemplaza 'estado' por 'ctx.state'
    4. Detecta y extrae imports inline
    """
    lines = block_code.split("\n")
    if not lines:
        return "", []

    # Skip first line (the if/elif line)
    code_lines = lines[1:]

    # Remove trailing empty lines
    while code_lines and not code_lines[-1].strip():
        code_lines.pop()

    if not code_lines:
        return "", []

    # Detect minimum indentation of non-empty lines
    min_indent = None
    for line in code_lines:
        stripped = line.lstrip()
        if stripped:
            indent = len(line) - len(stripped)
            if min_indent is None or indent < min_indent:
                min_indent = indent

    if min_indent is None:
        min_indent = 0

    # Dedent by min_indent
    dedented = []
    for line in code_lines:
        if line.strip() == "":
            dedented.append("")
        elif len(line) >= min_indent:
            dedented.append(line[min_indent:])
        else:
            dedented.append(line.lstrip())

    # Extract inline imports
    imports = []
    import_indices = []
    for i, line in enumerate(dedented):
        m = re.match(r'\s*from\s+(\S+)\s+import\s+(.+)', line)
        if m:
            module = m.group(1)
            names = m.group(2).strip()
            imports.append(f"from {module} import {names}")
            import_indices.append(i)

    # Remove import lines from dedented (reverse order)
    for i in reversed(import_indices):
        dedented.pop(i)

    code = "\n".join(dedented)

    # Replace 'estado' with 'ctx.state' (not inside strings)
    code = re.sub(r'\bestado\b', 'ctx.state', code)

    return code.strip(), imports


def generate_class(action_id, class_name, code, imports):
    """Genera el código de una clase GameAction."""
    # Determine return value: True if block has 'return True', else False
    # But NOT if it's inside a nested if (e.g. "if ...: return True")
    returns_true = False
    for line in code.split("\n"):
        stripped = line.strip()
        if stripped == "return True":
            returns_true = True
            break

    # Check if code uses x, y, or z variables
    uses_xyz = bool(re.search(r'\b[xyz]\b', code))

    # Build the class
    parts = []
    parts.append(f'@register_action("{action_id}")')
    parts.append(f"class {class_name}(GameAction):")
    parts.append("    def execute(self, ctx, params):")

    # Unpack position if needed
    if uses_xyz:
        parts.append("        x, y, z = ctx.position")

    # Indent code lines
    code_lines = code.split("\n")
    for line in code_lines:
        if line.strip():
            parts.append(f"        {line}")
        else:
            parts.append("")

    if returns_true:
        parts.append("        return True")
    else:
        parts.append("        return False")

    return "\n".join(parts)


def generate_file(filename, actions_data, all_imports):
    """Genera un archivo .py completo con todas las acciones del grupo."""
    imports_str = "\n".join(sorted(set(all_imports)))
    classes_str = "\n\n\n".join(actions_data)

    return f'''"""Acciones migradas automaticamente desde stack_manager._ejecutar_accion.

NO EDITAR MANUALMENTE - generado por scripts/migrate_trivial_actions.py
"""

from systems.action_registry import GameAction, register_action
{imports_str}

TAMANO_CELDA = 32  # from configs.constants

{classes_str}
'''


def main():
    print("=== Migrador de acciones triviales ===")
    print(f"Stack manager: {STACK_MANAGER}")
    print(f"Actions dir:   {ACTIONS_DIR}")
    print()

    source = read_stack_manager()
    blocks = extract_elif_blocks(source)
    print(f"Bloques elif encontrados: {len(blocks)}")
    print()

    # Build lookup of all trivial action ids
    all_trivial_ids = set()
    for filename, actions in TRIVIAL_ACTIONS:
        for action_id, class_name in actions:
            all_trivial_ids.add(action_id)

    # Verify all trivial actions exist in blocks
    missing = all_trivial_ids - set(blocks.keys())
    if missing:
        print(f"ADVERTENCIA: Acciones no encontradas en elif: {missing}")
        print("Estas acciones se omitiran.")
        print()

    generated = 0
    skipped = 0

    for filename, actions in TRIVIAL_ACTIONS:
        classes_data = []
        file_imports = []

        for action_id, class_name in actions:
            if action_id not in blocks:
                print(f"  SKIP {action_id}: no encontrado en elif")
                skipped += 1
                continue

            block = blocks[action_id]
            code, imports = transform_block(block, action_id)

            if not code.strip():
                print(f"  SKIP {action_id}: bloque vacio")
                skipped += 1
                continue

            # Check for self. references (should not exist in trivial actions)
            if "self." in code:
                print(f"  WARN {action_id}: contiene 'self.' - revisar manualmente")
                # Don't skip, but flag it

            class_code = generate_class(action_id, class_name, code, imports)
            classes_data.append(class_code)
            file_imports.extend(imports)
            generated += 1
            print(f"  OK   {action_id} -> {class_name}")

        if classes_data:
            filepath = os.path.join(ACTIONS_DIR, filename)
            content = generate_file(filename, classes_data, file_imports)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  -> Escrito: {filename} ({len(classes_data)} acciones)")

    print()
    print(f"Total generados: {generated}")
    print(f"Total omitidos:  {skipped}")
    print()
    print("Proximo paso: eliminar los bloques elif de stack_manager.py")


if __name__ == "__main__":
    main()
