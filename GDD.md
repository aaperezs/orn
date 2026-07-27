# GDD — Orm: La Serpiente Enroscada

## 1. Visión General

Juego de serpiente 2D con mecánicas de combate, habilidades, jefes y un sistema de capas Z. El jugador controla a **Orm**, una serpiente verde que se enrosca para empujar rocas, destruir obstáculos y enfrentar enemigos.

- **Resolución:** 800x600 px
- **Tile:** 20x20 px (40x30 tiles por nivel)
- **Motor:** Pygame 2.6
- **Estilo:** 8-bit/pixel art
- **Editor:** Cururo Editor (pygame), proyecto separado del juego, con selector de proyectos al inicio y 5 pestañas: Sprites/Mapas/Eventos/Elementos/Jefes

---

## 2. Personaje — Orm

Orm es una serpiente que se mueve por el mapa en grid discreto (múltiplos de 20 px).

### Estados
| Estado | Descripción |
|--------|-------------|
| **Normal** | Movimiento libre por el grid |
| **Enroscado** | Se enrosca sobre sí mismo (círculo apretado). No se mueve. Activa empuje de rocas y bloqueos. |
| **Durmiendo** | Estado enroscado inactivo. Muestra "apreta [tecla]" y flechas direccionales. |
| **Manto** | Intangible por 2 segundos (habilidad). Atraviesa paredes y enemigos. |

### Mecánica de Enroscamiento
- Orm se enrosca al presionar la tecla de acción estando sobre ciertos objetos (roca, bloque acero, árbol).
- Mientras está enroscado, puede empujar objetos en la dirección que miraba al enroscarse.
- Al desenroscarse, recupera su longitud y posición.
- **Cooldown anti-bucle:** 2 frames de inmunidad tras desenroscarse para evitar ciclos infinitos roca-pared.

### Velocidad
- Base: `10` (frames entre movimientos)
- Con deuda de escamas: `12` (más lento)
- Sobre pasto alto: `×0.6`
- Sobre speed-grass: `×1.3`

---

## 3. Habilidades

Sistema de 3 habilidades equipables + skin base. Se alternan con TAB y se activan con Q.

| Habilidad | PP | Efecto | Tecla | Skin |
|-----------|----|--------|-------|------|
| Golpe de Cabeza | 5 | Rompe rocas, aturde enemigos | Q | Café (cabeza 210,180,140 / cuerpo 139,90,43) |
| Manto de Oscuridad | 3 | Intangible 2s | W | Gris (180,180,190 / 80,80,90) |
| Cola Látigo | 4 | Gira 360°, corta vegetación | E | Naranja (230,120,50 / 200,60,30) |

---

## 4. Comida

| Tipo | Color | Nombre | Efecto |
|------|-------|--------|--------|
| Normal (0) | Rojo | Fruta de Esencia | Crece +1 |
| Mana (1) | Morado | Baya de Mana | Recarga PP |
| Especial (2) | Dorado | Fruta Dorada | Crece +3 |

Probabilidades de spawn: 5% especial, 15% mana, 80% normal.

Al recoger comida aparece texto flotante sobre Orm (`+1`, `+3`, `+PP`) que sube y se desvanece.

---

## 5. Entidades

Cada entidad del juego se define como un **elemento** en `data/elementos.json` con un **behavior** que determina su lógica en runtime y **propiedades** configurables desde el editor.

Comportamientos disponibles (11): `bloqueante`, `peligroso`, `hierba`, `food`, `enemigo_melee`, `enemigo_shooter`, `boss`, `decorative`, `spawn`, `suelo`, `multi_tile`.

Propiedades comunes: `solid`, `destructible`, `destructible_hp`, `cracked_sprite` (sprite cuando está agrietado), `animation` (nombre de animación), `pushable`, `damage_type`, `food_type`.

| Elemento | Sprite | Behavior | Propiedades clave |
|----------|--------|----------|-------------------|
| Roca | `roca.png` / `roca_grieta.png` | `block_breakable` | `health: 1`, `damage: 1` |
| Roca de Hielo | `roca_hielo.png` | `block_breakable` | `health: 1` |
| Roca de Nieve | `roca_nieve.png` | `block_breakable` | `health: 1` |
| Bloque Acero | `bloque_acero.png` | `block_pushable` | Solo se mueve si Orm está enroscado. |
| Árbol | `arbol.png` | `tree` | Indestructible. Muestra "El arbol es demasiado grueso". |
| Hierba Alta | `hierba_0/1/2.png` | `tall_grass` | Ralentiza (`×0.6`), se puede cortar con Cola Látigo. |
| Pared | `pared.png` | `wall` | Mata a Orm al colisionar. Tiene púas (spikes) direccionales. |
| Gate | `gate.png` | `gate` | `cost: 5`, muestra "ESC: 5" o "ABIERTO". |
| Cofre | `cofre.png` | `bloqueante` | Sólido. Otorga loot mediante eventos `interact` → `give_item` en el stack del tile. |
| Decorativo | cualquiera | `decorative` | Elemento visual sin colisión. Soporta animación y glow. |

