# Cururo Runtime API

La API Runtime permite crear juegos desde scripts Python sin modificar el motor.
Todo juego se define en `scripts/game.py` dentro del proyecto.

## Ciclo de vida

El runtime ejecuta hooks en este orden cada frame:

```
inicialización: @game.init (una vez)
cada frame:     @game.input → @game.update → @game.draw
```

## Decoradores de hooks

Importar el singleton `game` y decorar funciones:

```python
from orm.runtime import game

@game.init
def init():
    pass  # Una vez al inicio

@game.update
def update():
    pass  # Cada frame, después de input

@game.draw
def draw(screen):
    pass  # Cada frame, para dibujar

@game.input
def handle_input(event):
    pass  # Cada evento pygame
```

### Valores de retorno de `@game.input`
- `"quit"` — detiene el bucle del juego
- Cualquier otro valor se ignora

---

## Renderer (`orm.runtime.renderer`)

```python
from orm.runtime import renderer
```

### Sprites

| Función | Descripción |
|---------|-------------|
| `load_sprite(sprite_id)` | Carga un sprite desde `assets/{id}.png`. Cachea. Devuelve `pygame.Surface` o `None` |
| `sprite_size(sprite_id)` | `(ancho, alto)` del sprite |
| `draw_sprite(surface, sprite_id, x, y)` | Dibuja sprite en posición |
| `draw_sprite_scaled(surface, sprite_id, x, y, w, h)` | Dibuja sprite escalado |
| `clear_sprite_cache()` | Limpia caché (útil al recargar assets) |
| `set_assets_dir(path)` | Cambia directorio de assets (por defecto `assets/`) |

### Primitivas

| Función | Descripción |
|---------|-------------|
| `draw_rect(surface, color, rect, width=0)` | Rectángulo (width=0: filled) |
| `draw_rect_filled(surface, color, rect)` | Rectángulo relleno |
| `draw_circle(surface, color, center, radius, width=0)` | Círculo |
| `draw_line(surface, color, start, end, width=1)` | Línea |

### Texto

| Función | Descripción |
|---------|-------------|
| `draw_text(surface, text, x, y, color, size, font_name)` | Texto en posición |
| `draw_text_centered(surface, text, cx, cy, color, size, font_name)` | Texto centrado |
| `text_width(text, size, font_name)` | Ancho del texto en píxeles |
| `text_height(size, font_name)` | Alto de línea |

---

## Input (`orm.runtime.input`)

```python
from orm.runtime import input
```

### Teclado

| Función | Descripción |
|---------|-------------|
| `is_key_down("left")` | Tecla está siendo presionada ahora |
| `is_key_just_pressed("space")` | Tecla se presionó este frame |
| `is_key_just_released("a")` | Tecla se soltó este frame |

**Nombres de teclas soportados:** `up`, `down`, `left`, `right`, `space`, `return`, `escape`, `tab`, `a`-`z`, `0`-`9`, `lshift`, `rshift`, `lctrl`, `rctrl`, `lalt`, `ralt`

### Mouse

| Función | Descripción |
|---------|-------------|
| `get_mouse_pos()` | `(x, y)` actual |
| `get_mouse_buttons()` | `(btn1, btn2, btn3)` tuple |
| `is_mouse_button_down(button=1)` | Botón presionado |

### Interno (usado por el motor)

| Función | Descripción |
|---------|-------------|
| `handle_event(event)` | Procesa evento pygame para estado just_pressed |
| `clear_frame()` | Limpia estado just_pressed/released (llamar 1x por frame) |

---

## Cámara (`orm.runtime.camera.Camera`)

```python
from orm.runtime.camera import Camera

cam = Camera(ancho, alto)
```

| Método | Descripción |
|--------|-------------|
| `follow(x, y, center=True)` | Seguimiento suave (smoothing 0.1) |
| `snap_to(x, y, center=True)` | Posición instantánea |
| `apply(rect)` | Transforma coordenadas absolutas → relativas a cámara |
| `apply_x(x)` | Transforma X |
| `apply_y(y)` | Transforma Y |
| `set_pos(x, y)` | Posición directa |
| `set_bounds(min_x, min_y, max_x, max_y)` | Limita movimiento de cámara |
| `get_offset()` | `(int(x), int(y))` offset actual |
| `is_visible(rect)` | Verifica si un rect es visible en la viewport |
| `reset()` | Reinicia posición y bounds |
| `smoothing` | Factor de suavizado (0.0–1.0), por defecto 0.1 |

**Uso típico:**

```python
camera = Camera(800, 600)

@game.update
def update():
    camera.follow(jugador.x, jugador.y)

@game.draw
def draw(screen):
    sx, sy = camera.apply((jugador.x, jugador.y))
    renderer.draw_sprite(screen, "hero", sx, sy)
```

---

## Vec2 (`orm.runtime.vec2.Vec2`)

```python
from orm.runtime import Vec2

v = Vec2(10, 20)
v2 = Vec2(5, 5)
s = v + v2    # Vec2(15, 25)
d = v - v2    # Vec2(5, 15)
m = v * 2     # Vec2(20, 40)
t = v.as_tuple()  # (10, 20)
```

---

## Loader (`orm.runtime.loader`)

```python
from orm.runtime import load_script

mod = load_script(project_root, "game")  # Carga scripts/game.py
```

Usado internamente por el motor. Los scripts importan directamente los módulos que necesitan.

---

## Behaviors y `run_script`

Los behaviors (comportamientos) se definen en `data/behaviors.json` y se editan desde
Cururo Editor > Herramientas > Comportamientos.

### Eventos y capas Z

Los eventos (stacks) se procesan **independientemente de la capa Z** del jugador. Si hay un
stack en una celda, se dispara sin importar si está en Z=0, Z=1, Z=2, etc. No es necesario
que el jugador esté en la misma Z que el evento.

### Acción `run_script` en eventos

Los stacks de mapa pueden ejecutar funciones Python del proyecto:

```json
{
  "trigger": "contact",
  "acciones": [{
    "tipo": "run_script",
    "params": {"function_name": "mi_funcion", "args": "arg1, arg2"}
  }]
}
```

La función se busca en los módulos cargados del proyecto (`game`, `scripts.game`).

### GenericEntity

Si un behavior usa `class_path: "entities.generic.GenericEntity"`, las entidades
se crean con propiedades arbitrarias desde el editor de elementos. Además:

- `on_update` en properties: nombre de función en el script que se llama cada frame
  con `(entidad, estado)` como argumentos

---

## Ejemplo mínimo

```python
from orm.runtime import game, renderer, input
from orm.runtime.camera import Camera

x, y = 100, 100
speed = 3

@game.init
def init():
    global cam
    cam = Camera(800, 600)
    cam.snap_to(x, y)

@game.update
def update():
    global x, y
    if input.is_key_down("left"):  x -= speed
    if input.is_key_down("right"): x += speed
    if input.is_key_down("up"):    y -= speed
    if input.is_key_down("down"):  y += speed
    cam.follow(x, y)

@game.draw
def draw(screen):
    screen.fill((30, 40, 50))
    sx, sy = cam.apply((x, y))
    renderer.draw_rect_filled(screen, (100, 200, 255), (sx, sy, 20, 20))

@game.input
def handle_input(event):
    import pygame
    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        return "quit"
```
