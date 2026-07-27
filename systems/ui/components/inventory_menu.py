import pygame
from configs import ALTO, ANCHO
from systems.ui.components.base import dibujar_marco_madera, dibujar_runas, panel_tallado


class InventoryMenu:
    def __init__(self, fuente, fuente_grande, fuente_pequena):
        self.fuente = fuente
        self.fuente_grande = fuente_grande
        self.fuente_pequena = fuente_pequena

    def draw(self, pantalla, habilidades):
        overlay = pygame.Surface((ANCHO, ALTO))
        overlay.set_alpha(200)
        overlay.fill((10, 30, 8))
        pantalla.blit(overlay, (0, 0))

        m = 30
        w, h = ANCHO - 2*m, ALTO - 2*m

        marco_ext = pygame.Rect(m, m, w, h)
        dibujar_marco_madera(pantalla, marco_ext, (60, 40, 20), (80, 55, 30))

        int_rect = marco_ext.inflate(-12, -12)
        panel_tallado(pantalla, int_rect, (15, 38, 12), (35, 60, 25))

        col_runa = (100, 75, 40)
        dibujar_runas(pantalla, int_rect.left + 15, int_rect.top + 15, col_runa)
        dibujar_runas(pantalla, int_rect.right - 15, int_rect.top + 15, col_runa)
        dibujar_runas(pantalla, int_rect.left + 15, int_rect.bottom - 15, col_runa)
        dibujar_runas(pantalla, int_rect.right - 15, int_rect.bottom - 15, col_runa)

        tit_rect = pygame.Rect(int_rect.centerx - 180, int_rect.top + 8, 360, 36)
        panel_tallado(pantalla, tit_rect, (80, 55, 30), (120, 80, 45))
        titulo = self.fuente_grande.render("INVENTARIO", True, (220, 190, 120))
        tit_rect_txt = titulo.get_rect(center=tit_rect.center)
        pantalla.blit(titulo, tit_rect_txt)

        if habilidades.habilidad_equipada:
            hab = habilidades.habilidades[habilidades.habilidad_equipada]
            eq_rect = pygame.Rect(int_rect.centerx - 140, int_rect.top + 50, 280, 22)
            panel_tallado(pantalla, eq_rect, col_runa, (120, 80, 45))
            eq_texto = self.fuente_pequena.render(f"Equipado: {hab['nombre']}", True, (200, 180, 100))
            eq_txt_rect = eq_texto.get_rect(center=eq_rect.center)
            pantalla.blit(eq_texto, eq_txt_rect)

        inst = self.fuente_pequena.render("TAB: Cambiar   ESC: Cerrar", True, (100, 130, 80))
        inst_rect = inst.get_rect(center=(ANCHO//2, int_rect.bottom - 10))
        pantalla.blit(inst, inst_rect)

        habilidades_lista = habilidades.inventario
        if not habilidades_lista:
            txt = self.fuente.render("No tienes habilidades desbloqueadas", True, (120, 120, 120))
            txt_rect = txt.get_rect(center=(ANCHO//2, ALTO//2))
            pantalla.blit(txt, txt_rect)
            return

        panel_x = int_rect.left + 15
        panel_w = int_rect.width - 30
        y0 = int_rect.top + 78
        paso = 62

        for i, hid in enumerate(habilidades_lista):
            hab = habilidades.habilidades[hid]
            es_equipada = (hid == habilidades.habilidad_equipada)
            y_pos = y0 + i * paso

            item_rect = pygame.Rect(panel_x, y_pos, panel_w, 54)
            if es_equipada:
                panel_tallado(pantalla, item_rect, (35, 55, 25), (180, 150, 70))
            else:
                panel_tallado(pantalla, item_rect, (25, 42, 20), (60, 70, 50))

            if es_equipada:
                pygame.draw.polygon(pantalla, (200, 170, 80), [
                    (panel_x - 6, y_pos + 27 - 6),
                    (panel_x - 6, y_pos + 27 + 6),
                    (panel_x, y_pos + 27)
                ])

            nom_color = (220, 200, 130) if es_equipada else (180, 200, 160)
            texto_nombre = self.fuente.render(hab['nombre'], True, nom_color)
            pantalla.blit(texto_nombre, (panel_x + 10, y_pos + 4))

            texto_desc = self.fuente_pequena.render(hab['descripcion'], True, (140, 150, 130))
            pantalla.blit(texto_desc, (panel_x + 10, y_pos + 28))

            pp_x = panel_x + panel_w - 110
            pp_y = y_pos + 6
            pp_w = 100
            pp_h = 10

            pygame.draw.rect(pantalla, (20, 30, 15), (pp_x, pp_y, pp_w, pp_h))
            pygame.draw.rect(pantalla, (50, 60, 40), (pp_x, pp_y, pp_w, pp_h), 1)

            if hab['pp_max'] > 0:
                fill = int((hab['pp_actual'] / hab['pp_max']) * pp_w)
                if hab['pp_actual'] > 0:
                    color_pp = (100, 180, 80) if hab['pp_actual'] > 1 else (200, 120, 40)
                    pygame.draw.rect(pantalla, color_pp, (pp_x + 1, pp_y + 1, fill - 1, pp_h - 2))

            pp_txt = self.fuente_pequena.render(f"PP {hab['pp_actual']}/{hab['pp_max']}", True, (160, 180, 140))
            pantalla.blit(pp_txt, (pp_x + pp_w + 6, pp_y - 1))

            if i < len(habilidades_lista) - 1:
                sep_y = y_pos + paso - 2
                pygame.draw.line(pantalla, (40, 55, 35), (panel_x + 20, sep_y), (panel_x + panel_w - 20, sep_y), 1)