### Enemigos

| Enemigo | Sprite | HP | Patrones | Proyectiles |
|---------|--------|----|----------|-------------|
| Melee (casco vikingo) | `enemigo_melee.png` | 1 | Horizontal / Vertical / Circular | No |
| Shooter (casco circular) | `enemigo_shooter.png` | 1 | Horizontal / Vertical | Sí, 2 direcciones opuestas |

Ambos tienen pupilas que siguen la dirección de movimiento.

### Segmento Perdido
- Forma de escama (diamante ámbar con brillos)
- Brillo dorado (aura)
- Aparece al perder longitud (daño recibido)
- Se dispersa en dirección aleatoria (3–8 tiles)
- Vida útil: 60 frames, luego parpadea y desaparece
- Al recogerlo: efecto de anillo sónico + texto flotante

---

## 6. Sistema de Combate

### Daño
| Concepto | Valor |
|----------|-------|
| Longitud mínima | 3 |
| Daño mínimo | 2 |
| Daño máximo | 4 |
| Duración manto | 60 frames |
| Color manto | (80, 80, 100) |

### Jefes

| Jefe | Tipo | Vida | Descripción |
|------|------|------|-------------|
| Tronco, el Ciervo Podrido | `tronco` | 80 | Dispara runas doradas ({runa}). Fases por velocidad creciente. |
| (futuro) Gélica | `gelida` | — | Jefe de hielo (planeado) |

**Flujo de jefe:**
1. Orm toca portal → animación de entrada a arena
2. Arena se activa → jefe aparece (enroscado/en Snake Enroscado)
3. Diálogo de entrada (carga de `configs/dialogos.json`)
4. Combate: esquivar proyectiles, juntar poder rúnico, dañar al jefe
5. Jefe derrotado → diálogo de salida → teletransporte instantáneo de vuelta al mundo
6. Arena se desactiva, aparece comida en la posición de salida

### Proyectiles del Jefe
- Aparecen con sprite de runa dorada
- Orm puede "comer" proyectiles (contador: `proyectiles_comidos / proyectiles_necesarios`)
- Se usan como moneda para dañar al jefe

---

## 7. Sistema de Capas Z (Editor)

El editor de mapas permite crear hasta **5 capas dinámicas** (Z=0 a Z=4) para composición visual.

| Capa | Descripción |
|------|-------------|
| Z=0 | Base: terreno, paredes, gameplay principal |
| Z=1 | Plataformas / elementos elevados |
| Z=2 | Decoración / elementos intermedios |
| Z=3 | Nubes / elementos superiores |
| Z=4 | Techo / cielo / elementos decorativos frontales |

### Reglas
- **Z=0** es obligatoria (capa base, no se puede eliminar)
- Se agregan capas con botón "+ Capa" (máx 5 total)
- Cada capa tiene su propio grid, visibilidad y opacidad independientes
- Las operaciones de pintado solo afectan la capa activa
- **El juego carga todas las capas** y las renderiza en orden ascendente de Z (0 abajo, 4 arriba)
- Las entidades se renderizan ordenadas por su `z` (no por tipo)
- **Colisión**: los objetos peligrosos (paredes/espinas) se evalúan ANTES que los objetos bloqueantes (rocas). Si un peligroso mata al jugador, no se evalúan los bloqueantes.

### Archivos
```
{map_id}.json       → Z=0
{map_id}_z1.json    → Z=1
{map_id}_z2.json    → Z=2
{map_id}_z3.json    → Z=3
{map_id}_z4.json    → Z=4
```

---

## 8. Niveles / Mapas

Los niveles se cargan desde archivos de mapa en `levels/mapas/`.

