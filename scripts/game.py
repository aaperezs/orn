from orm.runtime import game, renderer, input
from orm.runtime.camera import Camera

# ── Estado del juego ─────────────────────────────────────

player_x = 100
player_y = 100
player_size = 20
speed = 3


# ── Hooks ────────────────────────────────────────────────

@game.init
def init():
    global camera
    camera = Camera(800, 600)
    camera.snap_to(player_x, player_y)


@game.update
def update():
    global player_x, player_y

    dx = 0
    dy = 0
    if input.is_key_down("left"):
        dx = -speed
    if input.is_key_down("right"):
        dx = speed
    if input.is_key_down("up"):
        dy = -speed
    if input.is_key_down("down"):
        dy = speed

    player_x += dx
    player_y += dy
    camera.follow(player_x, player_y)


@game.draw
def draw(screen):
    screen.fill((30, 40, 50))
    sx, sy = camera.apply((player_x, player_y))
    renderer.draw_rect_filled(screen, (100, 200, 255), (sx, sy, player_size, player_size))
    renderer.draw_text(screen, "Cururo Runtime Demo", 10, 10, color=(200, 200, 220), size=20)
    renderer.draw_text(screen, "Flechas para mover | ESC para salir", 10, 36, color=(150, 160, 170), size=14)


@game.input
def handle_input(event):
    import pygame
    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        return "quit"
