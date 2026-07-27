import sys

import pygame

from .screens.cururo_games import CururoGamesScreen
from .screens.imagen import ImagenScreen
from .screens.text import TextScreen

SCREEN_REGISTRY = {
    "cururo_games": CururoGamesScreen,
}


def registrar_pantalla(screen_id, cls):
    SCREEN_REGISTRY[screen_id] = cls


class ScreenManager:
    def __init__(self, display_surf, screens_cfg):
        self.display = display_surf
        self.items = screens_cfg.get("items", ["cururo_games"])
        self.screen_configs = screens_cfg.get("config", {})
        self.enabled = screens_cfg.get("enabled", True)

    def run(self):
        if not self.enabled:
            return
        clock = pygame.time.Clock()
        for screen_id in self.items:
            cfg = self.screen_configs.get(screen_id, {})
            if not cfg.get("enabled", True):
                continue
            screen = self._crear(screen_id, cfg)
            if screen is None:
                continue
            self._ejecutar(screen, clock)

    def _crear(self, screen_id, cfg):
        cls = SCREEN_REGISTRY.get(screen_id)
        if cls:
            return cls(cfg)
        try:
            texto = TextScreen(screen_id, cfg)
            if texto._lineas:
                return texto
        except Exception:
            pass
        try:
            return ImagenScreen(screen_id, cfg)
        except Exception:
            return None

    def _ejecutar(self, screen, clock):
        done = False
        while not done:
            dt = clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if screen.handle_event(event):
                    done = True
            if screen.update(dt):
                done = True
            screen.draw(self.display)
            pygame.display.flip()