| Mapa | Tamaño (tiles) | Inicio | Capas |
|------|----------------|--------|-------|
| 1-1 | 40×30 (800×600) | (80, 520) | 1 (Z=0) |
| 1-2 | 40×29 (800×580) | (360, 20) | 1 (Z=0) |
| 1-3 | 47×18 (940×360) | (20, 20) | 1 (Z=0) |
| 1-4 | 46×16 (920×320) | (20, 20) | 1 (Z=0) |
| 1-arena | 20×15 (400×300) | — | 1 (Z=0) |
| 1-test | 10×10 (200×200) | (100, 140) | 1 (Z=0) |
| habilidad-1 | 28×606 (560×12120) | — | 1 (Z=0) |

### Formato JSON v2
```json
{
  "version": 2,
  "ancho": 40,
  "alto": 30,
  "grid": {
    "0,0": "pared",
    "5,7": "inicio"
  }
}
```

### Punto de inicio (spawn)
- Definido por el sprite `inicio` (H) colocado en una celda del grid
- El juego escanea todos los mapas al cargar y empieza en el primero que tenga `inicio`
- Meta file: `{map_id}_meta.json` guarda `{"spawn": {"pos": [x,y], "z": capa}}`
- Fallback: centro del mapa si no hay sprite `inicio`

---

## 9. Renderizado (Orden de Capas)

De atrás a adelante:
1. `pantalla.fill(FOREST_BG)` — color base
2. Grid de tiles del editor renderizado por capa Z (0 abajo → 4 arriba)
3. Entidades renderizadas ordenadas por su propiedad `z` (menor Z abajo, mayor Z arriba), sin importar el tipo de entidad
4. Arena del jefe (si activa) + portal
5. Enemigos (si no hay arena)
6. Segmentos perdidos
7. Orm (la serpiente)
8. Partículas
9. Textos flotantes
10. UI (escamas, deuda, controles, mensajes)
11. HUD de habilidades

> **Nota:** El renderizado de entidades ya no es por tipo (rocas después de paredes). Todas las entidades (hierba, paredes, comida, rocas, bloques) se agrupan por su atributo `z` y se dibujan en orden ascendente. Esto permite que objetos en Z=2 (ej. espinas) se vean sobre objetos en Z=1 (ej. rocas).

Solo se renderizan los tiles dentro del viewport visible (`first_col..last_col`, `first_row..last_row`).

---

## 10. Assets / Sprites

Todos los sprites están en `assets/` como PNG de 20×20 px. El registro maestro es `editor/sprite_registry.py`.

| Archivo | Descripción |
|---------|-------------|
| `pasto.png` | Piso base con ruido verde |
| `pasto_esteril.png` | Piso oscuro sin decoración (no spawn) |
| `pared.png` | Madera para paredes |
| `roca.png` / `roca_grieta.png` | Roca intacta / agrietada |
| `roca_hielo.png` | Roca de hielo |
| `roca_nieve.png` | Roca con nieve |
| `bloque_acero.png` | Montaña/bloque indestructible |
| `arbol.png` | Árbol con copa |
| `hierba_0..2.png` | Pasto alto (3 variantes) |
| `gate.png` | Portal azul |
| `comida_normal.png` | Manzana roja |
| `comida_mana.png` | Ratón morado |
| `comida_dorada.png` | Manzana dorada |
| `enemigo_melee.png` | Casco vikingo |
| `enemigo_shooter.png` | Casco circular |
| `deco_0..3.png` | Flores, musgo, brotes |
| `spawn_hero.png` | Marcador H de spawn (gris semi-transparente + borde) |

28 sprites registrados. Cada elemento referencia un sprite por su `sprite_id`; el sprite Registry es ahora solo un catálogo visual.

Todos los sprites tienen canal alfa (SRCALPHA) para que el pasto de fondo se vea a través de las partes transparentes.

---

## 11. Sistema de Elementos

Inspirado en RPG Maker: los sprites son solo arte, los **elementos** definen el comportamiento y las propiedades de cada cosa en el juego.

### Archivo
`data/elementos.json` — 28 elementos que reemplazan el antiguo sistema de entidades hardcodeadas.

### Estructura
```json
{
  "pasto": {
    "sprite_id": "pasto",
    "name": "Pasto",
    "behavior": "decoration",
    "properties": {}
  },
  "roca": {
    "sprite_id": "roca",
    "name": "Roca",
    "behavior": "block_breakable",
    "properties": {
      "health": 1,
      "damage": 1,
      "drops": true
    }
  },
  "enemigo_melee": {
    "sprite_id": "enemigo_melee",
    "name": "Enemigo Melee",
    "behavior": "enemy_melee",
    "properties": {
      "health": 1,
      "speed": 10,
      "pattern": "horizontal",
      "damage": 1
    }
  }
}
```

