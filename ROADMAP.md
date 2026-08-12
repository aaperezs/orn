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

### ✅ 1.1 Sistema de opciones

**Nuevo archivo:** `systems/choice_box.py`
- Widget `ChoiceBox` que renderiza lista de opciones (stateless, lee de game_state)
- Dibujado: recuadro semitransparente, opción resaltada, teclas ↑↓ + ENTER
- Integrado en `main.py` dibujar() y `input_manager.py` _handle_key()

**Nueva acción en `stack_manager.py`:** `mostrar_opciones`
- Params: `opciones` → `[{texto, acciones: [{tipo, params}]}]`
- Bloqueante: setea `estado.mostrando_opciones = True`, pausa el stack
- Al elegir: ejecuta acciones de la opción vía `stack_manager.ejecutar_ahora()`

**Nuevo método público:** `stack_manager.ejecutar_ahora(accion_dict)` — ejecuta una acción directamente sin contexto de tile.

### ✅ 1.2 Sistema de flags

**Nuevo archivo:** `runtime/flags.py`
- Clase `FlagsManager`: diccionario clave → valor (int, string, bool, float)
- Métodos: `get()`, `set()`, `add()`, `check()` (operadores: `==`, `!=`, `>=`, `<=`, `>`, `<`, `es_verdadero`, `es_falso`)

**Acciones:** `set_flag(nombre, valor)` y `add_flag(nombre, cantidad)` — ambas añadidas a stack_manager.

### ✅ 1.3 Fondos y personajes

**Nuevas acciones en stack_manager:**
- `cambiar_fondo(sprite_id)` → setea `estado.fondo_activo`
- `mostrar_personaje(id, posicion, expresion)` → inserta en `estado.personajes_visibles`
- `ocultar_personaje(id)` / `ocultar_todos_personajes`

**Modificado `game_state.py`:**
- `self.flags = FlagsManager()` (reemplaza `self.flags = {}`)
- `self.fondo_activo = None`, `self.personajes_visibles = {}`
- `self.mostrando_opciones = False`, `self.opciones = []`, `self.opcion_seleccionada = -1`

**Modificado `main.py` dibujar():**
- VN Mode: si `fondo_activo` set → dibuja fondo + personajes + UI + choice_box, salta rendering normal

### ⏳ 1.4 Diálogo avanzado

**Pendiente:**
- [ ] `systems/dialogo.py`: reemplazar `{flag:nombre}` en texto por valor de flag
- [ ] Post-diálogo: ejecutar `_cola_acciones` (ya existe el mecanismo)

### ✅ 1.5 Template visual_novel funcional

**Nuevo archivo:** `templates/visual_novel/template.json`
- Evento auto con acciones reales: `cambiar_fondo`, `mostrar_personaje`, `dialogo_inline`, `mostrar_opciones`
- Branching: opción "Continuar" vs "Salir del modo VN"
- Uso de `{flag:nombre}` en texto de diálogo

---

### ✅ 1.4 Diálogo avanzado

**Modificado `systems/dialogo.py`:**
- Nuevo método `iniciar_inline(lineas, boss_nombre, al_terminar)` — recibe lista de strings directamente, sin pasar por JSON
- `_dividir_texto_con_marcadores` acepta `flags` y reemplaza `{flag:nombre}` por el valor del flag

### ✅ 1.6 Parches y fixes

| Ítem | Archivo | Cambio |
|------|---------|--------|
| `_bloqueo_por == "choice"` | `stack_manager.py:actualizar` | Agregado handler que limpia el bloqueo cuando `mostrando_opciones` se vuelve False |
| Flag condition string-safe | `stack_manager.py:_check_conditions` | Si flag o esperado es string, compara con `==`/`!=` en vez de castear a int |
| `_cola_ctx` preservation | `input_manager.py` + `stack_manager.py` | `ejecutar_secuencia` acepta `ctx` opcional; input_manager pasa `_cola_ctx` original |
| `dialogo_inline` en editor | `editor/categories.py` | Agregado a categoría visual_novel |

