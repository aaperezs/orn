"""Acción close_dialog: cierra el diálogo activo."""

from systems.action_registry import GameAction, register_action


@register_action("close_dialog")
class CloseDialog(GameAction):
    def execute(self, ctx, params):
        if ctx.dialog_service:
            ctx.dialog_service.activo = False
            ctx.dialog_service.terminado = True
            ctx.dialog_service.al_terminar = None
        ctx.state.mostrando_opciones = False
        ctx.state.opciones = []
        ctx.manager._bloqueo_por = None
        return True