### Behaviors (12 tipos)

Definidos en `editor/behaviors.py`. Cada uno tiene un esquema de propiedades que el editor renderiza como campos dinámicos.

| Behavior | Label | Propiedades |
|----------|-------|-------------|
| `decorative` | Decorativo | `animation` |
| `spawn` | Spawn | — |
| `suelo` | Suelo | `no_food_spawn`, `animation` |
| `bloqueante` | Bloqueante | `solid`, `destructible`, `destructible_hp`, `pushable`, `cracked_sprite`, `animation` |
| `peligroso` | Peligroso | `solid`, `damage_type` (mata/danio), `animation` |
| `hierba` | Hierba | `solid`, `animation` |
| `food` | Comida | `solid`, `food_type` (normal/mana/dorada), `animation` |

| `enemigo_melee` | Enemigo melee | `solid`, `damage_type`, `destructible`, `patron` (vertical/horizontal/circular) |
| `enemigo_shooter` | Enemigo shooter | `solid`, `damage_type`, `destructible`, `patron` (shooter_h/shooter_v) |
| `boss` | Jefe | `solid` |
| `multi_tile` | Multi-tile | `tile_rows`, `tile_cols` |

### Sistema de Animaciones

Definiciones en `data/animations.json`. Cada animación tiene frames (sprite_ids), intervalo (ms), y glow opcional:

```json
{
  "comida_dorada": {
    "frames": ["comida_dorada", "comida_dorada_2"],
    "interval": 400,
    "glow": { "enabled": true, "color": [255, 215, 0], "radius": 10, "alpha": 80 }
  }
}
```

- `systems/animation.py`: `get_anim_sprite(name)` alterna frames según `pygame.time.get_ticks()`
- `get_anim_glow(name)` retorna la config de aurea para el renderizado
- Entidades con propiedad `animation` usan el sistema en su `dibujar()`
- Elementos decorativos con animación se convierten en entidad `Decorativo` con Z-sorting y glow

### Factory Pattern (runtime)

El `LevelParser` usa **fábricas por behavior** en lugar de un solo switch de entidades. Cada behavior tiene su propia clase factory que recibe las propiedades del elemento y construye la entidad correspondiente:

```
elemento → behavior → factory_class(propiedades) → entidad del juego
```

Las fábricas se registran con `_reg_factory(behavior, fn)` en `levels/level_parser.py`. Para behaviors sin factory personalizada, se usa una factory genérica que crea la entidad desde `class_path` del behavior con las propiedades como kwargs.

### Daño a Objetos Destructibles

Rocas y bloques (`bloqueante`) pueden recibir daño con la habilidad Golpe Cabeza:

1. Propiedades del elemento: `destructible: true`, `destructible_hp: 2`, `cracked_sprite: "roca_grieta"`
2. `golpear()` en `entities/objeto_colision.py` reduce HP y llama a `stack_manager.on_hit()` con el daño
3. Si `cracked_sprite` está configurado y HP > 0, cambia automáticamente el tile de la grilla
4. Si HP ≤ 0: desactiva la entidad, publica `EventoObjetoDestruido`, remueve el tile de la grilla
5. Los stacks con trigger `on_hit` pueden filtrar por condición `damage >= X`

Las propiedades se asignan directamente desde el elemento vía `setattr` (sin filtro `hasattr`), por lo que cualquier propiedad personalizada funciona en runtime aunque no esté predefinida en la clase.

### Plan: Destructibles por tipo de ataque

Actualmente solo `bloqueante` (rocas) es destructible vía `golpear()` con `attack_type="golpe"`. Se necesita extender a `hierba` (hierba alta) con otro tipo de ataque:

**Objetivo:** Cada tipo de objeto destructible especifica qué `attack_type` lo daña.

| Objeto | Ataque que lo daña | Propiedades |
|--------|-------------------|-------------|
| Roca | `golpe` (golpe cabeza) | `destructible: true`, `attack_type_weak: "golpe"`, `destructible_hp: 2`, `cracked_sprite: "roca_grieta"` |
| Hierba alta | `latigo` (cola látigo) | `destructible: true`, `attack_type_weak: "latigo"`, `destructible_hp: 1` |

**Pasos para implementar:**

