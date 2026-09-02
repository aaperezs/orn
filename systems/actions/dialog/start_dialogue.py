"""Acción start_dialogue: inicia un diálogo con un personaje."""

from systems.action_registry import GameAction, register_action


@register_action("start_dialogue")
class StartDialogue(GameAction):
    def execute(self, ctx, params):
        dialogo_id = params.get("dialog", "") or params.get("dialogo_id", "")
        if "/" in dialogo_id and ctx.dialog_service:
            personaje, contexto = dialogo_id.split("/", 1)
            ctx.dialog_service.iniciar(
                personaje, contexto,
                al_terminar=lambda: ctx.manager.mostrar_opciones_plano(ctx.state),
            )
            ctx.manager._bloqueo_por = "dialogo"
            return True
        return False