### ✅ Template actualizado

`templates/visual_novel/template.json` ahora usa acciones reales en lugar de metadata `dialogo` no procesada.

## Fase 2 — Panel de personajes (editor) ✅ COMPLETADA

### Archivos creados

| Archivo | Propósito |
|---------|-----------|
| `editor/character_data.py` | CRUD sobre `data/personajes.json`. Campos: `nombre`, `color_texto [R,G,B]`, `retratos {emoción: sprite_id}` |
| `editor/character_panel.py` | Panel visual con: toolbar (Nuevo/Clonar/Eliminar/Guardar), lista izquierda con scroll, editor derecho con inputs para nombre, color RGB (con swatch) y 6 emociones predefinidas |

### Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `editor/categories.py` | Panel `characters` agregado a categorías `visual_novel` y `snake_rpg` |
| `editor/main.py` | `CharacterPanel` registrado en `PANEL_CLASSES`, `_load_characters()` llamado en startup |
| `editor/locales/es.json` | Traducciones `character.*` + `tab.characters` |
| `editor/locales/en.json` | English translations for character panel |
| `editor/templates/visual_novel/data/personajes.json` | Personaje "runa" predefinido con 6 emociones |
| `editor/templates/snake_rpg/data/personajes.json` | Plantilla vacía para `snake_rpg` |
| `editor/templates/blank/data/personajes.json` | Plantilla vacía para `blank` |

### Datos del personaje

```json
{
  "personajes": {
    "runa": {
      "nombre": "Runa",
      "color_texto": [255, 200, 200],
      "retratos": {
        "normal": "personajes/runa_normal",
        "feliz": "personajes/runa_feliz",
        ...
      }
    }
  },
  "protegidos": []
}
```

### Emociones soportadas
`normal`, `feliz`, `triste`, `enojado`, `sonrojado`, `sorpresa`

---

## Fase 3 — Editor de diálogo ramificado ✅ COMPLETADA

### Archivos modificados/creados

| Archivo | Cambio |
|---------|--------|
| `editor/dialog_data.py` | Extendido: soporta formato árbol (`nodes` + `start`) junto al plano. API nueva: `get_tree`, `set_tree`, `add_node`, `remove_node`, `create_tree_key`, `compile_to_flat`. Constantes `NODE_TYPES`, `NODE_LABELS`, `NODE_COLORS` |
| `editor/dialog_tree_panel.py` | **Nuevo.** Reemplaza `DialogTab`. Editor visual de árbol con toolbar (+ Diálogo, + Opción, + Condición, + Acción, + Salto), lista izquierda de claves, vista de árbol con badges de tipo + preview, panel detalle contextual según tipo de nodo |
| `editor/main.py` | `DialogTab` → `DialogTreePanel` en `PANEL_CLASSES` |
| `orm/systems/stack_manager.py` | Acción `dialogo_tree` + método `_avanzar_arbol_dialogo()` + acción `_arbol_choice` + `_bloqueo_por == 'dialogo_tree'` en `actualizar` |

### Tipos de nodo

| Tipo | Campos | Color |
|------|--------|-------|
| `dialogo` | texto, next | Azul |
| `opcion` | choices[{texto, next}] | Amarillo |
| `condicion` | flag, operador, valor, next, next_false | Púrpura |
| `accion` | tipo_accion, params, next | Verde |
| `salto` | destino | Naranja |

### Formato de datos

```json
{
  "runa": {
    "saludo": {
      "flat": ["linea1", "linea2"],
      "nodes": {
        "n1": {"tipo": "dialogo", "texto": "¡Hola!", "next": "n2"},
        "n2": {"tipo": "opcion", "choices": [...]}
      },
      "start": "n1"
    }
  }
}
```