1. Agregar propiedad `attack_type_weak` al behavior `bloqueante` y `hierba` en `editor/behaviors.py`
2. Implementar `golpear()` en `HierbaAlta` (heredado de `ObjetoColision` o propio) que verifique `attack_type == attack_type_weak` antes de dañar
3. En `main.py`, hacer que `usar_habilidad_golpe()` itere también `estado.hierba_alta` (pero el daño solo aplica si `attack_type` coincide)
4. Idem para `usar_habilidad_latigo()` sobre `estado.rocas` + `estado.bloques_acero`
5. Opcional: `cracked_sprite` para hierba (ej: "hierba_cortada")
6. Los stacks con trigger `on_hit` reciben `attack_type` como extra (ya implementado) y pueden filtrar por tipo de ataque

### Flujo de datos completo
```
editor/element_tab.py (GUI)
  → editor/elements.py (CRUD)
    → data/elementos.json
      → levels/level_parser.py (factory por behavior)
        → entities/ (instancia con propiedades)
```

### Editor de Elementos (4ta pestaña del Cururo Editor)
- **Lista**: panel izquierdo con todos los elementos, scroll, selección
- **Toolbar**: Nuevo, Clonar, Eliminar, Guardar
- **Propiedades**: panel derecho con campos dinámicos según el behavior seleccionado (bool, choice, int, text)
- **Selector de sprite**: dropdown con todos los sprites registrados
- **Selector de behavior**: dropdown que cambia las propiedades editables
- **Vista previa**: preview del sprite seleccionado

---

### Plataforma Cururo — Hacia un creador de juegos genérico

Ver `CURURO_PLATFORM.md` en la raíz del proyecto para el plan completo de convertir
Cururo Editor en una plataforma de creación de videojuegos 2D.

---

## 12. UI / Estilo Visual

### Temática Nórdica / Bosque
- **Fondo base:** `FOREST_BG` (verde bosque oscuro)
- **Fonts:** Georgia / Palatino Linotype / Book Antiqua con fallback a Pygame default
- **Brillo Rúnico:** Texto principal dorado (`DORADO`) con halo glow blanco-cálido alrededor (2–3 capas de offset 1px, sin negrita para evitar blur)
- Todos los textos de UI, diálogo y temporales usan el mismo estilo de glow

### Elementos en pantalla
- **Esquinas:** Escamas acumuladas / deuda de escamas
- **Controles:** "Q: Habilidad | TAB: Cambiar" (esquina inferior)
- **Gate:** "ESC: N" sobre el portal o "ABIERTO"
- **Jefe:** Barra de vida vertical rúnica (madera tallada + segmentos luminosos), nombre + icono arriba, fase abajo con runa futhark
- **Esferas de Poder:** `N` huecos circulares en el centro superior de la pantalla; se llenan con esferas doradas al comer proyectiles del jefe.
- **Habilidades:** HUD con PP restantes y habilidad equipada
- **Diálogo:** Caja de madera con texto typewriter (glow rúnico), sprite de runa inline, avance con ESPACIO/ENTER
- **Prologue:** Texto-on-black cinemático con word-wrap, revelado char-by-char, navegación con SPACE + dots

### Mensajes temporales
- Mensajes tipo toast con glow dorado
- Texto flotante sobre Orm al recoger comida/segmentos

---

## 13. Sistema de Prólogo

Carga texto desde `data/prologo.json` y lo muestra como cinemática antes del game loop:
- Pantalla negra, texto centrado
- Palabra-wrap automático
- Caracteres aparecen 1 por frame
- SPACE avanza al siguiente párrafo
- Dots de navegación abajo
- Al finalizar, transición al juego

---

## 14. Sistema de Demo (Tutorial Post-Jefe)

Al derrotar a Tronco por primera vez, Orm es transportado a `habilidad-1.txt` para aprender Golpe de Cabeza.

### Flujo
1. Diálogo del jefe → "tu primera habilidad..."
2. Teletransporte a nivel demo con una roca y un gate de retorno
3. Skill equipada + skin aplicada automáticamente
4. Pasos guiados (acercarse, golpear, regresar por gate)
5. Cada paso espera confirmación con retry kick
6. Input del jugador bloqueado durante la demo
7. Al cruzar el gate: mensaje de aprendizaje completado

---

## 15. Sistema de Eventos (Stacks)

Sistema de eventos por tile, manejado por `systems/stack_manager.py` y `editor/event_editor.py`.

### Formato (nuevo)
```json
{
  "pos": [5, 3],
  "z_layer": 0,
  "eventos": [
    {
      "trigger": "contact",
      "condiciones": [
        {"tipo": "has_item", "params": {"item": "llave_dorada"}}
      ],
      "acciones": [
        {"tipo": "show_message", "params": {"mensaje": "Has abierto la puerta"}},
        {"tipo": "activate_gate", "params": {"gate_id": "gate_5_3"}}
      ]
    }
  ]
}
```

