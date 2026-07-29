# Cururo Platform — Roadmap

## Visión
Cururo Editor debe evolucionar de ser un editor para un juego específico (**Orm: El Vástago del Mundo**) a una **plataforma genérica de creación de videojuegos 2D** donde cualquiera pueda crear RPGs, visual novels, aventuras y otros géneros SIN tocar código fuente Python, solo usando las herramientas del editor.

## Principios
1. **Cururo es el motor.** El runtime se incluye DENTRO del proyecto generado como código, no como dependencia externa.
2. **Desacoplado de Orm.** Orm es solo un proyecto de categoría `snake_rpg`. Cururo no importa nada de `entities/`, `managers/` ni `domain/` de Orm.
3. **Por categoría.** Cada proyecto elige una categoría al crearse. El editor muestra solo los paneles relevantes.
4. **Importación de assets.** Cualquier proyecto puede importar imágenes, audio, sprites, animaciones, etc.

---

## Fase 0 — Arquitectura de categorías ✅ COMPLETADA

### Objetivo
Desacoplar Cururo de Orm. Permitir crear proyectos de diferentes categorías con behaviours, paneles y runtimes propios.

### Archivos creados

| Archivo | Propósito |
|---------|-----------|
| `editor/categories.py` | 3 categorías: `snake_rpg`, `visual_novel`, `blank` |
| `templates/visual_novel/` | Template base para visual novel |
| `templates/blank/` | Template vacío |

### Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `editor/behaviors.py` | Eliminado hardcode de 11 behaviors de Orm. Ahora carga desde `data/behaviors.json` del proyecto activo |
| `editor/project.py` | `Project.category` + `get_available_panels()`. Templates filtrables por categoría |
| `editor/project_dialog.py` | Selector de categoría con teclado/mouse |
| `editor/main.py` | Paneles, menú y workspace filtrados por `get_available_panels()` |
| `templates/empty_rpg/` | Renombrado a `templates/snake_rpg/` |
| `data/behaviors.json` (snake_rpg) | Contiene los 11 behaviors que antes estaban hardcodeados |

### Pendiente post-Fase 0
- [ ] `templates/snake_rpg/scripts/game.py` no debe importar `orm.runtime`. El runtime debe copiarse dentro del proyecto al crearlo.
- [ ] `cururo.json` del proyecto debe guardar `category` y `runtime_version`.
- [ ] Verificar que `templates/visual_novel/` sea funcional (depende de Fase 1).

---

## Fase 1 — Runtime Visual Novel

### Objetivo
Agregar al runtime las herramientas necesarias para crear visual novels / juegos de citas: diálogos con opciones, flags de estado, fondos y personajes en pantalla.

### 1.1 Sistema de opciones

**Nuevo archivo:** `systems/choice_box.py`
- Widget `ChoiceBox` que renderiza lista de opciones
- Selección con ↑↓ + ENTER o mouse
- Cada opción tiene: `texto`, `acciones` a ejecutar al seleccionar

**Nueva acción en `stack_manager.py`:** `mostrar_opciones`
- Params: `opciones` → `[{texto, acciones: [{tipo, params}]}]`
- Bloqueante: pausa eventos hasta que el jugador elija
- Al elegir, ejecuta las acciones de la opción

### 1.2 Sistema de flags

**Nuevo archivo:** `runtime/flags.py`
- Clase `FlagsManager`: diccionario clave → valor
- Soporta: int, string, bool, float

**Nuevas acciones:**
- `set_flag(nombre, valor)` — escribe flag
- `add_flag(nombre, cantidad)` — suma a flag numérico

**Nuevas condiciones en eventos:**
- `"flag:nombre == valor"`, `"flag:nombre >= 5"`, etc.
- Evaluado en `_check_conditions()`

### 1.3 Fondos y personajes

**Nuevas acciones:**
- `cambiar_fondo(sprite_id)` — cambia el fondo (escalado a pantalla)
- `mostrar_personaje(id, posicion, expresion)` — muestra sprite
  - `posicion`: `izquierda`, `centro`, `derecha`
  - Sprite: `assets/personajes/{id}_{expresion}.png`
- `ocultar_personaje(id)` / `ocultar_todos_personajes`

**Modificar `game_state.py`:**
- `self.fondo_activo = None`
- `self.personajes_visibles = {}`
- `self.flags = FlagsManager()`

**Modificar `main.py` dibujar():**
- Orden: fondo → personajes → entidades → UI

### 1.4 Diálogo avanzado

**Modificar `systems/dialogo.py`:**
- Soporte para `{flag:nombre}` en texto (se reemplaza por valor)
- Post-diálogo: ejecutar `_cola_acciones` (ya existe)

### 1.5 Template visual_novel funcional

- Escena de ejemplo: fondo + personaje + diálogo con opciones
- `data/dialogos.json` con branching
- `assets/fondo_ejemplo.png`, `assets/personajes/runa_feliz.png`

---

## Fase 2 — Panel de personajes (editor)

Editor visual para:
- CRUD de personajes (nombre, ID, color de texto)
- Retratos por emoción/estado (feliz, triste, enojado, sonrojado)
- Previsualización con nombre

---

## Fase 3 — Editor de diálogo ramificado

Extender/reemplazar DialogTab con:
- Nodos: diálogo, opción, condición, acción, salto
- Editor visual de árbol
- Validación de rutas (detectar nodos huérfanos)
- Condiciones por flag
- Acciones: `set_flag`, `change_bg`, `show/hide character`, `play_sfx`, `launch_minigame`

---

## Fase 4 — Gestor de assets visuales (alta resolución)

- Importar PNG/JPG desde sistema de archivos
- Asignar fondos a escenas
- Previsualización fondo + retratos en editor
- CG gallery (imágenes bloqueables por flag)
- Posicionamiento: left/center/right para retratos, fill/fit/center para fondos

---

## Fase 5 — Editor de escenas / branching

- Orden de escenas por capítulo
- Condiciones de entrada (flag check)
- Pantalla de título personalizable
- Tipos de escena: diálogo, minijuego, CG, ending

---

## Fase 6 — Minijuegos

- Sistema para "llamar" minijuego desde flujo VN
- Reutilizar editor de mapas/sprites existente
- Pasar resultado (score, victoria) a flags del VN
- Tipos: recolección, timing, puzzle

---

## Fase 7 — Audio

- Importar BGM/SFX
- Asignar música por defecto a escenas
- Nodos de audio en diálogo
- Volumen, fade in/out

---

## Historial

| Fase | Estado | Fecha |
|------|--------|-------|
| Fase 0 — Arquitectura de categorías | ✅ Completada | Jul 2026 |
| Fase 1 — Runtime VN | 🔜 Pendiente | — |
| Fase 2 — Panel de personajes | ⏳ Pendiente | — |
| Fase 3 — Editor de diálogo | ⏳ Pendiente | — |
| Fase 4 — Assets visuales | ⏳ Pendiente | — |
| Fase 5 — Editor de escenas | ⏳ Pendiente | — |
| Fase 6 — Minijuegos | ⏳ Pendiente | — |
| Fase 7 — Audio | ⏳ Pendiente | — |

## Notas
- Las Fases pueden solaparse o reordenarse según necesidad.
- Cada Fase debe dejar el sistema funcional (aunque sea mínimo) antes de pasar a la siguiente.
- Este documento se actualiza al completar o modificar cada Fase.