### Runtime
- `dialogo_tree(dialogo_id)` bloquea el stack y reproduce el árbol nodo por nodo
- Soporta: diálogo (typewriter + SPACE), opciones (ChoiceBox), condiciones (flags), acciones, saltos a otro contexto

---

## Fase 4 — Gestor de assets visuales ✅ COMPLETADA

### Archivos creados

| Archivo | Propósito |
|---------|-----------|
| `editor/asset_data.py` | Registro de assets (`data/assets.json`). `import_asset()` copia PNG/JPG al proyecto, registra tipo, modo posición, flag desbloqueo. API: get/set/delete, filtro por tipo |
| `editor/asset_panel.py` | Panel editor con toolbar (Importar/Eliminar/Guardar), filtros por tipo (Todos/Fondos/Pers./CG/Sprites), lista izquierda, previsualización escalada, editor de metadatos (nombre, tipo, modo posición, flag desbloqueo) |

### Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `editor/categories.py` | Panel `assets` agregado a `visual_novel` y `snake_rpg` |
| `editor/main.py` | `AssetPanel` registrado en `PANEL_CLASSES`, `_load_assets()` en startup |
| `editor/locales/es.json` + `en.json` | Traducciones `asset.*` + `tab.assets` |
| `editor/templates/*/data/assets.json` | Registro de assets predefinidos (visual_novel con fondo y 6 retratos de Runa) |
| `orm/game_state.py` | Nuevo campo `fondo_modo` ("fill", "fit", "center") |
| `orm/main.py` | VN Mode mejorado: escala fondo según modo (fill → stretch, fit → proporcional + letterbox, center → raw centrado) |
| `orm/systems/stack_manager.py` | `cambiar_fondo` acepta `modo` param |

### Modos de posicionamiento

| Modo | Comportamiento |
|------|---------------|
| `fill` | Escala para llenar pantalla (puede deformar) |
| `fit` | Escala proporcional + barras negras |
| `center` | Tamaño original centrado sobre fondo negro |

---

## Fase 5 — Editor de escenas / branching ✅ COMPLETADA

- Orden de escenas por capítulo
- Condiciones de entrada (flag check)
- Pantalla de título personalizable
- Tipos de escena: diálogo, minijuego, CG, ending

### Archivos creados

| Archivo | Propósito |
|---------|-----------|
| `editor/scene_data.py` | CRUD sobre `data/scenes.json`. Capítulos con lista de escenas; tipos (`dialogo`/`minijuego`/`cg`/`ending`); condición de entrada por flag; pantalla de título personalizable |
| `editor/scene_panel.py` | Panel editor con lista de capítulos (izquierda), escenas por capítulo (derecha arriba), editor contextual por tipo (campos, condición de entrada), sección de título (toggle, fondo, título, subtítulo) |
| `orm/systems/scene_player.py` | Runtime: `load_scenes()`, `find_first_scene()`, `evaluate_condition()` con operadores `==`/`!=`/`>`/`<`/`>=`/`<=` |
| `orm/systems/screens/titulo.py` | `TituloScreen`: fondo personalizable, título, subtítulo, hint "[ENTER]" |
| `editor/templates/*/data/scenes.json` | Default escenas por tipo de proyecto |

### Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `editor/categories.py` | Panel `scenes` agregado a `visual_novel`, `snake_rpg`, `blank` |
| `editor/main.py` | `ScenePanel` registrado en `PANEL_CLASSES`; `_load_scenes()` en startup |
| `editor/locales/es.json` + `en.json` | Traducciones `scene.*` + `tab.scenes` |
| `orm/systems/screen_manager.py` | Si `screen_id == "title"` y `scenes.json` tiene `titulo.enabled`, crea `TituloScreen` |

---

## Fase 6 — Minijuegos

- Sistema para "llamar" minijuego desde flujo VN
- Reutilizar editor de mapas/sprites existente
- Pasar resultado (score, victoria) a flags del VN
- Tipos: recolección, timing, puzzle

---

