import os
import sys

import pygame

sys.path.insert(0, os.path.dirname(__file__))

from configs import *

pygame.init()
os.makedirs("assets", exist_ok=True)

def _render(nombre, surf, tam):
    ruta = f"assets/{nombre}.png"
    pygame.image.save(surf, ruta)
    print(f"  {ruta} ({tam}x{tam})")

# --- PASTO (piso base) ---
s = pygame.Surface((TAMANO_CELDA, TAMANO_CELDA), pygame.SRCALPHA)
s.lock()
for py in range(TAMANO_CELDA):
    for px in range(TAMANO_CELDA):
        ruido = ((px * 7 + py * 13) % 5 - 2) * 4
        s.set_at((px, py), (40 + ruido, 95 + ruido, 30 + ruido))
s.unlock()
_render("pasto", s, TAMANO_CELDA)

# --- PASTO ESTERIL (sin decoracion, no spawn de comida) ---
s = pygame.Surface((TAMANO_CELDA, TAMANO_CELDA), pygame.SRCALPHA)
s.lock()
for py in range(TAMANO_CELDA):
    for px in range(TAMANO_CELDA):
        ruido = ((px * 11 + py * 7) % 7 - 3) * 3
        s.set_at((px, py), (30 + ruido, 70 + ruido, 25 + ruido))
s.unlock()
_render("pasto_esteril", s, TAMANO_CELDA)

# --- PARED ---
s = pygame.Surface((TAMANO_CELDA, TAMANO_CELDA), pygame.SRCALPHA)
pygame.draw.rect(s, (110, 70, 40), (0, 0, TAMANO_CELDA, TAMANO_CELDA))
pygame.draw.rect(s, (80, 50, 25), (0, 0, TAMANO_CELDA, TAMANO_CELDA), 1)
pygame.draw.line(s, (130, 85, 50), (3, 0), (3, TAMANO_CELDA), 1)
pygame.draw.line(s, (130, 85, 50), (10, 0), (10, TAMANO_CELDA), 1)
pygame.draw.line(s, (130, 85, 50), (17, 0), (17, TAMANO_CELDA), 1)
_render("pared", s, TAMANO_CELDA)

# --- ROCA (intacta) — Objeto pétreo gris con relieve y sombras ---
# Polígono irregular con facetas de luz (gris claro) y sombra (gris oscuro)
# Pequeños círculos negros simulan textura de piedra porosa
s = pygame.Surface((TAMANO_CELDA, TAMANO_CELDA), pygame.SRCALPHA)
pts = [(2,18),(1,14),(3,8),(8,3),(14,2),(18,6),(19,12),(17,18),(13,19)]
pygame.draw.polygon(s, (100, 100, 100), pts)
pygame.draw.polygon(s, (70, 70, 70), pts, 1)
pygame.draw.polygon(s, (130, 130, 130), [(5,14),(8,8),(12,6)])
pygame.draw.polygon(s, (80, 80, 80), [(4,16),(6,14),(8,12)])
pygame.draw.circle(s, (50, 50, 50), (10, 10), 2)
pygame.draw.circle(s, (40, 40, 40), (15, 14), 1)
_render("roca", s, TAMANO_CELDA)

# --- ROCA (grietada) — Misma roca con grietas en X marcando el punto de ruptura ---
# Se renderiza cuando la roca recibió 1 golpe (self.rotura == 1)
# Las líneas grises simulando fracturas indican que está lista para romperse
s2 = pygame.Surface((TAMANO_CELDA, TAMANO_CELDA), pygame.SRCALPHA)
s2.blit(s, (0, 0))
pygame.draw.line(s2, (60, 60, 60), (3, 3), (16, 16), 2)
pygame.draw.line(s2, (60, 60, 60), (16, 3), (3, 16), 2)
_render("roca_grieta", s2, TAMANO_CELDA)

# --- ROCA HIELO — Roca de tonos azulados con brillo gélido ---
# Variante de roca con paleta fría (azul cielo, blanco, azul profundo)
# Polígono más redondeado que la roca normal, con reflejos en las facetas superiores
s = pygame.Surface((TAMANO_CELDA, TAMANO_CELDA), pygame.SRCALPHA)
pts = [(2,18),(1,12),(4,5),(9,2),(15,3),(18,8),(19,14),(16,19),(10,19)]
pygame.draw.polygon(s, (150, 200, 240), pts)
pygame.draw.polygon(s, (100, 150, 200), pts, 1)
pygame.draw.polygon(s, (200, 230, 255), [(6,12),(9,7),(13,6)])
pygame.draw.polygon(s, (180, 215, 245), [(3,14),(5,12),(7,10)])
_render("roca_hielo", s, TAMANO_CELDA)