### Triggers
| Trigger | Descripción |
|---------|-------------|
| `contact` | Al tocar el tile |
| `interact` | Al interactuar (tecla acción) |

### Condiciones (11 tipos)
| Tipo | Params | Descripción |
|------|--------|-------------|
| `has_ability` | `ability`, `nivel_min` | Tiene habilidad con nivel mínimo |
| `not_has_ability` | `ability` | No tiene habilidad |
| `has_ability_equipped` | `ability` | Habilidad equipada |
| `not_has_ability_equipped` | `ability` | No tiene equipada |
| `has_pp` | `min` | PP actual >= min |
| `has_item` | `item`, `cantidad_min` | Tiene N items (>= cantidad_min) |
| `not_has_item` | `item`, `cantidad` | No tiene N items (< cantidad) |
| `has_escamas` | `min` | Escamas del snake >= min (usa `snake.get_escamas()`) |
| `not_has_escamas` | `cantidad` | Escamas del snake < cantidad |
| `has_flag` | `flag` | Flag global activado |
| `not_has_flag` | `flag` | Flag global desactivado |

### Acciones (11 tipos)
| Tipo | Params | Descripción |
|------|--------|-------------|
| `show_message` | `mensaje` | Muestra mensaje temporal |
| `replace_sprite` | `sprite_id` | Cambia el sprite del tile (en `tile_overrides`) |
| `spawn_entity` | `sprite_id`, `offset_x`, `offset_y`, `z` | Spawnea entidad |
| `start_dialogue` | `dialogo_id` | Inicia diálogo |
| `change_map` | `nivel` | Cambia de nivel |
| `give_item` | `item`, `cantidad` | Da item |
| `remove_item` | `item`, `cantidad` | Quita item |
| `consume_pp` | `cantidad` | Consume PP |
| `set_flag` | `flag` | Activa flag global |
| `clear_flag` | `flag` | Desactiva flag global |

### Migración
- Formato antiguo (`capas` con `tipo`/`accion`/`parametros`) se auto-convierte a nuevo formato en `StackManager.__init__`

---

## 16. Editor — Cururo Editor

Editor visual en Pygame con 5 pestañas:

### Pestaña Sprites
- Editor de píxeles 20×20 con zoom (scroll wheel)
- **Herramientas:** Lápiz, Borrador (transparencia), Balde (flood fill), Gotero
- **Slider de opacidad** para dibujar semi-transparente (0-255)
- **Undo/Redo:** Ctrl+Z / Ctrl+Shift+Z (historial de 50 estados)
- Selector de color con 27 preajustes
- Carga/guarda PNG desde `assets/`

### Pestaña Mapas
- Editor de mapas con paint/erase en grid
- **Capas dinámicas** (1-5): botón +/− para agregar/quitar capas
- Por capa: toggle visibilidad + slider opacidad
- Paleta de sprites desde `SPRITE_REGISTRY` (28 IDs), con resolución vía `element_id → sprite_id`
- El painado en mapa resuelve el sprite del elemento automáticamente
- Scroll con viewport + zoom
- Guarda/carga JSON v2 por capa (`{id}_zN.json`)

### Pestaña Eventos
- Editor de stacks por tile (cadena trigger→condiciones→acciones)
- Interfaz de lista con dropdowns y campos inline
- Soporta 2 triggers, 7 condiciones, 11 acciones
- Carga/guarda desde `levels/mapas_stacks/{id}_stacks.json`

### Pestaña Elementos
- Editor de elementos con lista + toolbar (Nuevo, Clonar, Eliminar, Guardar)
- Selector de sprite y behavior por elemento
- Propiedades dinámicas según el behavior seleccionado (bool, choice, int, text)
- Vista previa del sprite
- Persistencia en `data/elementos.json`

### Pestaña Jefes
- Editor de bosses con lista + toolbar
- Campos: nombre, fight type, vida máxima, proyectiles necesarios, daño/ciclo, icono
- Editor de N fases colapsables con parámetros dinámicos según el fight type
- Cada fase tiene threshold de HP, params de combate y visuales
- Persistencia en `data/bosses.json`

### Internacionalización
- JSONs de locale: `editor/locales/es.json`, `editor/locales/en.json`
- Toggle en runtime desde la barra de idioma

---

## 17. Estado Actual — Julio 2026

