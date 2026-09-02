"""Acción save_game: guarda el juego."""

from systems.action_registry import GameAction, register_action


@register_action("save_game")
class SaveGame(GameAction):
    def execute(self, ctx, params):
        slot = int(params.get("slot", 1))
        dev = params.get("dev", False)
        if isinstance(dev, str):
            dev = dev.lower() in ("true", "1", "si")
        if hasattr(ctx.state, "save_system"):
            ok, msg = ctx.state.save_system.guardar_slot(slot, dev=dev)
            ctx.state.mensaje_temporal = msg
            ctx.state.tiempo_mensaje = 90
        return False
