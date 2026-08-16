import pygame
from configs import ALTO, ANCHO
from systems.ui.components.base import dibujar_marco_madera, dibujar_runas, panel_tallado


class PanelApartado:
    """Base para un panel de apartado del menú."""

    def __init__(self, fuente, fuente_pequena):
        self.fuente = fuente
        self.fuente_pequena = fuente_pequena

    def item_count(self, estado):
        """Cantidad de filas seleccionables de este apartado."""
        return 0

    def dibujar(self, pantalla, estado, area):
        raise NotImplementedError


class PanelHabilidades(PanelApartado):
    """Apartado Habilidades — mismo render que el menú original."""

    def item_count(self, estado):
        return len(estado.habilidades.inventario)

    def dibujar(self, pantalla, estado, area):
        habilidades = estado.habilidades
        lista = habilidades.inventario
        if not lista:
            txt = self.fuente.render("No tienes habilidades desbloqueadas", True, (120, 120, 120))
            txt_rect = txt.get_rect(center=(area.centerx, area.centery))
            pantalla.blit(txt, txt_rect)
            return

        sel = estado.menu.seleccion
        paso = 62
        for i, hid in enumerate(lista):
            hab = habilidades.habilidades[hid]
            es_equipada = (hid == habilidades.habilidad_equipada)
            es_seleccion = (i == sel)
            y_pos = area.top + i * paso

            item_rect = pygame.Rect(area.left, y_pos, area.width, 54)
            if es_equipada:
                panel_tallado(pantalla, item_rect, (35, 55, 25), (180, 150, 70))
            elif es_seleccion:
                panel_tallado(pantalla, item_rect, (40, 60, 30), (120, 150, 90))
            else:
                panel_tallado(pantalla, item_rect, (25, 42, 20), (60, 70, 50))

            if es_equipada:
                pygame.draw.polygon(pantalla, (200, 170, 80), [
                    (area.left - 6, y_pos + 27 - 6),
                    (area.left - 6, y_pos + 27 + 6),
                    (area.left, y_pos + 27)
                ])

            if es_seleccion and not es_equipada:
                pygame.draw.polygon(pantalla, (140, 200, 120), [
                    (area.left + area.width + 6, y_pos + 27 - 6),
                    (area.left + area.width + 6, y_pos + 27 + 6),
                    (area.left + area.width, y_pos + 27)
                ])

            nom_color = (220, 200, 130) if es_equipada else (180, 200, 160)
            texto_nombre = self.fuente.render(hab['nombre'], True, nom_color)
            pantalla.blit(texto_nombre, (area.left + 10, y_pos + 4))

            texto_desc = self.fuente_pequena.render(hab['descripcion'], True, (140, 150, 130))
            pantalla.blit(texto_desc, (area.left + 10, y_pos + 28))

            pp_x = area.left + area.width - 110
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

            if i < len(lista) - 1:
                sep_y = y_pos + paso - 2
                pygame.draw.line(pantalla, (40, 55, 35), (area.left + 20, sep_y), (area.left + area.width - 20, sep_y), 1)


class PanelItems(PanelApartado):
    """Apartado Items — placeholder de Fase 2."""

    def dibujar(self, pantalla, estado, area):
        txt = self.fuente.render("Items", True, (200, 190, 140))
        txt_rect = txt.get_rect(center=(area.centerx, area.centery - 20))
        pantalla.blit(txt, txt_rect)
        sub = self.fuente_pequena.render("Proximamente en Fase 2", True, (120, 120, 120))
        sub_rect = sub.get_rect(center=(area.centerx, area.centery + 10))
        pantalla.blit(sub, sub_rect)


class PanelEquipo(PanelApartado):
    """Apartado Equipo — placeholder de Fase 3."""

    def dibujar(self, pantalla, estado, area):
        txt = self.fuente.render("Equipo", True, (200, 190, 140))
        txt_rect = txt.get_rect(center=(area.centerx, area.centery - 20))
        pantalla.blit(txt, txt_rect)
        sub = self.fuente_pequena.render("Proximamente en Fase 3", True, (120, 120, 120))
        sub_rect = sub.get_rect(center=(area.centerx, area.centery + 10))
        pantalla.blit(sub, sub_rect)


# Registro de paneles por id de apartado (data/inventario.json)
PANELES_APARTADO = {
    "habilidades": PanelHabilidades,
    "items": PanelItems,
    "equipo": PanelEquipo,
}
