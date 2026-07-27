# Cururo Platform — Plan de Conversión a Plataforma de Creación de Juegos

## Visión

Cururo Editor debe evolucionar de ser un editor para un juego específico (Orm: El Vástago del Mundo) a una **plataforma genérica de creación de videojuegos 2D** donde cualquiera pueda crear RPGs, aventuras y otros géneros SIN tocar código fuente Python, solo usando las herramientas del editor.

## Arquitectura Meta

```
┌─────────────────────────────────────────────────────┐
│                   CURURO EDITOR                      │
│  (editor/main.py — todos los paneles + menús)        │
│                                                      │
│  Sprite Editor │ Map Editor │ Element Editor │ ...   │
│  NUEVO: Script Editor │ Behavior Editor │ Templates │
└──────────────────────┬──────────────────────────────┘
                       │ exporta datos/
                       │ level_parser + runtime API
                       ▼
┌─────────────────────────────────────────────────────┐
│                RUNTIME ENGINE                        │
│  (orm/main.py simplificado + orm/runtime/)           │
│                                                      │
│  Carga: datos/ → elementos, mapas, animaciones       │
│  Carga: scripts/ → game logic (game.py)              │
│  API Runtime: dibujo, input, entidades, cámara       │
│  Sistema de eventos (stacks) + condiciones/acciones  │
│  Procesamiento genérico por frames                   │
└─────────────────────────────────────────────────────┘
```

## Roadmap (5 Fases — 1 Semana)

### Fase 1 — Editor de Scripts (Días 1-2)
**Archivos a crear:**
- `editor/widgets/script_editor.py` — Widget editor de texto multilínea con:
  - Syntax highlighting para Python (keywords, strings, comments, numbers, decorators)
  - Números de línea en gutter (40px)
  - Resaltado de línea actual
  - Scroll vertical con scrollbar
  - Undo/redo (Ctrl+Z/Y)
  - Tab → 4 espacios, auto-indent
  - Clipboard (Ctrl+C/V/X)
  - Ctrl+S callback
- `editor/scripts.py` — CRUD para scripts del proyecto en `project/scripts/`
- `editor/script_panel.py` — Panel con toolbar + editor + lista de scripts
- Actualizar `editor/main.py` — Registrar `ScriptPanel` en PANEL_CLASSES y menú
- Actualizar locales (`es.json`/`en.json`) con entradas "script.*"

### Fase 2 — API Runtime (Días 2-3) ✅
**Archivos creados:**
- `orm/runtime/` — Nuevo paquete con:
  - `vec2.py` — `Vec2` dataclass con operadores aritméticos
  - `api.py` — Clase `Game` con decoradores (`@game.init`, `@game.update`, `@game.draw`, `@game.input`) + singleton `game`
  - `loader.py` — `load_script(project_root, name)` carga scripts desde `scripts/` usando `importlib`
  - `renderer.py` — API de dibujo: `draw_sprite()`, `draw_rect()`, `draw_circle()`, `draw_line()`, `draw_text()`, `draw_text_centered()`, `load_sprite()`, `sprite_size()`, `text_width()`, `clear_sprite_cache()`
  - `input.py` — API de teclado/mouse: `is_key_down()`, `is_key_just_pressed()`, `is_key_just_released()`, `get_mouse_pos()`, `get_mouse_buttons()`, `handle_event()`, `clear_frame()`. Mapa string→keycode incluido.
  - `camera.py` — Clase `Camera` con `follow()`, `snap_to()`, `apply()`, `set_bounds()`, `is_visible()`, smoothing.
  - `__init__.py` — Exporta todo
  - `test_api.py` — 7 tests headless (todos pasan)
  - `test_runner.py` — Runner completo con pygame
- `orm/scripts/game.py` — Script demo que usa la API (cubo moves con flechas + cámara)

**Próximo:** Fase 3 — Behaviors extensibles + plugins (custom_behaviors.json, panel editor, run_script action)

### Fase 3 — Behaviors Extensibles + Plugins (Días 3-4) ✅
**Archivos creados:**
- `orm/data/behaviors.json` — Schema de behaviors en JSON (12 behaviors con propiedades, class_path, target_list, group)
- `editor/custom_behaviors.py` — Panel visual para crear/editar behaviors desde Cururo (lista + editor con campos: ID, label, group, class_path, target_list, properties dinámicas con add/remove)
- `orm/entities/generic.py` — `GenericEntity` para behaviors sin clase específica; soporta propiedades arbitrarias y hook `on_update` que llama a función del script

**Modificaciones:**
- `editor/behaviors.py` — Refactorizado: carga desde `data/behaviors.json` del proyecto. Mantiene `BEHAVIORS` y `DEFAULT_ELEMENT_PROPERTIES` como backward-compat. Hardcoded como fallback si no existe el JSON. Funciones CRUD: `get_behaviors()`, `get_behavior()`, `set_behavior()`, `delete_behavior()`, `create_behavior()`.
- `editor/widgets/event_editor_widget.py` — Nueva acción `run_script` con params `function_name` y `args`
- `editor/main.py` — Registrado `CustomBehaviorsPanel` en PANEL_CLASSES ("behaviors") + menú Herramientas > Comportamientos. `editor_behaviors._load()` llamado en startup.
- `orm/systems/stack_manager.py` — Handler `run_script`: busca función por nombre en módulos cargados (`game`, `scripts.game`) y la ejecuta con args opcionales.
- `editor/locales/es.json` / `en.json` — 10 nuevas entradas `behavior.*` + `event.action.run_script`

