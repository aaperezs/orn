# Backlog: Configuración Gráfica por Proyecto (Cururo Editor)

## Objetivo
Permitir que cada proyecto en Cururo Editor defina su propia configuración gráfica (tile size, resolución, pixel art scale, tilesets) al crearlo, almacenada en `cururo.json` y usada tanto por el editor como por el runtime.

---

## Schema `cururo.json`

```json
{
  "graphics": {
    "tile_size": 20,
    "resolution": [800, 600],
    "pixel_art_scale": 1,
    "tileset": null
  }
}
```

- `tile_size`: 16 / 20 / 24 / 32 píxeles por celda del grid
- `resolution`: [ancho, alto] en píxeles lógicos (múltiplo de tile_size)
- `pixel_art_scale`: 1 = nativo, 2 = doble (640×360 lógico → 1280×720 ventana)
- `tileset`: ruta a tileset PNG o `null` si usa sprites individuales

---

## Fases

### Fase 0 — Proyectos Existentes (ORM)

Agregar `graphics` a `orm/cururo.json`:

```json
{
  "graphics": {
    "tile_size": 20,
    "resolution": [800, 600],
    "pixel_art_scale": 1,
    "tileset": null
  }
}
```

ORM conserva su `configs/constants.py` hardcodeado. El editor ya sabe la config del proyecto.
Fallback si no existe `graphics`: asumir 20×20 / 800×600 / scale 1.

**Archivos:** `orm/cururo.json`, `editor/project.py`

---

### Fase 1 — Editor: Propiedades del Proyecto

`editor/project.py` → `Project` expone:

```python
@property
def tile_size(self):
    return self._manifest.get("graphics", {}).get("tile_size", 20)

@property
def resolution(self):
    return tuple(self._manifest.get("graphics", {}).get("resolution", [800, 600]))

@property
def pixel_art_scale(self):
    return self._manifest.get("graphics", {}).get("pixel_art_scale", 1)

@property
def tileset(self):
    return self._manifest.get("graphics", {}).get("tileset", None)
```

`create_project()` recibe `graphics_config` y lo escribe en `cururo.json`.

**Archivos:** `editor/project.py`

---

### Fase 2 — Editor: Diálogo de Nuevo Proyecto

`editor/project_dialog.py` → estado `STATE_NEW` agrega:

| Campo | Widget | Notas |
|---|---|---|
| Tile size | Dropdown: 16 / 20 / 24 / 32 | Al cambiar, recalcula resoluciones sugeridas |
| Resolución | Dropdown pre-calculado | Múltiplo de tile_size |
| Pixel art scale | Dropdown: 1×, 2×, 3× | Escala la ventana, no el grid |
| Tileset | Checkbox + file picker | Si activo, carga PNG y lo divide en tiles |

Resoluciones sugeridas por tile size:

| Tile | Resoluciones |
|---|---|
| 16 | 640×480, 800×600, 960×720 |
| 20 | 800×600, 960×720 |
| 24 | 960×720, 1200×900 |
| 32 | 960×720, 1280×960 |

**Archivos:** `editor/project_dialog.py`

---

### Fase 3 — Editor: Tile Size Dinámico

El editor deja de importar `TAMANO_CELDA` como constante global y usa `project.tile_size`:

| Archivo | Cambio |
|---|---|
| `editor/map_editor.py:_tile_size()` | `ts = int(project.tile_size * self._zoom)` |
| `editor/map_editor.py:_screen_to_grid()` | Usa `project.tile_size` |
| `editor/map_editor.py` (carga legacy) | Usa `project.tile_size` para convertir píxeles a grid |
| `editor/sprite_editor.py` | `TILE_W = TILE_H = project.tile_size` |
| `editor/sprite_editor.py:_new_sprite(), _load_sprite(), _save_multi_tiles(), _set_multi_size()` | Usan `project.tile_size` |
| `editor/event_editor.py` | Minimapa usa `project.tile_size` |

**Archivos:** `editor/map_editor.py`, `editor/sprite_editor.py`, `editor/event_editor.py`

---

### Fase 4 — Editor: Soporte de Tilesets

Un tileset es un PNG de N×M tiles (ej: 320×320, 10×10 tiles de 32×32).
El editor lo carga, lo divide en tiles según `tile_size`, y el mapa guarda índices en vez de sprite_ids.

| Archivo | Cambio |
|---|---|
| `editor/tileset.py` | **Nuevo** — carga PNG, divide en tiles, maneja índices |
| `editor/map_editor.py` | Si `project.tileset`, pinta por índice en vez de `sprite_id` |
| `editor/sprite_editor.py` | Si tileset activo, edita tile individual del tileset |
| `editor/behaviors.py` | Elementos referencian `tileset_idx` o `sprite_id` según modo |
| `data/elementos.json` | Campo `tileset_idx` opcional |

Pueden convivir tileset para el mapa base + sprites individuales para entidades.

---

### Fase 5 — Template: Generación Dinámica

La template `empty_rpg` genera código que lee de `cururo.json` en runtime:

| Archivo | Contenido |
|---|---|
| `configs/constants.py` | **Nuevo** — lee `graphics` de `cururo.json`, exporta `ANCHO`, `ALTO`, `TAMANO_CELDA`, `PIXEL_ART_SCALE` |
| `main.py` | `display.set_mode((ANCHO * PIXEL_ART_SCALE, ALTO * PIXEL_ART_SCALE))` y escala internamente |
| `camera.py` | Usa `ANCHO, ALTO` para centrado/clamping |
| `game_state.py` | Usa `TAMANO_CELDA` para todo |
| `scripts/game.py` | Usa `ANCHO, ALTO` desde constants |

**Archivos:** `editor/templates/empty_rpg/`

---

### Fase 6 — Runtime: Pixel Art Scale

Cuando `pixel_art_scale > 1`:

1. `pygame.display.set_mode((ANCHO * scale, ALTO * scale))`
2. Renderizar todo a una surface interna de `(ANCHO, ALTO)`
3. `pygame.transform.scale(interna, (ANCHO * scale, ALTO * scale))` → pantalla

Esto da aspecto pixel-perfect retro sin cambiar la lógica del juego.

---

## Archivos del Backlog

| Archivo | Tipo | Fase |
|---|---|---|
| `orm/cururo.json` | Existente | 0 |
| `editor/project.py` | Existente | 1 |
| `editor/project_dialog.py` | Existente | 2 |
| `editor/map_editor.py` | Existente | 3 |
| `editor/sprite_editor.py` | Existente | 3 |
| `editor/event_editor.py` | Existente | 3 |
| `editor/tileset.py` | **Nuevo** | 4 |
| `editor/behaviors.py` | Existente | 4 |
| `editor/templates/empty_rpg/configs/constants.py` | **Nuevo** | 5 |
| `editor/templates/empty_rpg/main.py` | Template | 5 |
| `editor/templates/empty_rpg/camera.py` | Template | 5 |
| `editor/templates/empty_rpg/game_state.py` | Template | 5 |
| `editor/templates/empty_rpg/scripts/game.py` | Template | 5 |
| `docs/GRAPHICS_CONFIG_BACKLOG.md` | **Este archivo** | — |
