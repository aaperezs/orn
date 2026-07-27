import sys

import pygame


class InputManager:
    """Unified input handler: maps keys to actions. Supports rebinding."""

    _DEFAULT_MAP = {
        # Movement
        pygame.K_UP: "MOVE_UP",
        pygame.K_DOWN: "MOVE_DOWN",
        pygame.K_LEFT: "MOVE_LEFT",
        pygame.K_RIGHT: "MOVE_RIGHT",
        # Interaction
        pygame.K_e: "INTERACT",
        # Skills
        pygame.K_q: "USE_SKILL",
        pygame.K_TAB: "NEXT_SKILL",
        # Menus
        pygame.K_p: "TOGGLE_PAUSE",
        pygame.K_f: "TOGGLE_FORGE",
        pygame.K_t: "TOGGLE_TRADE",
        pygame.K_i: "TOGGLE_INVENTORY",
        # Dialogue
        pygame.K_SPACE: "DIALOGUE_ADVANCE",
        pygame.K_RETURN: "DIALOGUE_ADVANCE",
        # Game over
        pygame.K_r: "RESTART",
        # Forge/inventory navigation
        pygame.K_ESCAPE: "CLOSE_MENU",
        # Debug
        pygame.K_F3: "TOGGLE_GODMODE",
    }

    _DIR_MAP = {
        "MOVE_UP": "ARRIBA",
        "MOVE_DOWN": "ABAJO",
        "MOVE_LEFT": "IZQUIERDA",
        "MOVE_RIGHT": "DERECHA",
    }

    _TRADE_MAP = {
        pygame.K_1: "TRADE_1",
        pygame.K_3: "TRADE_3",
        pygame.K_5: "TRADE_5",
        pygame.K_d: "TRADE_BORROW",
    }

    def __init__(self, estado, mostrar_mensaje, usar_habilidad_golpe):
        self.estado = estado
        self.mostrar_mensaje = mostrar_mensaje
        self.usar_habilidad = usar_habilidad_golpe
        self._action_map = dict(self._DEFAULT_MAP)

    def rebind(self, key, action):
        self._action_map[key] = action

    def process_events(self):
        estado = self.estado
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN:
                self._handle_key(evento.key)

    def _handle_key(self, key):
        estado = self.estado

        # Dialogue overrides everything
        if estado.dialogo.activo:
            if key in (pygame.K_SPACE, pygame.K_RETURN):
                estado.dialogo.avanzar()
            return

        # Ventana
        if estado.ventana.activo:
            if key in (pygame.K_SPACE, pygame.K_RETURN):
                estado.ventana.avanzar()
            return

        # Game over
        if estado.game_over:
            if key == pygame.K_r:
                estado.reiniciar()
            elif key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            return

        # Forge
        if estado.mostrando_forja:
            self._handle_forge(key)
            return

        # Inventory
        if estado.mostrando_inventario:
            self._handle_inventory(key)
            return

        # Trade
        if estado.mostrando_trueque:
            self._handle_trade(key)
            return

        # World controls
        self._handle_world(key)

    def _handle_forge(self, key):
        estado = self.estado
        if key == pygame.K_ESCAPE:
            estado.mostrando_forja = False
        elif key == pygame.K_UP:
            estado.sistema_forja.seleccion = max(0, estado.sistema_forja.seleccion - 1)
        elif key == pygame.K_DOWN:
            recetas = list(estado.sistema_forja._repo.get_todas().keys())
            estado.sistema_forja.seleccion = min(len(recetas) - 1, estado.sistema_forja.seleccion + 1)
        elif key == pygame.K_RETURN:
            estado.sistema_forja.fabricar_seleccion()

    def _handle_inventory(self, key):
        estado = self.estado
        if key == pygame.K_ESCAPE:
            estado.mostrando_inventario = False
        elif key == pygame.K_TAB:
            self._cycle_skill()

    def _handle_trade(self, key):
        estado = self.estado
        if key == pygame.K_1:
            if estado.snake.vender_segmentos(1):
                self.mostrar_mensaje("Vendiste 1 segmento!", 60)
                estado.mostrando_trueque = False
        elif key == pygame.K_3:
            if estado.snake.vender_segmentos(3):
                self.mostrar_mensaje("Vendiste 3 segmentos!", 60)
                estado.mostrando_trueque = False
        elif key == pygame.K_5:
            if estado.snake.vender_segmentos(5):
                self.mostrar_mensaje("Vendiste 5 segmentos!", 60)
                estado.mostrando_trueque = False
        elif key == pygame.K_d:
            if estado.snake.pedir_prestado(3):
                self.mostrar_mensaje("Pediste prestado! Velocidad aumentada.", 60)
                estado.mostrando_trueque = False
        elif key == pygame.K_ESCAPE:
            estado.mostrando_trueque = False

    def _cycle_skill(self):
        estado = self.estado
        estado.habilidades.cambiar_habilidad(1)
        hab = estado.habilidades.get_habilidad_equipada()
        if hab:
            estado.snake.set_skin(hab.get("efecto"))

    def _interact(self):
        estado = self.estado
        cabeza = estado.snake.get_cabeza()
        if not cabeza:
            return
        from configs import TAMANO_CELDA
        dx = dy = 0
        if estado.snake.direccion == "ARRIBA":    dy = -TAMANO_CELDA
        elif estado.snake.direccion == "ABAJO":   dy = TAMANO_CELDA
        elif estado.snake.direccion == "IZQUIERDA": dx = -TAMANO_CELDA
        elif estado.snake.direccion == "DERECHA":  dx = TAMANO_CELDA
        target_x = cabeza[0] + dx
        target_y = cabeza[1] + dy

        estado.stack_manager.process_events(target_x, target_y, "interact", estado.snake.z)

    def _handle_world(self, key):
        estado = self.estado
        if estado.mandos_bloqueados:
            return

        action = self._action_map.get(key)

        # Movement (handled even if not in action_map for non-bound keys during sleep)
        if key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
            self._apply_direction(key, estado)
            return

        if action == "INTERACT":
            self._interact()
        elif action == "USE_SKILL":
            self.usar_habilidad()
        elif action == "NEXT_SKILL":
            self._cycle_skill()
        elif action == "TOGGLE_PAUSE":
            estado.pausa = not estado.pausa
        elif action == "TOGGLE_FORGE":
            estado.mostrando_forja = not estado.mostrando_forja
        elif action == "TOGGLE_TRADE":
            estado.mostrando_trueque = not estado.mostrando_trueque
        elif action == "TOGGLE_INVENTORY":
            estado.mostrando_inventario = not estado.mostrando_inventario
        elif action == "TOGGLE_GODMODE":
            estado.god_mode = not estado.god_mode
            msg = "DEBUG: God Mode ON" if estado.god_mode else "DEBUG: God Mode OFF"
            self.mostrar_mensaje(msg, 90)

    def _apply_direction(self, key, estado):
        dir_map = {
            pygame.K_UP: "ARRIBA",
            pygame.K_DOWN: "ABAJO",
            pygame.K_LEFT: "IZQUIERDA",
            pygame.K_RIGHT: "DERECHA",
        }
        direction = dir_map[key]
        estado.snake.cambiar_direccion(direction)

    def get_action_name(self, action):
        """Get the key name for an action (for UI display)."""
        for key, act in self._action_map.items():
            if act == action:
                return pygame.key.name(key)
        return "?"
