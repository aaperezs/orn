# Progreso — Diálogos + Eventos de Boss

## Objetivo
Completar el flujo boss: entrada → alerta → diálogo → pelea → derrota → diálogo post-boss → skill unlock → demo. Refactorizar hardcode a eventos data-driven desde el editor Cururo.

## Estado Actual (22 Jul 2026)

### Completado — Flujo de entrada + post-boss migrado a eventos
- `iniciar_dialogo` acción en `stack_manager.py` — parsea clave compuesta `"personaje/contexto"` y llama a `dialogo.iniciar()`
- **`iniciar_dialogo` ahora retorna `True` (bloqueante)** — acciones post-diálogo se almacenan en `_cola_acciones` hasta que el diálogo termina
- `esperar` acción reescrita con `pygame.time.get_ticks()` (ms reales, no frames); ahora usa `_bloqueo_por = "timer"`
- `bloquear_mandos` acción con parámetro booleano `bloquear` (unifica bloquear/desbloquear)
- `bloquear_eventos` acción (renombrado desde `bloquear_acciones`)
- Marcadores genéricos `{nombre}` en diálogos — carga `assets/nombre.png` con caché, escala a 22px
- Editor `event_editor_widget.py`: acciones `iniciar_dialogo`, `esperar`, `bloquear_mandos`, `bloquear_eventos`, `desbloquear_habilidad`, `equipar_habilidad`, `cambiar_skin`, `mostrar_boss`, `iniciar_demo` con dropdowns correspondientes
- **Nuevo trigger `on_boss_defeated`** + método `StackManager.on_boss_defeated()` — busca eventos con ese trigger en todos los stacks
- **Post-boss eliminado de `combate_manager.py:_derrotar_jefe()`** — ahora solo mata al boss visualmente y llama a `on_boss_defeated()`
- **`main.py`**: `stack_manager.actualizar()` se llama durante el diálogo para poder ejecutar acciones post-diálogo
- **`1-arena_stacks.json`**: evento `trigger_boss` tiene `bloquear_mandos(False)` al final; nuevo evento `post_boss` con trigger `on_boss_defeated` que maneja diálogo de victoria → skill unlock → skin → demo → cambio de nivel
- Hardcode de diálogo de entrada removido de `main.py` y `game_state.py`
- `data/dialogos.json`: `{runa}` → `{runa_28}`
- Bugfix: `import pygame` faltante en `stack_manager.py`
- Bugfix: `_avanzar_char()` chequea `{` antes de incrementar
- Bugfix: dropdown Bloquear/Desbloquear para parámetro `bloquear`

### Pendiente
- Testear flujo completo: entrada → alerta → diálogo → pelea → derrota → diálogo victoria → skill unlock → demo → cambio de nivel

### Bugs Conocidos
- (ninguno abierto)

### Archivos Clave
| Archivo | Rol |
|---------|-----|
| `systems/stack_manager.py` | Acciones: `iniciar_dialogo`, `esperar`, `bloquear_mandos`, `bloquear_eventos` |
| `systems/dialogo.py` | Marcadores `{nombre}`, sprite cache, renderizado |
| `data/dialogos.json` | Datos de diálogos `{personaje: {contexto: [líneas]}}` |
| `levels/mapas_stacks/1-arena_stacks.json` | Evento boss en (9,11) y (3,11) |
| `editor/widgets/event_editor_widget.py` | Editor de eventos con acciones de diálogo |
| `main.py` | Hardcode de diálogo de entrada removido |
| `game_state.py` | `_dialogo_entrada_mostrado` removido |
| `managers/combate_manager.py` | Post-boss migrado a eventos (solo mata boss visualmente + llama on_boss_defeated) |
