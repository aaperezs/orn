"""Acciones migradas automaticamente desde stack_manager._ejecutar_accion.

NO EDITAR MANUALMENTE - generado por scripts/migrate_trivial_actions.py
"""

from systems.action_registry import GameAction, register_action


TAMANO_CELDA = 32  # from configs.constants

@register_action("open_save_menu")
class OpenSaveMenu(GameAction):
    def execute(self, ctx, params):
        if hasattr(ctx.state, "menu") and hasattr(ctx.state.menu, "abrir_menu"):
            ctx.state.mostrando_inventario = True
            ctx.state.menu.abrir_menu("save")
        return False


@register_action("open_load_menu")
class OpenLoadMenu(GameAction):
    def execute(self, ctx, params):
        if hasattr(ctx.state, "menu") and hasattr(ctx.state.menu, "abrir_menu"):
            ctx.state.mostrando_inventario = True
            ctx.state.menu.abrir_menu("load")
        return False


@register_action("close_shop")
class CloseShop(GameAction):
    def execute(self, ctx, params):
        if hasattr(ctx.state, "shop_actual"):
            ctx.state.shop_actual = None
        ctx.state.mostrando_inventario = False
        if hasattr(ctx.state, "menu") and hasattr(ctx.state.menu, "cerrar"):
            ctx.state.menu.cerrar()
        return False


@register_action("close_save_menu")
class CloseSaveMenu(GameAction):
    def execute(self, ctx, params):
        if hasattr(ctx.state, "menu") and hasattr(ctx.state.menu, "cerrar"):
            ctx.state.menu.cerrar()
        ctx.state.mostrando_inventario = False
        return False


@register_action("mostrar_personaje")
class MostrarPersonaje(GameAction):
    def execute(self, ctx, params):
        personaje_id = params.get("personaje_id", "")
        posicion = params.get("posicion", "centro")
        expresion = params.get("expresion", "normal")
        if personaje_id and hasattr(ctx.state, "personajes_visibles"):
            sprite_name = f"personajes/{personaje_id}_{expresion}"
            pos_map = {"izquierda": 0, "centro": 1, "derecha": 2}
            ctx.state.personajes_visibles[personaje_id] = {
                "sprite": sprite_name,
                "posicion": pos_map.get(posicion, 1),
                "x": 0,
                "y": 0,
            }
        return False


@register_action("ocultar_personaje")
class OcultarPersonaje(GameAction):
    def execute(self, ctx, params):
        personaje_id = params.get("personaje_id", "")
        if personaje_id and hasattr(ctx.state, "personajes_visibles"):
            ctx.state.personajes_visibles.pop(personaje_id, None)
        return False


@register_action("ocultar_todos_personajes")
class OcultarTodosPersonajes(GameAction):
    def execute(self, ctx, params):
        if hasattr(ctx.state, "personajes_visibles"):
            ctx.state.personajes_visibles.clear()
        return False