## Fase 7 — Audio ✅ COMPLETADA

- Importar BGM/SFX (extensión del sistema de assets existente)
- Asignar música por defecto a escenas (campo `scene_default` en audio.json)
- Acciones de audio en stack (`play_bgm`, `stop_bgm`, `play_sfx`, `set_bgm_volume`, `set_sfx_volume`)
- Volumen, fade in/out (parámetro `fade_ms` en play/stop)

### Archivos creados

| Archivo | Propósito |
|---------|-----------|
| `orm/systems/audio_manager.py` | Runtime: `play_bgm(asset_id, fade_ms)`, `stop_bgm(fade_ms)`, `play_sfx(asset_id)`, `set_bgm_volume()`, `set_sfx_volume()`. Usa `pygame.mixer.music` para BGM (loop/volumen/fade), `pygame.mixer.Sound` para SFX multicanal |
| `editor/audio_data.py` | CRUD sobre `data/audio.json`. Campos: `asset_id`, `tipo` (bgm/sfx), `volumen`, `loop`, `scene_default` |
| `editor/audio_panel.py` | Panel editor con lista, selector de asset (desde assets.json), tipo (BGM/SFX dropdown), volumen, toggle loop, escena por defecto |
| `editor/templates/*/data/audio.json` | Defaults por tipo de proyecto |

### Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `editor/asset_data.py` | `ASSET_TIPOS` extendido con `bgm`/`sfx`; `import_asset()` acepta `.wav`/`.ogg`/`.mp3`; `get_available_extensions()` actualizado |
| `editor/categories.py` | Panel `audio` agregado a las 3 categorías |
| `editor/main.py` | `AudioPanel` registrado, `_load_audio()` en startup, menú "Audio" |
| `editor/locales/es.json` + `en.json` | Traducciones `audio.*` + `tab.audio` |
| `orm/game_state.py` | `self.audio = AudioManager()` |
| `orm/main.py` | `pygame.mixer.init()` después de `pygame.init()` |
| `orm/systems/stack_manager.py` | 5 acciones de audio: `play_bgm`, `stop_bgm`, `play_sfx`, `set_bgm_volume`, `set_sfx_volume` |
| `orm/editor/categories.py` | Categoría `audio` con las 5 acciones |

---

## Fase 8 — Correcciones de QA: pantalla y título ✅ COMPLETADA

### Contexto

QA del runtime VN: **orm funciona correctamente salvo por la pantalla y el
título**. El resto (retratos, minijuegos, fondo hardcodeado, tipos de escena,
persistencia de personajes) son funcionalidad a resolver en el editor, no bugs
de runtime.

- **Pantalla:** `main.py` abre una ventana fija de `1600×1200` (quality default
  `"medium"` → `_render_scale=2`), que excede la resolución del monitor
  (1920×1080 → 1200 > 1080). El rendering ya usa un buffer lógico de 800×600
  (`display.py`), así que el fix es de ventana/presentación, no de renderizado.
- **Título:** `systems/screens/titulo.py` avanza con ENTER, ESPACIO y ESC y con
  clic; el hint dice "[ENTER]". Debe avanzar solo con ENTER.

### 8.1 display.py — ajuste al escritorio + letterbox

- [x] `setup(window_size, fullscreen)`: si `fullscreen=True` →
      `set_mode((0,0), pygame.FULLSCREEN)`; si no, tamaño = escala uniforme 4:3
      que entra en `pygame.display.get_desktop_sizes()` (nunca mayor que el
      monitor).
- [x] `present()`: letterbox real (`scale = min(rw/800, rh/600)`), relleno del
      fondo del window con `set_letterbox_fill` (escala cover) o negro, contenido
      centrado.
- [x] Nuevo `set_letterbox_fill(surf|None)`.

### 8.2 main.py — usar el ajuste + relleno con fondo

- [x] Quitar `ANCHO*_render_scale` del tamaño de ventana; conservar `_fullscreen`
      desde `cururo.json window.fullscreen`.
