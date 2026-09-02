"""Acciones migradas automaticamente desde stack_manager._ejecutar_accion.

NO EDITAR MANUALMENTE - generado por scripts/migrate_trivial_actions.py
"""

from systems.action_registry import GameAction, register_action


TAMANO_CELDA = 32  # from configs.constants

@register_action("clear_flag")
class ClearFlag(GameAction):
    def execute(self, ctx, params):
        flag = params.get("flag", "")
        if flag and hasattr(ctx.state, "flags"):
            ctx.state.flags.set(flag, False)
        return False
