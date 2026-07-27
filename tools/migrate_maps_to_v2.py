"""
Script one-time: convierte todos los mapas .txt (v1, char-based) a .json (v2, sprite-id-based).
Uso: python tools/migrate_maps_to_v2.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from levels.level_manager import RUTA_MAPAS

from editor.sprite_registry import CHAR_TO_SPRITE

LAYER_SUFFIX = {0: "", -1: "_z-1", -2: "_z-2", 1: "_z1"}


def text_to_grid(text):
    lines = [l.rstrip() for l in text.split("\n") if l.strip() and not l.startswith("# ")]
    grid = {}
    for y, line in enumerate(lines):
        for x, ch in enumerate(line):
            sid = CHAR_TO_SPRITE.get(ch)
            if sid:
                grid[(x, y)] = sid
    return grid, len(lines), max(len(l) for l in lines) if lines else 0


def grid_to_json(grid, ancho, alto):
    raw = {}
    for (gx, gy), sid in grid.items():
        raw[f"{gx},{gy}"] = sid
    return json.dumps({"version": 2, "ancho": ancho, "alto": alto, "grid": raw}, indent=2, ensure_ascii=False)


def extract_meta(text, map_id):
    meta = {"gates": [], "cofres": []}
    for line in text.split("\n"):
        line = line.strip()
        if not line.startswith("# ") or "=" not in line:
            continue
        kv = line[1:].strip()
        key, value = kv.split("=", 1)
        key, value = key.strip(), value.strip()
        parts = key.split(".")
        if parts[0] == "gate" and len(parts) >= 3:
            gate_char = parts[1]
            field = parts[2]
            # Find position for this gate char in grid
            meta["gates"].append({"char": gate_char, field: value})
        elif parts[0] == "cofre" and len(parts) >= 3:
            cofre_char = parts[1]
            field = parts[2]
            meta["cofres"].append({"char": cofre_char, field: value})
        elif parts[0] == "arena":
            meta["arena"] = value
    return meta


def migrate_map(map_id):
    converted = 0
    meta_accum = {"gates": [], "cofres": []}

    for z, suffix in LAYER_SUFFIX.items():
        txt_path = os.path.join(RUTA_MAPAS, f"{map_id}{suffix}.txt")
        json_path = os.path.join(RUTA_MAPAS, f"{map_id}{suffix}.json")

        if not os.path.exists(txt_path):
            continue

        with open(txt_path, "r", encoding="utf-8") as f:
            text = f.read()

        grid, alto, ancho = text_to_grid(text)
        if not grid:
            continue

        json_data = grid_to_json(grid, ancho, alto)
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(json_data)

        meta = extract_meta(text, map_id)
        for g in meta.get("gates", []):
            meta_accum["gates"].append(g)
        for c in meta.get("cofres", []):
            meta_accum["cofres"].append(c)
        if "arena" in meta:
            meta_accum["arena"] = meta["arena"]

        converted += 1
        print(f"  Capa Z={z}: {txt_path} -> {json_path}")

    # Write meta file
    meta_path = os.path.join(RUTA_MAPAS, f"{map_id}_meta.json")
    if meta_accum["gates"] or meta_accum["cofres"] or "arena" in meta_accum:
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta_accum, f, indent=2, ensure_ascii=False)
        print(f"  Meta: {meta_path}")

    return converted


def main():
    print("Migrando mapas de v1 (char) a v2 (sprite-id)...")
    count = 0
    for archivo in sorted(os.listdir(RUTA_MAPAS)):
        if not archivo.endswith(".txt"):
            continue
        map_id = archivo[:-4]
        if any(map_id.endswith(sfx) for sfx in ["_z1", "_z-1", "_z-2"]):
            continue
        # Avoid re-migrating
        json_check = os.path.join(RUTA_MAPAS, f"{map_id}.json")
        if os.path.exists(json_check):
            print(f"  Saltando {map_id} (ya existe .json)")
            continue
        print(f"\n{map_id}:")
        c = migrate_map(map_id)
        if c:
            count += 1

    print(f"\nMigrados {count} mapas a formato v2.")


if __name__ == "__main__":
    main()
