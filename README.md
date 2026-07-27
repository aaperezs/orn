# Orm: La Serpiente Enroscada

Juego 2D Pygame — serpiente en grid con combate, habilidades, jefes y capas Z.

**Entry point:** `main.py` | **Res:** 800×600 | **Tile:** 20×20 | **Python:** Pygame 2.6

---

> **Cururo Platform:** Este proyecto es el juego de demostración/referencia de la plataforma Cururo. Ver `CURURO_PLATFORM.md` en la raíz del proyecto para el plan de evolución.

## AI Agent — Quick Reference

### Directorio Clave

| Ruta | Qué es |
|------|--------|
| `main.py` | Game loop, input, renderizado, suscripciones a eventos |
| `game_state.py` | `GameState` — estado global del juego |
| `camera.py` | Cámara con seguimiento suave |
| `config.py` | Constantes (colores, velocidades, físicas) |
| `entities/` | Todas las entidades del juego (snake, rocas, enemigos, etc.) |
| `systems/` | Sistemas puros (event_bus, stack_manager, habilidades, partículas) |
| `managers/` | Managers de colisión, combate, comida |
| `levels/` | LevelParser, LevelManager, mapas, eventos por tile (stacks) |
| `repositories/` | CRUDs para datos JSON (enemigos, habilidades, objetos, jefes) |
| `handlers/` | Handlers de eventos (event_handler.py) |
| `data/` | JSONs: elementos, enemigos, habilidades, bosses, recetas |
| `assets/` | Sprites PNG (20×20, con canal alfa) |
| `configs/` | Diálogos y configuraciones extra |

### Arquitectura

```
data/*.json → repositories/* → level_parser (factory por behavior)
                                  ↓
                            entities/* (instancias con propiedades)
                                  ↓
                            managers/* (colisión, combate, comida)
                                  ↓
                            systems/* (event_bus, stack_manager, habilidades)
                                  ↓
                            main.py (game loop, renderizado)
```

### Flujo de Eventos

```
pygame.event → main.py → handlers/event_handler.py
                            ↓
                    systems/event_bus.py (publicación de eventos)
                            ↓
                    Handlers suscritos en main.py (_on_objeto_destruido, etc.)
```

### Sistema de Elementos (RPG Maker style)

Los sprites son solo arte visual. Los **elementos** (`data/elementos.json`) definen comportamiento + propiedades:

```
elemento → behavior (12 tipos) → factory_class(propiedades) → entidad runtime
```

Behaviors: `decorative`, `spawn`, `suelo`, `bloqueante`, `peligroso`, `hierba`, `food`, `enemigo_melee`, `enemigo_shooter`, `boss`, `multi_tile`.

Propiedades comunes: `solid`, `destructible`, `destructible_hp`, `cracked_sprite`, `animation`, `pushable`, `damage_type`, `food_type`.

### Sistema de Eventos (Stacks)

Eventos por tile con trigger→condiciones→acciones, manejados por `systems/stack_manager.py`.

Triggers: `contact` (al pisar), `interact` (al interactuar), `on_hit` (al recibir golpe). 12 condiciones, 13 acciones.

Condiciones: `escamas`, `item_count`, `flag`, `ability`, `ability_equipped`, `pp`, `evaluar_evento`, `damage` (daño del golpe).

### Entidades Principales

| Clase | Archivo | Behavior |
|-------|---------|----------|
| `Snake` | `entities/snake.py` | — |
| `ObjetoBloqueante` | `entities/objeto_colision.py` | `bloqueante` |
| `Roca` | `entities/roca.py` | `bloqueante` (hereda ObjetoBloqueante, sprite desde grilla) |
| `RocaHielo` | `entities/roca_hielo.py` | `bloqueante` |
| `RocaNieve` | `entities/roca_nieve.py` | `bloqueante` |
| `BloqueAcero` | `entities/bloque_acero.py` | `bloqueante` |
| `Arbol` | `entities/arbol.py` | `bloqueante` (hereda BloqueAcero) |
| `HierbaAlta` | `entities/hierba_alta.py` | `hierba` |
| `Pared` | `entities/pared.py` | `peligroso` |
| `Boss` | `entities/boss.py` | `boss` |
| `Food` | `entities/food.py` | `food` |
| `Decorativo` | `entities/decorativo.py` | `decorative` (con soporte de animación) |
| `Boss` | `entities/boss.py` | — |
| `Food` | `entities/food.py` | `food` |

### Cómo agregar un elemento nuevo

1. Ir al editor → pestaña "Elementos" → Nuevo → configurar behavior + propiedades
2. El editor persiste en `data/elementos.json`
3. Si el behavior ya existe, el `LevelParser` lo maneja automáticamente
4. Si es un behavior nuevo: agregar en `editor/behaviors.py` + factory en `levels/level_parser.py`

### Sistema de Animaciones

Definidas en `data/animations.json`, renderizadas por `systems/animation.py`:

```json
{
  "comida_dorada": {
    "frames": ["comida_dorada", "comida_dorada_2"],
    "interval": 400,
    "glow": { "enabled": true, "color": [255, 215, 0], "radius": 10, "alpha": 80 }
  }
}
```

- `get_anim_sprite(name)` — retorna el sprite_id del frame actual según `pygame.time.get_ticks()`
- `get_anim_glow(name)` — retorna la config de aurea si está activada
- Entidades con `self.animation` usan `get_anim_sprite()` en su `dibujar()`
- Elementos decorativos con animación se convierten en `Decorativo` entity (en lugar de sprite estático de grilla)
- El glow se renderiza como círculos concéntricos superpuestos detrás del sprite

### Sistema de Daño a Objetos Destructibles

Las rocas y bloques con `destructible: true` y `destructible_hp: N` reciben daño vía `golpear()`:

1. Al golpear, reduce `destructible_hp` en `damage`
2. Si hay `cracked_sprite` configurado y HP > 0, cambia el tile de la grilla
3. Si HP ≤ 0: desactiva la entidad, publica `EventoObjetoDestruido`, remueve el tile de la grilla
4. Llama a `stack_manager.on_hit()` que procesa eventos con trigger `on_hit` y condición `damage`

El daño se pasa como extra a las condiciones del stack, permitiendo condiciones como `damage >= 1`.

**Plan futuro:** Extender a `hierba` (hierba alta) como destructible por `attack_type="latigo"` (cola látigo). Ver GDD.md → "Plan: Destructibles por tipo de ataque".

### Documentación Relacionada

- `GDD.md` — Game Design Document completo (mecánicas, habilidades, UI, niveles)
- `../editor/README.md` — Guía del Cururo Editor
- `../editor/TECH-DESIGN.md` — Arquitectura detallada del editor
