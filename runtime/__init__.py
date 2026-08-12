try:
    from orm.runtime.api import game, Game
    from orm.runtime.vec2 import Vec2
    from orm.runtime import renderer, input, camera
    from orm.runtime.loader import load_script
except ImportError:
    from runtime.api import game, Game
    from runtime.vec2 import Vec2
    from runtime import renderer, input, camera
    from runtime.loader import load_script

__all__ = ["game", "Game", "Vec2", "renderer", "input", "camera", "load_script"]