# --- ROCA NIEVE — Roca gris con casquete de nieve en la parte superior ---
# Similar a la roca normal pero con un polígono blanco/azulado simulando nieve acumulada
# Cubre los píxeles superiores (y=1..12) dejando visible la base gris inferior
s = pygame.Surface((TAMANO_CELDA, TAMANO_CELDA), pygame.SRCALPHA)
pts = [(2,18),(1,14),(3,8),(8,3),(14,2),(18,6),(19,12),(17,18),(13,19)]
pygame.draw.polygon(s, (100, 100, 100), pts)
pygame.draw.polygon(s, (70, 70, 70), pts, 1)
pygame.draw.polygon(s, (130, 130, 130), [(5,14),(8,8),(12,6)])
pygame.draw.polygon(s, (220, 230, 240), [(2,8),(5,2),(10,1),(14,4),(4,12)])
pygame.draw.polygon(s, (240, 245, 255), [(3,5),(7,2),(11,3)])
_render("roca_nieve", s, TAMANO_CELDA)

# --- BLOQUE ACERO (montaña) ---
s = pygame.Surface((TAMANO_CELDA, TAMANO_CELDA), pygame.SRCALPHA)
pts_m = [(0,19),(0,12),(3,6),(7,2),(10,0),(13,2),(17,6),(20,12),(20,19)]
pygame.draw.polygon(s, (60, 65, 70), pts_m)
pygame.draw.polygon(s, (120, 125, 130), [(14,12),(16,6),(10,3),(7,7),(10,12)])
pygame.draw.polygon(s, (60, 55, 50), [(0,18),(4,14),(8,16),(4,19)])
pygame.draw.line(s, (50, 50, 55), (5, 12), (12, 6), 1)
pygame.draw.line(s, (50, 50, 55), (12, 6), (16, 10), 1)
_render("bloque_acero", s, TAMANO_CELDA)

# --- ARBOL ---
s = pygame.Surface((TAMANO_CELDA, TAMANO_CELDA), pygame.SRCALPHA)
pygame.draw.rect(s, (80, 50, 30), (8, 8, 4, 12))
pygame.draw.circle(s, (20, 80, 20), (10, 6), 6)
pygame.draw.circle(s, (25, 90, 25), (10, 4), 5)
pygame.draw.circle(s, (30, 100, 30), (7, 7), 4)
pygame.draw.circle(s, (30, 100, 30), (13, 7), 4)
pygame.draw.circle(s, (15, 60, 15), (10, 8), 5)
_render("arbol", s, TAMANO_CELDA)

# --- HIERBA ALTA (3 variantes) ---
for v in range(3):
    s = pygame.Surface((TAMANO_CELDA, TAMANO_CELDA), pygame.SRCALPHA)
    if v == 0:
        pts_g = [(10,18),(8,12),(6,4),(10,5),(12,12)]
    elif v == 1:
        pts_g = [(8,18),(5,10),(4,2),(8,4),(10,10)]
    else:
        pts_g = [(12,18),(14,10),(16,3),(12,4),(10,10)]
    pygame.draw.polygon(s, (40, 120, 30), pts_g)
    pygame.draw.circle(s, (60, 160, 40), (pts_g[0][0], pts_g[0][1]), 2)
    pygame.draw.circle(s, (60, 160, 40), (pts_g[2][0], pts_g[2][1]), 2)
    _render(f"hierba_{v}", s, TAMANO_CELDA)

# --- GATE ---
s = pygame.Surface((TAMANO_CELDA, TAMANO_CELDA))
pygame.draw.rect(s, (50, 50, 150), (2, 2, 16, 16))
pygame.draw.rect(s, (80, 80, 200), (2, 2, 16, 16), 1)
pygame.draw.circle(s, (100, 100, 255), (10, 10), 5)
pygame.draw.circle(s, (60, 60, 200), (10, 10), 5, 1)
_render("gate", s, TAMANO_CELDA)

# --- FOOD NORMAL (manzana) ---
s = pygame.Surface((TAMANO_CELDA, TAMANO_CELDA), pygame.SRCALPHA)
pygame.draw.circle(s, (200, 40, 40), (10, 11), 6)
pygame.draw.circle(s, (160, 20, 20), (10, 11), 6, 1)
pygame.draw.circle(s, (230, 100, 100), (8, 9), 2)
pygame.draw.line(s, (60, 60, 40), (10, 5), (10, 3), 1)
pygame.draw.line(s, (60, 60, 40), (10, 3), (12, 2), 1)
_render("comida_normal", s, TAMANO_CELDA)