**Próximo:** Fase 4 — Desacoplar Orm + sistema de plantillas (mover lógica de main.py a scripts/game.py, templates de proyecto, nuevo proyecto desde Cururo)

### Fase 4 — Desacoplar Orm + Plantillas (Días 5-6) ✅
**Archivos creados:**
- `editor/templates/empty_rpg/` — Template de proyecto vacío con:
  - `cururo.json` (manifiesto)
  - `data/elementos.json`, `data/animations.json`, `data/behaviors.json`
  - `scripts/game.py` (script mínimo que usa la API Runtime)
  - `assets/`, `levels/mapas/`, `levels/mapas_stacks/` (directorios vacíos)

**Modificaciones:**
- `editor/project.py` — Nuevas funciones:
  - `list_templates()` — descubre templates en `editor/templates/`
  - `create_project(template_id, name, target_dir)` — copia template + escribe cururo.json con nombre e ID
- `editor/project_dialog.py` — Dos modos:
  - `STATE_LIST`: muestra proyectos existentes + "Nuevo Proyecto" como primera opción
  - `STATE_NEW`: formulario con nombre, selector de plantilla (TAB para cambiar), botones Crear/Cancelar
  - Navegación completa con teclado (↑↓ Enter ESC TAB) y mouse
- `editor/main.py` — `nuevo_proyecto()` implementado:
  - Diálogo modal in-editor con overlay semi-transparente
  - Campos: nombre, plantilla (TAB), Crear/Cancelar
  - Al crear: cambia al nuevo proyecto, recarga datos, reconstruye UI

**Próximo:** Fase 5 — Polish + documentación (tests de integración, docs de API Runtime, QA)

### Fase 5 — Polish + Documentación (Día 7) ✅
**Archivos creados:**
- `docs/API_RUNTIME.md` — Referencia completa de la API Runtime con tablas de funciones, ejemplos y guía de uso
- `docs/QUICKSTART.md` — Tutorial paso a paso: crear proyecto → sprites → elementos → mapa → script → ejecutar
- `tests/test_platform_integration.py` — 18 tests de integración:
  - Template system (list, create)
  - Behaviors data (hardcoded, JSON, project loading)
  - Runtime API (hooks, Vec2, camera, loader, renderer, input)
  - Bedrock imports (script_editor, script_panel, custom_behaviors, generic_entity, project_dialog)

**Resultados:** 86/86 tests pasan (68 existentes + 18 nuevos)

### Resumen de las 5 fases

| Fase | Estado | Archivos creados/modificados |
|------|--------|------------------------------|
| 1 — Editor de Scripts | ✅ | script_editor.py, scripts.py, script_panel.py, main.py, locales |
| 2 — API Runtime | ✅ | orm/runtime/ (7 archivos: api, loader, renderer, input, camera, vec2, test) |
| 3 — Behaviors extensibles | ✅ | behaviors.json, behaviors.py refactor, custom_behaviors.py, run_script action, GenericEntity |
| 4 — Templates + Nuevo Proyecto | ✅ | empty_rpg template, project.py (create/list_templates), project_dialog.py (2 modos), nuevo_proyecto en main.py |
| 5 — Polish + Docs + QA | ✅ | docs/API_RUNTIME.md, docs/QUICKSTART.md, 18 integration tests, 86/86 tests |

## Estado Actual (Antes de Fase 1)

### Lo que ya funciona
- Editor de sprites pixel-art
- Editor de mapas multicapa con eventos (stacks: trigger + condiciones + acciones)
- Editor de animaciones con glow
- Editor de elementos (tiles con behaviors)
- Editor de habilidades, ítems, bosses
- Editor de eventos

### Lo que está hardcodeado y limita la plataforma
1. **Game loop entero en `orm/main.py`** — lógica de serpiente, habilidades, combate
2. **12 behaviors fijos en `editor/behaviors.py`** — no extensibles desde el editor
3. **3 habilidades hardcodeadas** con if/elif en main.py
4. **Sin scripting** — no hay forma de agregar lógica personalizada sin editar Python
5. **Runtime acoplado a Orm** — Snake, segmentos, enroscamiento, etc.

## Convenciones de Código

### Editor de Scripts (Fase 1)
- El widget `ScriptEditor` hereda de `Widget` (no de `TextArea`)
- El tokenizador de Python es simple (regex-free, línea por línea con estado)
- El gutter mide 40px de ancho
- Los colores de syntax highlighting están definidos como constantes RGB en el mismo archivo
- Los scripts se guardan como `.py` en `project/scripts/`
- El panel `ScriptPanel` sigue el patrón de `AnimationPanel` (toolbar + editor)
