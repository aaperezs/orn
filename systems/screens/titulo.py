import os
import pygame

from project_paths import assets_dir
from .base import BaseScreen


class TituloScreen(BaseScreen):
    def __init__(self, config=None, title_data=None, display_size=None):
        super().__init__(config)
        self.title_data = title_data or {}
        self.display_size = display_size or (800, 600)
        self._bg = None
        self._load_bg()

    def _load_bg(self):
        bg_id = self.title_data.get("fondo", "")
        if bg_id:
            for ext in (".png", ".jpg", ".jpeg"):
                path = assets_dir(f"{bg_id}{ext}")
                if os.path.exists(path):
                    img = pygame.image.load(path).convert()
                    self._bg = pygame.transform.scale(img, self.display_size)
                    return
        self._bg = None

    def draw(self, surface):
        dw, dh = self.display_size
        if self._bg:
            surface.blit(self._bg, (0, 0))
        else:
            surface.fill((10, 12, 16))
        titulo = self.title_data.get("titulo", "")
        subtitulo = self.title_data.get("subtitulo", "")
        if titulo:
            font_l = pygame.font.SysFont("Georgia", 48, bold=True)
            ts = font_l.render(titulo, True, (220, 200, 160))
            surface.blit(ts, ((dw - ts.get_width()) // 2, dh // 3 - 20))
        if subtitulo:
            font_s = pygame.font.SysFont("Georgia", 22)
            ss = font_s.render(subtitulo, True, (180, 180, 190))
            surface.blit(ss, ((dw - ss.get_width()) // 2, dh // 2 + 10))
        hint = pygame.font.SysFont("Arial", 16).render(
            "[ENTER] continuar   [R] resolucion", True, (120, 130, 140)
        )
        surface.blit(hint, ((dw - hint.get_width()) // 2, dh - 60))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                return True
            if event.key in (pygame.K_r, pygame.K_o):
                self._abrir_ajustes()
        return False

    def _abrir_ajustes(self):
        from .settings import SettingsScreen
        SettingsScreen(self.config, self.display_size).run()