- [x] Bucle VN: `set_letterbox_fill(obtener_sprite(estado.fondo_activo))` cada
      frame → las barras se rellenan con el fondo activo (`fondo_ejemplo`), como
      relleno sin funcionalidad.
- [x] Bucle snake: `set_letterbox_fill(None)`.

### 8.3 titulo.py — solo ENTER

- [x] Solo `K_RETURN` avanza; quitar `K_SPACE`, `K_ESCAPE` y el clic de ratón.

### 8.4 Templates — fullscreen configurable

- [x] Añadir `"window": {"fullscreen": false}` a los `cururo.json` de
      `editor/templates/*/` (explícito y configurable).

### 8.5 Criterio de aceptación

- [x] `python orm/main.py --project test_nv`: la ventana entra en el monitor,
      letterbox con el fondo de relleno, y el título avanza solo con ENTER.
- [x] `python orm/main.py --test` (snake): sin regresión.
- [x] Fullscreen: probar con `window.fullscreen=true` temporal en un proyecto.

---

## Fase 9 — Estabilización de la suite de tests ⏳ PLANIFICADA

### Contexto

El desarrollo de la plataforma (Fases 0-7) avanzó sin commitear, y la suite
`orm/tests/` (tests del juego ORN original + tests de plataforma aspiracionales)
quedó desincronizada con el runtime. Al momento del plan, 45 tests fallan,
agrupados en 5 causas raíz. Ningún fallo proviene de los archivos VN
(`main.py`, `systems/stack_manager.py`, `systems/vn_state.py`); se verificó el
grafo de imports de cada módulo que falla.

### 9.1 Rutas de datos (arregla 8 tests)

- [ ] `orm/project_paths.py`: `runtime_root()` — quitar un `dirname()` en el
      fallback (devuelve `orm/` en vez de `python/`).
  - Causa: sin proyecto activo, `data_dir()` resuelve a `python/data`
    (archivos faltantes) → repos devuelven `{}`.
  - Efecto: `test_config_provider.py` (4) + `test_data_service.py` (4) en verde.
  - Se conserva el comportamiento proyecto-aware (usado por el editor).

### 9.2 Fixture FakeEstado (arregla 20 tests)

- [ ] `orm/tests/test_input_manager.py`: completar `FakeEstado` para espejar
      `GameState`: `mostrando_minijuego`, `mostrando_opciones`, `opciones`,
      `opcion_seleccionada`, `ventana` (con `activo`/`avanzar`), y los
      atributos que surjan al iterar con pytest.
  - Causa: AttributeError en cascada por atributos faltantes.
  - Efecto: los 20 tests de `TestInputManager` en verde.

### 9.3 Tests obsoletos

- [ ] Eliminar `test_get_demo_timers`: llama a `data_service.get_demo_timers()`,
      método que no existe (ni en HEAD ni en worktree) y no se usa en el runtime.

### 9.4 test_platform_integration.py (16 tests)

- [ ] Path: añadir `python/` al sys.path (conftest o el propio test) para
      `import editor.*` / `import orm.*`.
- [ ] API obsoleta: `empty_rpg` → `snake_rpg` en `test_list_templates` y
      `test_create_project`; `test_behaviors_load_hardcoded` adaptado (behaviors
      ya no hardcode, se cargan de `data/behaviors.json`).
- [ ] `TestRuntimeAPI`: marcar xfail/skip documentado como **API legado**
      (decisión tomada). `orm.runtime` (Game/Vec2/Camera/loader/renderer/input)
      está incompleta (`runtime/game.py` no existe) y la arquitectura actual
      copia el runtime dentro del proyecto.

### 9.5 Criterio de aceptación

- [ ] `python -m pytest tests/` con 0 fallos (los xfail/skip explícitos y
      documentados).
