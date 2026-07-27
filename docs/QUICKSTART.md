# Cururo Platform — Quickstart

Crear un videojuego desde cero usando Cururo Editor y la Runtime API.

## 1. Crear un proyecto

**Desde Cururo Editor:**
1. Ejecutar `python editor/main.py`
2. En el diálogo de inicio, seleccionar **+ Nuevo Proyecto**
3. Ingresar nombre (ej: "Mi Aventura")
4. Seleccionar plantilla **"Mi Juego"** (TAB para cambiar)
5. Click **Crear** o Enter

**O desde consola:**
```bash
python -c "
from editor.project import create_project
create_project('empty_rpg', 'Mi Aventura', 'ruta/a/mi_aventura')
"
```

## 2. Estructura del proyecto

```
mi_aventura/
├── cururo.json          # Manifiesto del proyecto
├── assets/              # Sprites PNG
├── data/
│   ├── elementos.json   # Definiciones de tiles/elementos
│   ├── behaviors.json   # Comportamientos disponibles
│   └── animations.json  # Definiciones de animaciones
├── levels/
│   ├── mapas/           # Mapas del juego (JSON v2)
│   └── mapas_stacks/    # Eventos por tile
└── scripts/
    └── game.py          # Lógica del juego (API Runtime)
```

## 3. Flujo de trabajo

### a) Crear sprites
1. Abrir Cururo Editor
2. **Arte > Sprites (Ctrl+1)**
3. Dibujar sprites con lápiz, borrador, balde
4. Guardar como PNG → aparecen en `assets/`

### b) Definir elementos
1. **Herramientas > Elementos**
2. Crear elemento: asignar sprite + comportamiento (bloqueante, food, decorativo, etc.)
3. Configurar propiedades del behavior

### c) Crear mapa
1. **Arte > Mapas (Ctrl+2)**
2. Nuevo mapa, definir tamaño
3. Pintar elementos en la grilla
4. Agregar capas Z para profundidad
5. Asignar eventos (stacks) a tiles

### d) Programar lógica
1. **Arte > Scripts**
2. Editar `game.py` usando la [API Runtime](API_RUNTIME.md)
3. Los hooks `@game.init`, `@game.update`, `@game.draw`, `@game.input` controlan el juego

### e) Probar
1. **Ejecutar > Iniciar juego (Ctrl+R)**
2. El runtime carga `scripts/game.py` + `data/` + `levels/`

## 4. Ejemplo: Pantalla de título

En `scripts/game.py`:

```python
from orm.runtime import game, renderer, input

show_title = True

@game.init
def init():
    pass

@game.update
def update():
    global show_title
    if show_title and input.is_key_just_pressed("return"):
        show_title = False

@game.draw
def draw(screen):
    if show_title:
        screen.fill((20, 25, 35))
        renderer.draw_text_centered(screen, "MI AVENTURA",
                                    400, 200, size=36, color=(220, 200, 150))
        renderer.draw_text_centered(screen, "Presiona Enter",
                                    400, 300, size=18, color=(150, 160, 170))
    else:
        screen.fill((30, 40, 50))

@game.input
def handle_input(event):
    import pygame
    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        return "quit"
```

## 5. Próximos pasos

- Leer la [Referencia completa de la API Runtime](API_RUNTIME.md)
- Explorar los behaviors en el editor (Herramientas > Comportamientos)
- Usar `run_script` en eventos de mapa para lógica avanzada
- Ver el proyecto **Orm** como ejemplo completo de juego