### Implementado
- [x] Movimiento grid de Orm (4 direcciones)
- [x] Enroscamiento / desenroscamiento con cooldown anti-bucle
- [x] Enemigos melee y shooter con ojos tracking
- [x] Sistema de habilidades (3 habilidades + base)
- [x] Golpe de Cabeza, Manto de Oscuridad, Cola Látigo
- [x] Sistema de comida (3 tipos)
- [x] Segmentos perdidos con física de dispersión
- [x] Paredes con púas
- [x] Gate con requisito de escamas
- [x] Sistema de capas Z (editor: 5 capas dinámicas 0-4)
- [x] Arena de jefe con portal
- [x] Jefe "Tronco" con diálogos de entrada/salida
- [x] Proyectiles rúnicos del jefe
- [x] Diálogo con efecto typewriter y sprite de runa inline
- [x] Carga de niveles desde archivos de mapa (JSON v2 + legacy .txt)
- [x] Cámara con seguimiento suave
- [x] Renderizado de piso con tile pasto + decoraciones
- [x] Sprites con canal alfa (transparencia)
- [x] Partículas (explosiones, anillos sónicos)
- [x] Textos flotantes
- [x] Estilo visual nórdico (fuentes Georgia/Palatino, glow rúnico)
- [x] Sistema de prólogo
- [x] Demo post-jefe con Golpe de Cabeza
- [x] God Mode (F3 toggle)
- [x] Esferas de Poder en UI de jefe
- [x] Sistema de eventos por tile (trigger→condiciones→acciones)
- [x] Stack Manager con 11 condiciones y 11 acciones
- [x] Condiciones `has_escamas`/`not_has_escamas` para gate con requisito de escamas
- [x] Fix: `Inventario.cantidad()` y `Inventario.remover_item()` agregados (bugs de `has_item`/`remove_item`)
- [x] Fix: `GameState.flags` inicializado (bugs de `set_flag`/`clear_flag`/`has_flag`/`not_has_flag`)
- [x] Sprite Registry (28 sprite IDs con metadatos)
- [x] Editor visual 3 en 1: Sprites, Mapas, Eventos
- [x] Gotero (eyedropper) para copiar colores + opacidad
- [x] Slider de opacidad en editor de sprites
- [x] Undo/Redo en editor de sprites
- [x] Capas dinámicas en editor de mapas (1-5 capas)
- [x] Multi-archivo por capa (`{id}_zN.json`)
- [x] Ruta multi-capa: editor guarda, juego carga y renderiza
- [x] Fix: entidades renderizadas ordenadas por `z` (no por tipo) — espinas en Z=2 se ven sobre rocas en Z=1
- [x] Fix: objetos peligrosos (paredes/espinas) evaluados antes que rocas en colisión — si mata, no evalúa bloqueantes
- [x] Fix: `_make_bloqueante` recibe y aplica `z_layer` del grid — rocas/bloques respetan su capa Z
- [x] Fix: `stack_manager.py` — eventos con `once: false` ya no se marcan como `"finalizado"` ni se filtran al recargar nivel

### Element System — Implementado
- [x] Sistema de Elementos (RPG Maker style): sprite = arte, elemento = comportamiento + props
- [x] `data/elementos.json` con 28 elementos migrados desde SPRITE_REGISTRY
- [x] `editor/behaviors.py` con 12 behaviors y schemas de propiedades
- [x] `editor/elements.py` — CRUD loader para elementos.json
- [x] `editor/element_tab.py` — 4ta pestaña del editor con lista + editor de propiedades
- [x] `levels/level_parser.py` — fábricas por behavior (factory pattern)
- [x] Paleta de mapas resuelve `element_id → sprite_id`
- [x] `systems/stack_manager.py` usa `spawn_from_element`

### Boss System Paramétrico — Implementado
- [x] Boss fight types: `editor/boss_fight_types.py` define schemas de parámetros por tipo de pelea
- [x] `data/bosses.json` con formato expandido: fight_type, damage_per_cycle, N fases con params y visual
- [x] `editor/boss_data.py` — CRUD para bosses.json
- [x] `editor/boss_tab.py` — 5ta pestaña del editor con lista + editor de fases colapsables
- [x] `entities/boss.py` — refactorizado para leer `_phase_config()` desde JSON (velocidad, cooldown, proyectiles, órbita, colores, runas)
- [x] Fases con N thresholds configurables (no limitado a 3)
- [x] `combate_manager.py` usa `boss.damage_per_cycle` y `boss.proyectiles_necesarios`
- [x] Editor con campos dinámicos según fight type schema