- [ ] Smoke: `python orm/main.py --project test_nv` arranca sin crashear.
- [ ] Snake: `python orm/main.py --test` arranca sin crashear.
- [ ] Sin regresiones en los tests VN headless.

### 9.6 Checkpoint (decisión tomada)

- [ ] Commit del trabajo de plataforma pendiente (Fases 0-7 + runtime VN +
      Fase 8 + Fase 9) una vez la suite esté en verde.

---

## Fase 10 — Resolución base (editor) + resolución del jugador (runtime) ✅ COMPLETADA

### Contexto

- La resolución lógica estaba fija en `configs/constants.py` (800×600) y se usa
  en ~25 archivos. En fullscreen, el contenido 4:3 se veía a 1440×1080 con
  barras laterales en monitores 16:9 ("no queda como fullscreen").
- Modelo decidido: la **resolución base** la define el desarrollador al crear
  el proyecto; la **resolución de pantalla** la elige el usuario final del
  juego (menú en runtime), con fullscreen que **estira para llenar**.

### 10.1 Editor — resolución base al crear proyecto

- [x] `editor/project_dialog.py`: campo "Resolucion base (WxH)" (default
      `800x600`, validado) en el foco tras Calidad; diálogo más alto.
- [x] `editor/project.py`: `create_project(..., resolution=...)` escribe
      `manifest["resolution"]`; `Project.resolution` lo parsea;
      `update_config(resolution=...)` lo permite editar.

### 10.2 Runtime — aplicar la resolución base

- [x] `orm/main.py`: bloque temprano (antes de `from configs import *`) que lee
      `resolution` del manifest y fija `configs.constants.ANCHO/ALTO` y
      `configs.ANCHO/ALTO`. Todos los módulos que importan después ven el valor
      nuevo; sin refactor de los ~25 archivos.

### 10.3 Runtime — resolución del usuario final + fullscreen estirar

- [x] `orm/systems/user_prefs.py` (nuevo): `load()/save()` de
      `data/user_prefs.json` → `{"resolution": "auto", "fullscreen": false}`.
- [x] `orm/display.py`: `setup` acepta tamaño explícito (clamped al escritorio);
      flag `_stretch` (fullscreen) → `present()` escala a toda la ventana (sin
      letterbox); ventana conserva letterbox. Nuevo `get_buffer()`.
- [x] `orm/systems/screens/settings.py` (nuevo): menú "Automático", presets de
      ventana (4:3 y 16:9 clamped al desktop) y "Pantalla completa (estirar)";
      aplica en vivo y persiste.
- [x] `orm/systems/screens/titulo.py`: tecla **R** abre el menú; hint actualizado.
- [x] `orm/systems/screen_manager.py`: dibuja sobre el buffer actual
      (`_display_buffer()`) para que el cambio de display se aplique en vivo.
- [x] `orm/main.py`: lee prefs antes de `_display_setup` (prefs del jugador
      ganan); re-fetch del buffer tras los screens en modos VN y snake.

### 10.4 Criterio de aceptación

- [x] `py_compile` de todos los archivos tocados.
- [x] Resolución base 1280×720 → buffer 1280×720 (verificado headless:
      `camera`/`game_state` ven el nuevo ANCHO/ALTO).
- [x] Ventana explícita clampada al desktop; fullscreen estira (present sin
      crash, headless).
- [x] Modal de ajustes: aplicar opción guarda `user_prefs.json` y re-configura
      el display (headless).
- [x] Smokes: VN default, VN 1280×720, snake `--test` arrancan; API runtime 6/6.

### Nota

- La plantilla `snake_rpg` estaba incompleta (sin `habilidades.json`,
  `comida.json`, `enemigos.json` ni mapas) y su carpeta `utils/` tapaba el
  `orm/utils` del runtime (rompía `from utils.helpers` en `entities/food.py`).
  Ambos vacíos preexistentes se resolvieron en la **Fase 11**.

---

## Fase 11 — Alertas de proyecto inválido ✅ COMPLETADA