# --- FOOD MANA (raton morado) ---
s = pygame.Surface((TAMANO_CELDA, TAMANO_CELDA), pygame.SRCALPHA)
pygame.draw.ellipse(s, (120, 60, 160), (4, 8, 12, 8))
pygame.draw.circle(s, (120, 60, 160), (8, 8), 4)
pygame.draw.circle(s, (140, 80, 180), (8, 8), 4, 1)
pygame.draw.circle(s, (180, 140, 220), (6, 7), 1)
pygame.draw.circle(s, (180, 140, 220), (10, 7), 1)
pygame.draw.circle(s, NEGRO, (6, 7), 1)
pygame.draw.circle(s, NEGRO, (10, 7), 1)
pygame.draw.circle(s, (180, 120, 200), (8, 9), 1)
pygame.draw.line(s, (120, 60, 160), (5, 12), (3, 16), 1)
pygame.draw.line(s, (120, 60, 160), (11, 12), (13, 16), 1)
_render("comida_mana", s, TAMANO_CELDA)

# --- FOOD DORADA (manzana dorada) ---
s = pygame.Surface((TAMANO_CELDA, TAMANO_CELDA), pygame.SRCALPHA)
pygame.draw.circle(s, (220, 190, 30), (10, 11), 6)
pygame.draw.circle(s, (180, 150, 10), (10, 11), 6, 1)
pygame.draw.circle(s, (255, 230, 100), (8, 9), 2)
pygame.draw.line(s, (100, 80, 20), (10, 5), (10, 3), 1)
pygame.draw.line(s, (100, 80, 20), (10, 3), (12, 2), 1)
_render("comida_dorada", s, TAMANO_CELDA)

# --- ENEMIGO MELEE (casco vikingo) — Guerrero de carga cuerpo a cuerpo ---
# Casco metálico trapezoidal con visera, dos cuernos laterales y ojos blancos
# Se mueve en patrones lineales (horizontal/vertical) y ataca al contacto
# Al aturdirse (self.aturdido) el sprite se renderiza en gris (linea 66-80 de base.py)
s = pygame.Surface((TAMANO_CELDA, TAMANO_CELDA), pygame.SRCALPHA)
pygame.draw.polygon(s, (140, 130, 120), [(2,6),(10,2),(18,6),(16,8),(4,8)])
pygame.draw.polygon(s, (100, 90, 80), [(2,6),(10,2),(18,6),(16,8),(4,8)], 1)
pygame.draw.rect(s, (80, 70, 60), (6, 8, 8, 6))
pygame.draw.line(s, (80, 70, 60), (5, 5), (2, 0), 2)
pygame.draw.line(s, (80, 70, 60), (15, 5), (18, 0), 2)
pygame.draw.circle(s, BLANCO, (8, 9), 2)
pygame.draw.circle(s, BLANCO, (12, 9), 2)
pygame.draw.circle(s, NEGRO, (8, 9), 1)
pygame.draw.circle(s, NEGRO, (12, 9), 1)
_render("enemigo_melee", s, TAMANO_CELDA)

# --- ENEMIGO SHOOTER (casco circular) — Artillero de proyectiles ---
# Casco redondo con visera, dos pequeños cuernos y ojos blancos
# Dispara proyectiles a distancia (ver shooter.py linea 90-100)
# Misma paleta que el melee para mantener coherencia visual entre enemigos
s = pygame.Surface((TAMANO_CELDA, TAMANO_CELDA), pygame.SRCALPHA)
pygame.draw.circle(s, (140, 130, 120), (10, 8), 7)
pygame.draw.circle(s, (100, 90, 80), (10, 8), 7, 1)
pygame.draw.rect(s, (80, 70, 60), (6, 10, 8, 6))
pygame.draw.line(s, (80, 70, 60), (3, 3), (1, 0), 2)
pygame.draw.line(s, (80, 70, 60), (17, 3), (19, 0), 2)
pygame.draw.circle(s, BLANCO, (8, 9), 2)
pygame.draw.circle(s, BLANCO, (12, 9), 2)
pygame.draw.circle(s, NEGRO, (8, 9), 1)
pygame.draw.circle(s, NEGRO, (12, 9), 1)
_render("enemigo_shooter", s, TAMANO_CELDA)

# --- HIERBA (decoracion del suelo, 4 variantes) ---
for v in range(4):
    s = pygame.Surface((TAMANO_CELDA, TAMANO_CELDA), pygame.SRCALPHA)
    if v == 0:
        col = (255, 180, 200)
        pygame.draw.circle(s, col, (10, 10), 2)
    elif v == 1:
        col = (15, 55, 12)
        pygame.draw.circle(s, col, (10, 10), 5)
        pygame.draw.circle(s, (8, 35, 6), (10, 10), 3)
    elif v == 2:
        pygame.draw.line(s, (40, 80, 30), (7, 14), (7, 6), 1)
        pygame.draw.circle(s, (20, 70, 15), (7, 6), 3)
    else:
        col = (255, 220, 120)
        pygame.draw.circle(s, col, (10, 10), 2)
    _render(f"deco_{v}", s, TAMANO_CELDA)

pygame.quit()
print("\nTodos los sprites generados en assets/")