### Arquitectura Limpia — Implementado
- [x] **Dataficación JSON**: enemigos, habilidades, jefes, comida, objetos, recetas, rocas_eventos
- [x] **Repositorios**: `repositories/` package completo
- [x] **Bus de Eventos**: `systems/event_bus.py` con 10+ tipos de eventos
- [x] **Sistema de Equipamiento**: `entities/inventario.py` con 3 slots y 5 objetos equipables
- [x] **Cofres**: elementos `cofre` con `behavior: bloqueante` + eventos `interact` → `give_item`
- [x] **Forja**: `systems/forja.py` con recetas desde `data/recetas.json`
- [x] **Eventos de roca**: drops probabilísticos desde `data/rocas_eventos.json`
- [x] **Internacionalización**: editor con locale ES/EN toggleable

### Planeado / En Progreso
- [ ] Animación de daño al jefe
- [ ] Jefe "Gélida" (variante de hielo)
- [ ] Propiedades de colisión por sprite (qué sprites son sólidos en qué capas)
- [ ] Más habilidades o mejoras
- [ ] Transiciones de capa con animación
- [ ] Destructibles por tipo de ataque: roca←golpe cabeza, hierba←cola látigo (ver "Plan: Destructibles por tipo de ataque")
- [ ] `attack_type_weak` en behaviors para filtrar qué ataque daña cada objeto
- [ ] `golpear()` en HierbaAlta con verificación de `attack_type`
- [ ] **Phase 1**: Editor de Scripts (ScriptPanel + syntax highlighting)
- [x] **Phase 2**: API Runtime (orm/runtime/ con hooks init/update/draw) ✅
- [x] **Phase 3**: Behaviors extensibles + plugins (behaviors.json, custom panel, run_script action) ✅
- [x] **Phase 4**: Sistema de plantillas + Nuevo Proyecto desde Cururo ✅
- [ ] **Phase 5**: Documentación + QA
- Ver `CURURO_PLATFORM.md` para el plan completo
- [ ] Más niveles / mapas
- [ ] Efecto de congelación en hielo (terreno que desliza)
- [ ] **Sistema de items en HUD**: Permitir que items de inventario se muestren en pantalla (similar al contador de escamas). Requiere: (a) editor visual del HUD, (b) registrar qué items mostrar por mapa o por evento, (c) contadores sincronizados con el inventario. Esto permitiría al gate checkear items custom en lugar de solo escamas del snake.

---

## 18. Guía de Arquitectura

### Flujo de Datos
```
data/*.json  →  repositories/*.py  →  configs/*.py  →  consumidores (entities, managers, systems)
                                                        ↑
systems/event_bus.py  →  publicación de eventos  →  handlers suscritos en main.py
```

### Cómo agregar un enemigo nuevo
1. Agregar entrada en `data/enemigos.json` (tipo + subtipo + stats)
2. Agregar carácter en `LevelParser.CHAR_MAP` y su parsing en `parsear_mapa()`
3. Opcional: sprite en `assets/`
4. Opcional: registrar en `editor/sprite_registry.py`

### Cómo agregar un objeto nuevo
1. Agregar en `data/objetos.json` con slot y efectos
2. En `data/recetas.json` agregar receta para forjarlo

### Cómo agregar un cofre
1. Colocar elemento `cofre` o `cofre_key1` en el mapa JSON
2. Agregar stack con trigger `interact` → acción `give_item` y el item deseado

### Cómo agregar drops de roca
1. Agregar entrada en `data/rocas_eventos.json` con probabilidad y tipo
2. El bus de eventos (`EventoRocaRota`) lo maneja automáticamente

### Cómo agregar un elemento nuevo
1. Abrir pestaña "Elementos" en el editor
2. Click "Nuevo" → se crea con behavior `decoration` y primer sprite disponible
3. Seleccionar behavior (cambia las propiedades editables automáticamente)
4. Configurar sprite, nombre y propiedades
5. Click "Guardar" → persiste en `data/elementos.json`

### Cómo cambiar el comportamiento de un elemento existente
1. Seleccionar elemento en la lista
2. Cambiar el behavior en el dropdown
3. Las propiedades se reinician a los defaults del nuevo behavior
4. Guardar

### Cómo agregar un behavior nuevo
1. Crear entry en `BEHAVIORS` en `editor/behaviors.py` con label y schema de propiedades
2. Opcional: agregar clase factory en `levels/level_parser.py` y registrarla en `FACTORY_MAP`
3. El editor renderiza las propiedades automáticamente según el schema