### Contexto

Un proyecto snake sin mapa crasheaba con `TypeError` opaco
(`posicion_inicio_static(None)`). Además, un proyecto recién creado de
cualquier plantilla ni siquiera llegaba ahí: crasheaba al importar
`from utils.helpers` (el `utils/` de la plantilla tapaba el del runtime) y la
plantilla `snake_rpg` no traía los datos mínimos (`habilidades.json` etc.).

### 11.1 Prerequisitos — plantillas usables

- [x] Eliminada la carpeta `utils/` de las plantillas `snake_rpg`,
      `visual_novel` y `blank` (su `sprite_manager.py` era idéntico al default
      del runtime, que ya resuelve `assets/` del proyecto vía
      `get_current_project()`). Arregla el shadowing que rompía
      `from utils.helpers`.
- [x] Completada la data de `snake_rpg` desde `orm/data/`: habilidades, comida,
      enemigos, items, objetos, botin, recetas, gameplay, text_screens,
      bosses, dialogos. La plantilla NO lleva mapas (para disparar la alerta).

### 11.2 Validación de mapa + alerta

- [x] `orm/levels/level_manager.py`: helpers `tiene_mapas()` y
      `mapa_con_inicio()`.
- [x] `orm/main.py`: `_validar_proyecto()` (sin mapas → "Debes crear un mapa";
      mapas sin inicio → "Debes setear el inicio del personaje") ejecutada en
      el modo snake tras el display y antes del loop; en `--test` imprime el
      mensaje y sale con código 1 sin bloquear.
- [x] `orm/main.py`: `_alerta(titulo, detalle)` — pantalla pygame que espera
      ENTER/ESC/SPACE/QUIT y sale con código 1.
- [x] `orm/game_state.py`: red de seguridad — si `nivel is None` →
      `RuntimeError("No hay mapa")` (mensaje claro).

### 11.3 Criterio de aceptación

- [x] `py_compile` de los archivos tocados.
- [x] Proyecto snake fresco de plantilla (sin mapas) → alerta "Debes crear un
      mapa", sin crash.
- [x] Con mapa + inicio (copia de `1-1`) → arranca al loop del juego.
- [x] Con mapas pero ninguno con inicio → alerta "Debes setear el inicio del
      personaje".
- [x] `--test` sin mapa → imprime el error y sale con código 1 (sin colgar).
- [x] Sin regresiones: `test_nv`, `snake --test`, proyecto VN fresco de
      plantilla y API runtime 6/6.

---

## Historial

| Fase | Estado | Fecha |
|------|--------|-------|
| Fase 0 — Arquitectura de categorías | ✅ Completada | Jul 2026 |
| Fase 1 — Runtime VN | ✅ Completada | Jul 2026 |
| Fase 2 — Panel de personajes | ✅ Completada | Jul 2026 |
| Fase 3 — Editor de diálogo | ✅ Completada | Jul 2026 |
| Fase 4 — Assets visuales | ✅ Completada | Jul 2026 |
| Fase 5 — Editor de escenas | ✅ Completada | Jul 2026 |
| Fase 6 — Minijuegos | ✅ Completada | Jul 2026 |
| Fase 7 — Audio | ✅ Completada | Jul 2026 |
| Fase 8 — Correcciones de QA (pantalla y título) | ✅ Completada | Jul 2026 |
| Fase 9 — Estabilización de tests | ⏳ Planificada | Jul 2026 |
| Fase 10 — Resolución base (editor) + resolución del jugador (runtime) | ✅ Completada | Jul 2026 |
| Fase 11 — Alertas de proyecto inválido | ✅ Completada | Jul 2026 |

## Notas
- Las Fases pueden solaparse o reordenarse según necesidad.
- Cada Fase debe dejar el sistema funcional (aunque sea mínimo) antes de pasar a la siguiente.
- Este documento se actualiza al completar o modificar cada Fase.
