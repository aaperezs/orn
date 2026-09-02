"""Acción remove_sprite: elimina un tile y sus entidades."""

from systems.action_registry import GameAction, register_action

TAMANO_CELDA = 32


@register_action("remove_sprite")
class RemoveSprite(GameAction):
    def execute(self, ctx, params):
        x, y, z = ctx.position
        gx = x // TAMANO_CELDA
        gy = y // TAMANO_CELDA
        if hasattr(ctx.state, "remove_tile_sprite"):
            ctx.state.remove_tile_sprite(gx, gy, z)
        if ctx.manager:
            ctx.manager.remover_entidades_en(ctx.state, gx, gy)
        return False
