#!/usr/bin/env python3
"""Elimina los bloques elif de acciones migradas de stack_manager.py.

Lee la lista de acciones migradas y elimina cada bloque elif
correspondiente de _ejecutar_accion, manteniendo la cadena if/elif intacta.
"""

import os
import re

ORM_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STACK_MANAGER = os.path.join(ORM_ROOT, "systems", "stack_manager.py")

# Acciones que ya fueron migradas al registry
MIGRATED = {
    "show_message",
    "replace_sprite", "cambiar_fondo",
    "remove_escamas", "bloquear_mandos", "cambiar_skin", "avanzar", "despertar",
    "clear_flag",
    "mostrar_boss",
    "fin_demo",
    "set_bgm_volume", "set_sfx_volume", "set_volume",
    "set_resolution",
    "open_save_menu", "open_load_menu", "close_shop", "close_save_menu",
    "mostrar_personaje", "ocultar_personaje", "ocultar_todos_personajes",
    "restock_shop", "add_shop_stock", "modify_shop_price",
    "increment_contador", "set_contador",
    # Also migrated in earlier sprints
    "play_bgm", "stop_bgm", "play_sfx",
    "set_flag", "add_flag",
    "give_item", "remove_item",
}

# Acciones internas que ya fueron movidas a _ejecutar_accion_interna
INTERNAL = {"_arbol_choice", "accion_botton", "esperar", "bloquear_eventos"}

# Alias de diálogos (ya consolidados en un solo bloque)
DIALOG_ALIASES = {"start_dialog", "iniciar_dialogo"}


def find_method_body(source):
    """Encuentra el inicio y fin de _ejecutar_accion."""
    start = source.find("def _ejecutar_accion(")
    if start == -1:
        raise RuntimeError("No se encontro _ejecutar_accion")

    # Find end: next def at indent 4
    lines = source[start:].split("\n")
    end_offset = start
    for i, line in enumerate(lines):
        if i == 0:
            continue
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if stripped.startswith("def ") and indent == 4:
            end_offset = start + sum(len(l) + 1 for l in lines[:i])
            break

    return start, end_offset


def extract_action_ids_from_line(line):
    """Extrae action IDs de una línea if/elif."""
    m = re.match(r'\s*(?:if|elif)\s+accion\s*==\s*"(\w+)"', line)
    if m:
        return [m.group(1)]

    m = re.match(r'\s*elif\s+accion\s+in\s*\(', line)
    if m:
        return re.findall(r'"(\w+)"', line)

    return []


def main():
    with open(STACK_MANAGER, encoding="utf-8") as f:
        source = f.read()

    method_start, method_end = find_method_body(source)
    method_body = source[method_start:method_end]
    lines = method_body.split("\n")

    # Find all elif blocks and their line ranges
    blocks_to_remove = []
    i = 0
    while i < len(lines):
        line = lines[i]
        action_ids = extract_action_ids_from_line(line)

        if action_ids:
            # Check if ALL action IDs in this block are migrated
            all_migrated = all(
                aid in MIGRATED or aid in INTERNAL or aid in DIALOG_ALIASES
                for aid in action_ids
            )

            if all_migrated:
                # Find the end of this block (next elif/def at same indent)
                block_start = i
                block_end = i + 1
                while block_end < len(lines):
                    next_line = lines[block_end]
                    next_stripped = next_line.lstrip()
                    next_indent = len(next_line) - len(next_stripped)

                    # Block ends at next elif/def at indent 8 (same level)
                    if next_indent == 8 and (
                        next_stripped.startswith("elif ") or
                        next_stripped.startswith("def ")
                    ):
                        break
                    # Also check for "elif accion in" at indent 8
                    if next_indent == 8 and next_stripped.startswith("elif"):
                        break
                    block_end += 1

                blocks_to_remove.append((block_start, block_end, action_ids))
                i = block_end
                continue

        i += 1

    # Remove blocks in reverse order to preserve line numbers
    for block_start, block_end, action_ids in reversed(blocks_to_remove):
        del lines[block_start:block_end]

    # Remove consecutive blank lines (max 1)
    cleaned = []
    prev_blank = False
    for line in lines:
        is_blank = not line.strip()
        if is_blank and prev_blank:
            continue
        cleaned.append(line)
        prev_blank = is_blank

    new_body = "\n".join(cleaned)
    new_source = source[:method_start] + new_body + source[method_end:]

    with open(STACK_MANAGER, "w", encoding="utf-8") as f:
        f.write(new_source)

    total_removed = sum(end - start for start, end, _ in blocks_to_remove)
    print(f"Bloques eliminados: {len(blocks_to_remove)}")
    print(f"Líneas eliminadas: {total_removed}")
    print(f"Acciones eliminadas: {', '.join(sorted(MIGRATED | INTERNAL | DIALOG_ALIASES))}")


if __name__ == "__main__":
    main()
