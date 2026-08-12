# Plan: Sprite sheet para bosses (2D tile set animado por fases)

## Objetivo
Permitir que cada boss use una hoja de sprites animada por fases: **filas = fases**, **columnas = frames** del bucle de animación. Sin sprite sheet, el boss actual dibuja con primitivas (fallback procedural intacto). "Sprite obligatorio" queda en backlog (cuando los 4 bosses tengan sprite).

## Convención de grilla (decidida)
- Filas = fases (fila 0 = fase 1; fila N-1 = fase N).
- Columnas = frames del bucle de animación de esa fase.
- En runtime se elige la fila con `self.fase` y la columna avanza con el tiempo:
  `col = (ticks // intervalo) % cols`.
- Cada frame se escala/centra a la caja de juego (60×60) → el sprite puede ser 64×64, 128×128, etc., sin tocar colisiones ni layout.
- `visual.*` actuales siguen siendo el fallback procedural.

---

## 1. Datos — `orm/data/bosses.json` (por boss, todos opcionales)

```json
{
  "sprite_sheet": "tronco_boss",
  "sprite_rows": 3,
  "sprite_cols": 4,
  "sprite_frame_w": 64,
  "sprite_frame_h": 64,
  "sprite_interval": 150
}
```

| Campo | Tipo | Notas |
|---|---|---|
| `sprite_sheet` | string | Archivo en `assets/` (sin extensión): `assets/tronco_boss.png`; vacío = procedural |
| `sprite_rows` | int | Nº de filas (fases) |
| `sprite_cols` | int | Nº de columnas (frames por fase) |
| `sprite_frame_w` | int | Ancho de celda |
| `sprite_frame_h` | int | Alto de celda |
| `sprite_interval` | int | ms por frame |

Los `visual.*` actuales siguen siendo el fallback procedural.

**Archivos:** `orm/data/bosses.json`

---

## 2. Runtime — módulo `orm/utils/sprite_sheet.py` (nuevo)

```python
def cargar_hoja(nombre, rows, cols, fw, fh):
    # carga assets/<nombre>.png
    # valida fw*cols <= ancho y fh*rows <= alto  → si no, None
    # recorta y cachea la lista de frames
    # devuelve None si el archivo no existe o la grilla no coincide
```

- Devuelve `list[Surface]` de `rows*cols` frames (orden fila-mayor: `frame[r*cols+c]`).
- `None` si el archivo no existe o la grilla no coincide con el tamaño real de la imagen.

**Archivos:** `orm/utils/sprite_sheet.py` (nuevo)

---

## 3. Runtime — `orm/entities/boss.py`

### `__init__` / `_configurar_tipo`
Leer `sprite_sheet`, `sprite_rows`, `sprite_cols`, `sprite_frame_w`, `sprite_frame_h`, `sprite_interval` (con defaults seguros).

### `dibujar()`
1. Si hay sprite y la hoja carga OK:
   - `sheet = cargar_hoja(...)`
   - `row = min(self.fase, rows - 1)`
   - `col = (pygame.time.get_ticks() // interval) % cols`
   - `frame = sheet[row * cols + col]`
   - `pantalla.blit(pygame.transform.scale(frame, (ancho, alto)), (cx - ancho // 2, cy - alto // 2))`
   - `return` (sin duplicar proyectiles: mantener `dibujar_proyectiles` igual).
2. Si no → proseguir con el código procedural existente sin cambios.
3. Efecto "herido" (alpha/blanqueo) se mantiene **únicamente** en el path procedural; para sprites se puede esquivar en esta iteración.

**Archivos:** `orm/entities/boss.py`

---

## 4. Editor — `editor/boss_tab.py`

Nueva sección **"Sprite"** en la cabecera del boss (`boss.sprite.*` es/en):

| Control | Tipo | Notas |
|---|---|---|
| `boss.sprite.sheet` | Dropdown/TextInput | Opciones = sprites de `assets/*.png`; vacío = procedural |
| `boss.sprite.rows` | Input numérico | Filas (fases) |
| `boss.sprite.cols` | Input numérico | Columnas (frames por fase) |
| `boss.sprite.frame_w` | Input numérico | Ancho de celda |
| `boss.sprite.frame_h` | Input numérico | Alto de celda |
| `boss.sprite.interval` | Input numérico | ms por frame |
| `boss.sprite.preview` | Mini-preview | Recorta celdas (0,0) y (1,0) de la hoja para verificar alineación |

- Si la grilla no coincide con la imagen → mostrar aviso.
- `_on_save` escribe esos campos en `set_boss`; `_select_boss` los lee.
- Comportamiento idéntico al resto del panel.

**Archivos:** `editor/boss_tab.py`

---

## 5. Traducciones — `editor/locales/es.json` / `en.json`

Claves nuevas:

- `boss.sprite`
- `boss.sprite.sheet`
- `boss.sprite.rows`
- `boss.sprite.cols`
- `boss.sprite.frame_w`
- `boss.sprite.frame_h`
- `boss.sprite.interval`
- `boss.sprite.preview`
- Aviso de grilla inválida

**Archivos:** `editor/locales/es.json`, `editor/locales/en.json`

---

## 6. Verificación

- `py_compile` de los archivos tocados.
- Smoke tests headless:
  - `cargar_hoja` con PNG sintético 256×192 (grilla 3×4, celdas 64×64) → 12 frames, slicing correcto.
  - Grilla mayor que la imagen → `None`/warning.
  - `dibujar()` con `sprite_sheet` cargado vs sin él (fallback procedural idéntico al anterior).
  - Editor: guardar/cargar los campos nuevos; `bosses.json` real intacto (solo se toca al guardar).
- Prueba manual: subir un sprite 256×192 de prueba al boss "tronco" → ver 3 formas animadas según la fase.

## Archivos del plan

| Archivo | Tipo |
|---|---|
| `orm/data/bosses.json` | Existente (datos opcionales) |
| `orm/utils/sprite_sheet.py` | **Nuevo** |
| `orm/entities/boss.py` | Existente |
| `editor/boss_tab.py` | Existente |
| `editor/locales/es.json` | Existente |
| `editor/locales/en.json` | Existente |
| `docs/BOSS_SPRITE_SHEET.md` | **Este archivo** |