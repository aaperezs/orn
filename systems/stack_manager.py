import json
import os
import sys

import pygame

from configs import MOSTRAR_LOGS
from configs.constants import TAMANO_CELDA
from configs.game import VELOCIDAD_BASE
from repositories.repositorio_objetos import RepositorioObjetos

STACKS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "levels", "mapas_stacks")


class StackManager:
    def __init__(self, estado):
        self.estado = estado
        self._stacks = {}
        self._nivel_id = None
        self._event_states = {}  # {event_id: "pendiente"|"finalizado"}
        self.bloqueado = False    # Blockea process_events mientras espera
        self.timer_hasta = 0      # Timestamp en ms hasta cuando esperar
        self._cola_acciones = []  # Acciones pendientes tras esperar
        self._cola_ctx = (0, 0, 0)  # (x, y, z) contexto de la cola
        self._bloqueo_por = None  # None, "timer", "dialogo", "ventana"
        self._auto_direccion = None  # Dirección para auto_caminar

    def load_stacks(self, nivel_id):
        self._stacks = {}
        self._nivel_id = nivel_id
        if not nivel_id:
            return
        path = os.path.join(STACKS_DIR, f"{nivel_id}_stacks.json")
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for s in data.get("stacks", []):
                pos = tuple(s["pos"])
                z = s.get("z", s.get("z_layer", 0))
                eventos = s.get("eventos", [])
                # Convert old format (capas -> eventos)
                if not eventos and "capas" in s:
                    capas = s.get("capas", [])
                    if capas:
                        for capa in capas:
                            capa_evs = capa.get("eventos", [])
                            for ev in capa_evs:
                                old_tipo = ev.get("tipo", "")
                                new_trigger = "contact" if old_tipo == "on_destroy" else \
                                              "interact" if old_tipo == "on_interact" else "contact"
                                eventos.append({
                                    "trigger": new_trigger,
                                    "condiciones": [],
                                    "acciones": [{"tipo": ev.get("accion", "show_message"),
                                                  "params": dict(ev.get("parametros", {}))}]
                                })
                # Migrate old condition format to new 6-type with operators
                for ev in eventos:
                    for cond in ev.get("condiciones", []):
                        ct = cond["tipo"]
                        p = cond["params"]
                        if ct == "has_escamas":
                            cond["tipo"] = "escamas"
                            p["operador"] = ">="
                            p["valor"] = p.pop("min", 1)
                        elif ct == "not_has_escamas":
                            cond["tipo"] = "escamas"
                            p["operador"] = "<"
                            p["valor"] = p.pop("cantidad", 1)
                        elif ct == "has_item":
                            cond["tipo"] = "item_count"
                            p["operador"] = ">="
                            p["valor"] = p.pop("cantidad_min", 1)
                        elif ct == "not_has_item":
                            cond["tipo"] = "item_count"
                            p["operador"] = "<"
                            p["valor"] = p.pop("cantidad", 1)
                        elif ct == "has_flag":
                            cond["tipo"] = "flag"
                            p["operador"] = "es_verdadero"
                        elif ct == "not_has_flag":
                            cond["tipo"] = "flag"
                            p["operador"] = "es_falso"
                        elif ct == "has_ability":
                            cond["tipo"] = "ability"
                            p["operador"] = "tiene"
                            p.pop("nivel_min", None)
                        elif ct == "not_has_ability":
                            cond["tipo"] = "ability"
                            p["operador"] = "no_tiene"
                        elif ct == "has_ability_equipped":
                            cond["tipo"] = "ability_equipped"
                            p["operador"] = "equipado"
                        elif ct == "not_has_ability_equipped":
                            cond["tipo"] = "ability_equipped"
                            p["operador"] = "no_equipado"
                        elif ct == "has_pp":
                            cond["tipo"] = "pp"
                            p["operador"] = ">="
                            p["valor"] = p.pop("min", 1)
                s["eventos"] = eventos
                key = (pos[0], pos[1], z)
                self._stacks[key] = s
                # Register event IDs as pending (only if not already finalized)
                for ev in s.get("eventos", []):
                    eid = ev.get("id", "")
                    if eid and eid not in self._event_states:
                        self._event_states[eid] = "pendiente"
        except (json.JSONDecodeError, FileNotFoundError):
            pass

        # Filter out only once=True events that have been finalized (already executed)
        for key in list(self._stacks.keys()):
            stack = self._stacks[key]
            eventos = stack.get("eventos", [])
            eventos[:] = [ev for ev in eventos
                          if not (ev.get("once", False)
                                  and self._event_states.get(ev.get("id", "")) == "finalizado")]
            if not eventos:
                del self._stacks[key]

    def get_stack_at(self, x, y, z=0):
        gx = x // TAMANO_CELDA
        gy = y // TAMANO_CELDA
        return self._stacks.get((gx, gy, z))

    def get_stack_grid(self, gx, gy, z=0):
        return self._stacks.get((gx, gy, z))

    def actualizar(self, estado):
        """Se llama cada frame. Procesa bloqueos por timer o diálogo."""
        if self._bloqueo_por == "timer":
            if pygame.time.get_ticks() >= self.timer_hasta:
                self.bloqueado = False
                self.timer_hasta = 0
                self._bloqueo_por = None
                acciones, self._cola_acciones = self._cola_acciones, []
                self._ejecutar_acciones(acciones, *self._cola_ctx)
        elif self._bloqueo_por == "dialogo":
            if not estado.dialogo.activo:
                self._bloqueo_por = None
                acciones, self._cola_acciones = self._cola_acciones, []
                self._ejecutar_acciones(acciones, *self._cola_ctx)
        elif self._bloqueo_por == "ventana":
            if not estado.ventana.activo:
                self._bloqueo_por = None
                acciones, self._cola_acciones = self._cola_acciones, []
                self._ejecutar_acciones(acciones, *self._cola_ctx)

        if self._auto_direccion and hasattr(estado, "snake"):
            estado.snake.cambiar_direccion(self._auto_direccion)

    def process_events(self, x, y, trigger, jugador_z=None):
        if self.bloqueado:
            return
        gx = x // TAMANO_CELDA
        gy = y // TAMANO_CELDA
        stacks_here = [(k, v) for k, v in self._stacks.items()
                       if k[0] == gx and k[1] == gy]
        if not stacks_here:
            return
        for key, stack in stacks_here:
            z_layer = key[2]
            eventos = stack.get("eventos", [])
            eventos_removed = []
            for ev in eventos:
                if ev.get("trigger") == trigger:
                    print(f"[EVENTO] stack ({gx},{gy}) Z={z_layer} trigger={trigger} condiciones={len(ev.get('condiciones',[]))}")
                    if self._check_conditions(ev.get("condiciones", [])):
                        self._auto_direccion = None
                        print(f"[EVENTO] condiciones OK, ejecutando {len(ev.get('acciones',[]))} accion(es)")
                        self._ejecutar_acciones(ev.get("acciones", []), gx * TAMANO_CELDA, gy * TAMANO_CELDA, z_layer)
                        eid = ev.get("id", "")
                        actions = [a.get("tipo") for a in ev.get("acciones", [])]
                        auto_consume = "remove_sprite" in actions
                        if eid and (ev.get("once", False) or auto_consume):
                            self._event_states[eid] = "finalizado"
                            self._check_event_triggers(eid)
                        if ev.get("once", False) or auto_consume:
                            eventos_removed.append(ev)
                    else:
                        print("[EVENTO] condiciones NO cumplidas")
            for ev in eventos_removed:
                eventos.remove(ev)
            if eventos_removed:
                print(f"[EVENTO] {len(eventos_removed)} evento(s) eliminados (once=True o remove_sprite). Eventos restantes: {len(eventos)}")
            if not eventos:
                del self._stacks[key]
                print(f"[EVENTO] stack ({gx},{gy}) Z={z_layer} eliminado (sin eventos)")

    def on_hit(self, x, y, z=0, damage=0, attack_type=""):
        """Procesa eventos trigger on_hit con información del golpe"""
        gx = x // TAMANO_CELDA
        gy = y // TAMANO_CELDA
        stacks_here = [(k, v) for k, v in self._stacks.items()
                       if k[0] == gx and k[1] == gy
                       and k[2] == z]
        for key, stack in stacks_here:
            z_layer = key[2]
            eventos = stack.get("eventos", [])
            eventos_removed = []
            for ev in eventos:
                if ev.get("trigger") == "on_hit":
                    extra = {"damage": damage, "attack_type": attack_type}
                    if self._check_conditions(ev.get("condiciones", []), extra):
                        self._ejecutar_acciones(ev.get("acciones", []), gx * TAMANO_CELDA, gy * TAMANO_CELDA, z_layer)
                        eid = ev.get("id", "")
                        actions = [a.get("tipo") for a in ev.get("acciones", [])]
                        auto_consume = "remove_sprite" in actions
                        if eid and (ev.get("once", False) or auto_consume):
                            self._event_states[eid] = "finalizado"
                            self._check_event_triggers(eid)
                        if ev.get("once", False) or auto_consume:
                            eventos_removed.append(ev)
            for ev in eventos_removed:
                eventos.remove(ev)
            if not eventos:
                del self._stacks[key]

    def _check_event_triggers(self, eid):
        """Dispara eventos con trigger 'on_event_finalized' que observan a eid."""
        if not eid:
            return
        for key, stack in list(self._stacks.items()):
            gx, gy, z_layer = key
            eventos = stack.get("eventos", [])
            eventos_removed = []
            for ev in eventos:
                if ev.get("trigger") == "on_event_finalized":
                    watched = ev.get("watched_event_id", "")
                    if watched != eid:
                        continue
                    print(f"[EVENTO] on_event_finalized ({gx},{gy}) Z={z_layer} watched={eid}")
                    if self._check_conditions(ev.get("condiciones", [])):
                        self._ejecutar_acciones(ev.get("acciones", []), gx * TAMANO_CELDA, gy * TAMANO_CELDA, z_layer)
                        eid2 = ev.get("id", "")
                        if eid2 and ev.get("once", False):
                            self._event_states[eid2] = "finalizado"
                            self._check_event_triggers(eid2)
                        if ev.get("once", False):
                            eventos_removed.append(ev)
            for ev in eventos_removed:
                eventos.remove(ev)
            if not eventos:
                del self._stacks[key]

    def on_boss_defeated(self, boss_id):
        """Busca y ejecuta eventos con trigger 'on_boss_defeated' cuyo boss_id coincida."""
        if self.bloqueado:
            return
        for key, stack in list(self._stacks.items()):
            gx, gy, z_layer = key
            eventos = stack.get("eventos", [])
            eventos_removed = []
            for ev in eventos:
                if ev.get("trigger") == "on_boss_defeated":
                    ev_boss = ev.get("boss_id", "")
                    if ev_boss and ev_boss != boss_id:
                        continue
                    from configs.habilidades import HabilidadID
                    hid = getattr(HabilidadID, boss_id.upper(), boss_id)
                    extra = {"boss_id": boss_id, "boss_hid": hid}
                    print(f"[EVENTO] on_boss_defeated ({gx},{gy}) Z={z_layer} boss={boss_id}")
                    if self._check_conditions(ev.get("condiciones", []), extra):
                        self._ejecutar_acciones(ev.get("acciones", []), gx * TAMANO_CELDA, gy * TAMANO_CELDA, z_layer)
                        eid = ev.get("id", "")
                        if eid and ev.get("once", False):
                            self._event_states[eid] = "finalizado"
                        if ev.get("once", False):
                            eventos_removed.append(ev)
            for ev in eventos_removed:
                eventos.remove(ev)
            if not eventos:
                del self._stacks[key]

    def on_entity_destroyed(self, x, y, entidad_tipo, z=None):
        if z is None and hasattr(self.estado, "snake"):
            z = self.estado.snake.z
        self.process_events(x, y, "contact", z)

    def on_interact(self, x, y, entidad_tipo, z=None):
        if z is None and hasattr(self.estado, "snake"):
            z = self.estado.snake.z
        self.process_events(x, y, "interact", z)

    def _check_conditions(self, condiciones, extra=None):
        extra = extra or {}
        estado = self.estado
        for cond in condiciones:
            ct = cond.get("tipo", "")
            params = cond.get("params", {})
            op = params.get("operador", ">=")
            valor = params.get("valor", 1)

            if ct == "escamas":
                if not hasattr(estado, "snake"):
                    return False
                actual = estado.snake.get_escamas()
                if not self._eval(actual, op, int(valor)):
                    return False

            elif ct == "item_count":
                item = params.get("item", "")
                if not hasattr(estado, "inventario"):
                    return False
                actual = estado.inventario.cantidad(item)
                if not self._eval(actual, op, int(valor)):
                    return False

            elif ct == "flag":
                flag = params.get("flag", "")
                if not hasattr(estado, "flags"):
                    return False
                actual = bool(estado.flags.get(flag))
                if op == "es_verdadero" and not actual:
                    return False
                if op == "es_falso" and actual:
                    return False

            elif ct == "ability":
                ability = params.get("ability", "")
                if not hasattr(estado, "habilidades"):
                    return False
                actual = estado.habilidades.tiene_habilidad(ability)
                if op == "tiene" and not actual:
                    return False
                if op == "no_tiene" and actual:
                    return False

            elif ct == "ability_equipped":
                ability = params.get("ability", "")
                if not hasattr(estado, "habilidades"):
                    return False
                tiene = estado.habilidades.tiene_habilidad(ability)
                equipada = estado.habilidades.habilidad_equipada == ability
                if op == "equipado" and not (tiene and equipada):
                    return False
                if op == "no_equipado" and (tiene and equipada):
                    return False

            elif ct == "pp":
                if not hasattr(estado, "habilidades"):
                    return False
                actual = estado.habilidades.get_pp_actual()
                if not self._eval(actual, op, int(valor)):
                    return False

            elif ct == "evaluar_evento":
                evento_id = params.get("evento_id", "")
                estado_esperado = params.get("estado", "finalizado")
                actual = self._event_states.get(evento_id, "pendiente")
                if actual != estado_esperado:
                    return False

            elif ct == "damage":
                actual = extra.get("damage", 0)
                if not self._eval(actual, op, int(valor)):
                    return False

            elif ct == "attack_type":
                esperado = params.get("valor", "")
                actual = extra.get("attack_type", "")
                if op == "==" and actual != esperado:
                    return False
                if op == "!=" and actual == esperado:
                    return False

        return True

    def _eval(self, actual, op, esperado):
        if op == ">=": return actual >= esperado
        if op == "<=": return actual <= esperado
        if op == ">":  return actual > esperado
        if op == "<":  return actual < esperado
        if op == "==": return actual == esperado
        if op == "!=": return actual != esperado
        return True

    def _ejecutar_acciones(self, acciones, x, y, z=0):
        for i, act in enumerate(acciones):
            print(f"[EVENTO] accion {i+1}: {act.get('tipo')} params={act.get('params', {})}")
            bloquea = self._ejecutar_accion(act.get("tipo"), act.get("params", {}), x, y, z)
            if bloquea:
                self._cola_acciones = acciones[i+1:]
                self._cola_ctx = (x, y, z)
                break

    def _ejecutar_accion(self, accion, params, x, y, z=0):
        estado = self.estado

        if accion == "show_message":
            mensaje = params.get("mensaje", "")
            if mensaje:
                estado.mensaje_temporal = mensaje
                estado.tiempo_mensaje = 90

        elif accion == "replace_sprite":
            sprite_id = params.get("sprite_id", "")
            gx = x // TAMANO_CELDA
            gy = y // TAMANO_CELDA
            if hasattr(estado, "replace_tile_sprite"):
                estado.replace_tile_sprite(gx, gy, sprite_id, z)

        elif accion == "remove_sprite":
            gx = x // TAMANO_CELDA
            gy = y // TAMANO_CELDA
            if hasattr(estado, "remove_tile_sprite"):
                estado.remove_tile_sprite(gx, gy, z)
            self._remover_entidades_en(estado, gx, gy)

        elif accion == "spawn_entity":
            sprite_id = params.get("sprite_id", "")
            ox = int(params.get("offset_x", 0))
            oy = int(params.get("offset_y", 0))
            z = int(params.get("z", 0))
            sx = x + ox * TAMANO_CELDA
            sy = y + oy * TAMANO_CELDA
            self._spawn_from_sprite(sprite_id, sx, sy)

        elif accion == "start_dialogue":
            dialogo_id = params.get("dialogo_id", "")
            if "/" in dialogo_id and hasattr(estado, "dialogo"):
                personaje, contexto = dialogo_id.split("/", 1)
                estado.dialogo.iniciar(personaje, contexto)

        elif accion == "iniciar_dialogo":
            dialogo_id = params.get("dialogo_id", "")
            if "/" in dialogo_id and hasattr(estado, "dialogo"):
                personaje, contexto = dialogo_id.split("/", 1)
                estado.dialogo.iniciar(personaje, contexto)
                self._bloqueo_por = "dialogo"
                return True

        elif accion == "start_boss_fight":
            if hasattr(estado, 'arena_boss') and estado.arena_boss:
                arena = estado.arena_boss
                boss = getattr(estado, 'boss', None)
                if boss and boss.vivo:
                    if getattr(arena, 'es_nivel_completo', False):
                        arena.activar_combate(estado.snake, estado)
                    else:
                        punto_entrada = (arena.x + 60, arena.y + arena.alto - 60)
                        arena.activar_con_entrada(boss, punto_entrada, estado.snake, estado)

        elif accion == "change_map":
            nivel = params.get("nivel", "")
            exit_id = params.get("exit_id", "")
            if nivel and hasattr(estado, "cambiar_nivel"):
                estado.gate_destino = nivel
                estado.gate_salida_id = exit_id if exit_id else None
                estado.cambiando_nivel = True

        elif accion == "give_item":
            item = params.get("item", "")
            cantidad = int(params.get("cantidad", 1))
            if item and hasattr(estado, "inventario"):
                estado.inventario.agregar_item(item, cantidad)
                repo = RepositorioObjetos()
                cfg = repo.get_objeto(item)
                nombre = cfg.get("nombre", item) if cfg else item
                mensaje = f"¡{nombre} x{cantidad}!"
                estado.mensaje_temporal = mensaje
                estado.tiempo_mensaje = 60

        elif accion == "remove_item":
            item = params.get("item", "")
            cantidad = int(params.get("cantidad", 1))
            if item and hasattr(estado, "inventario"):
                estado.inventario.remover_item(item, cantidad)

        elif accion == "consume_pp":
            cantidad = int(params.get("cantidad", 1))
            if hasattr(estado, "habilidades"):
                for _ in range(cantidad):
                    estado.habilidades.usar_habilidad()

        elif accion == "set_flag":
            flag = params.get("flag", "")
            if flag and hasattr(estado, "flags"):
                estado.flags[flag] = True

        elif accion == "clear_flag":
            flag = params.get("flag", "")
            if flag and hasattr(estado, "flags"):
                estado.flags[flag] = False

        elif accion == "mover_a":
            evento_id = params.get("evento_id", "")
            if evento_id and hasattr(estado, "snake"):
                # Buscar el evento por ID en todos los stacks cargados
                for (gx, gy, z), stack in list(self._stacks.items()):
                    for ev in stack.get("eventos", []):
                        if ev.get("id") == evento_id:
                            px = gx * TAMANO_CELDA
                            py = gy * TAMANO_CELDA
                            estado.snake.body = [[px, py]]
                            estado.snake.iniciar_dormido((px, py))
                            print(f"[EVENTO] mover_a -> evento '{evento_id}' en ({gx},{gy}) Z={z}")
                            return

        elif accion == "remove_escamas":
            cantidad = int(params.get("cantidad", 1))
            if hasattr(estado, "snake"):
                estado.snake.perder_escamas(cantidad)

        elif accion == "damage":
            cantidad = int(params.get("cantidad", 1))
            if not hasattr(estado, "snake"):
                return
            snake = estado.snake
            if snake.invencible or getattr(estado, "god_mode", False):
                return
            if snake.get_longitud() <= 3:
                estado.game_over = True
                estado.death_cause = "Daño letal en evento"
                return
            max_perder = snake.get_longitud() - 3
            if cantidad > max_perder:
                cantidad = max_perder
            if cantidad <= 0:
                return
            perdidos = snake.perder_segmentos(cantidad)
            if perdidos:
                from entities.segmento_perdido import SegmentoPerdido
                for pos in perdidos:
                    if pos:
                        seg = SegmentoPerdido(pos[0], pos[1],
                            estado.nivel_ancho, estado.nivel_alto)
                        estado.segmentos_perdidos.append(seg)
                from systems.event_bus import EventoDamageInfligido
                estado.event_bus.publicar(EventoDamageInfligido(
                    cantidad=len(perdidos),
                    fuente="event",
                    posicion=(x, y),
                ))
                mensaje = params.get("mensaje", f"¡Perdiste {len(perdidos)} segmentos!")
                estado.mensaje_temporal = mensaje
                estado.tiempo_mensaje = 60

        elif accion == "bloquear_mandos":
            bloquear = params.get("bloquear", True)
            if isinstance(bloquear, str):
                bloquear = bloquear.lower() in ("true", "1", "si")
            estado.mandos_bloqueados = bool(bloquear)

        elif accion == "desbloquear_habilidad":
            habilidad = params.get("habilidad", "")
            if habilidad and hasattr(estado, "habilidades"):
                from configs.habilidades import HabilidadID
                hid = getattr(HabilidadID, habilidad.upper(), habilidad)
                if not estado.habilidades.tiene_habilidad(hid):
                    estado.habilidades.desbloquear_habilidad(hid)
                print(f"[EVENTO] habilidad '{habilidad}' desbloqueada")

        elif accion == "equipar_habilidad":
            habilidad = params.get("habilidad", "")
            if habilidad and hasattr(estado, "habilidades"):
                from configs.habilidades import HabilidadID
                hid = getattr(HabilidadID, habilidad.upper(), habilidad)
                estado.habilidades.equipar_habilidad(hid)
                print(f"[EVENTO] habilidad '{habilidad}' equipada")

        elif accion == "cambiar_skin":
            skin = params.get("skin", "")
            if skin and hasattr(estado, "snake"):
                estado.snake.set_skin(skin)

        elif accion == "mostrar_boss":
            visible = params.get("visible", True)
            if isinstance(visible, str):
                visible = visible.lower() in ("true", "1", "si")
            if hasattr(estado, "boss") and estado.boss:
                estado.boss.vivo = bool(visible)

        elif accion == "mostrar_ventana":
            ventana_id = params.get("ventana_id", "")
            if ventana_id and hasattr(estado, "ventana"):
                estado.ventana.iniciar(ventana_id)
                self._bloqueo_por = "ventana"
                return True

        elif accion == "fin_demo":
            estado.volver_a_menu = True
            estado.corriendo = False

        elif accion == "iniciar_demo":
            demo_id = params.get("demo_id", "")
            if demo_id:
                estado.demo_habilidad_pendiente = True
                estado.demo_habilidad_id = demo_id
                nivel_origen = getattr(estado, '_nivel_antes_arena', getattr(estado.level_manager, 'obtener_id_actual', lambda: None)())
                if nivel_origen:
                    estado.nivel_origen = nivel_origen

        elif accion == "comando_automatico":
            comando = params.get("comando", "")
            if comando in ("DERECHA", "IZQUIERDA", "ARRIBA", "ABAJO"):
                if hasattr(estado, "snake"):
                    estado.snake.cambiar_direccion(comando)
            elif comando == "ATAQUE":
                if self.fn_ataque:
                    self.fn_ataque()
            elif comando == "ACCION":
                if hasattr(estado, "stack_manager"):
                    cabeza = estado.snake.get_cabeza()
                    if cabeza:
                        dx = dy = 0
                        direccion = estado.snake.direccion
                        if direccion == "ARRIBA":    dy = -TAMANO_CELDA
                        elif direccion == "ABAJO":   dy = TAMANO_CELDA
                        elif direccion == "IZQUIERDA": dx = -TAMANO_CELDA
                        elif direccion == "DERECHA":  dx = TAMANO_CELDA
                        estado.stack_manager.process_events(cabeza[0] + dx, cabeza[1] + dy, "interact", estado.snake.z)

        elif accion == "avanzar":
            direccion = params.get("direccion", "")
            if direccion and hasattr(estado, "snake"):
                estado.snake.cambiar_direccion(direccion.upper())
                estado.snake.mover()

        elif accion == "auto_caminar":
            direccion = params.get("direccion", "").upper()
            if direccion in ("DERECHA", "IZQUIERDA", "ARRIBA", "ABAJO"):
                self._auto_direccion = direccion
            else:
                self._auto_direccion = None

        elif accion == "despertar":
            if hasattr(estado, "snake"):
                estado.snake.despertar()

        elif accion == "accion_botton":
            tecla = params.get("tecla", "").upper()
            if MOSTRAR_LOGS: print(f"[BOTON] tecla={tecla}")
            if tecla == "Q":
                self.estado.ejecutar_golpe_q()

        elif accion == "esperar":
            segundos = float(params.get("segundos", 1))
            self.timer_hasta = pygame.time.get_ticks() + max(1, int(segundos * 1000))
            self._bloqueo_por = "timer"
            return True

        elif accion == "bloquear_eventos":
            bloquear = params.get("bloquear", True)
            if isinstance(bloquear, str):
                bloquear = bloquear.lower() in ("true", "1", "si")
            self.bloqueado = bool(bloquear)

        elif accion == "run_script":
            func_name = params.get("function_name", "")
            args_str = params.get("args", "")
            if func_name:
                args_list = [a.strip() for a in args_str.split(",") if a.strip()] if args_str else []
                import importlib
                for mod_name in list(sys.modules.keys()):
                    if mod_name.endswith("_game") or mod_name == "game" or mod_name == "scripts.game":
                        module = sys.modules[mod_name]
                        func = getattr(module, func_name, None)
                        if func and callable(func):
                            try:
                                func(*args_list)
                            except Exception as e:
                                print(f"[EVENTO] run_script error: {e}")
                            break

    def _remover_entidades_en(self, estado, gx, gy):
        px = gx * TAMANO_CELDA
        py = gy * TAMANO_CELDA
        # Remover comida (entity singular)
        if hasattr(estado, "comida") and estado.comida:
            if estado.comida.x == px and estado.comida.y == py:
                estado.comida = None
        # Remover entidades en listas
        listas = ["bloqueantes", "paredes", "bloques_acero", "hierba_alta",
                  "enemigos", "suelos"]
        for nombre_lista in listas:
            if not hasattr(estado, nombre_lista):
                continue
            lista = getattr(estado, nombre_lista)
            for ent in lista:
                if hasattr(ent, "x") and hasattr(ent, "y") and hasattr(ent, "activo"):
                    if ent.x == px and ent.y == py:
                        ent.activo = False

    def _spawn_from_sprite(self, sprite_id, x, y):
        from levels.level_parser import _make_from_behavior

        from editor.elements import get_element

        el = get_element(sprite_id)
        if not el:
            return
        behavior = el.get("behavior", "decorative")
        if behavior in ("decorative", "spawn"):
            return

        entity, target = _make_from_behavior(x, y, sprite_id, el, {}, {}, {}, (0, 0), 0)
        if entity is None:
            return

        estado = self.estado

        if target == "collidables":
            from entities.arbol import Arbol
            from entities.bloque_acero import BloqueAcero
            from entities.hierba_alta import HierbaAlta
            from entities.pared import Pared
            from entities.objeto_colision import ObjetoBloqueante
            if isinstance(entity, Pared) and hasattr(estado, "paredes"):
                estado.paredes.append(entity)
            elif isinstance(entity, ObjetoBloqueante) and not isinstance(entity, (BloqueAcero, Arbol)) and hasattr(estado, "bloqueantes"):
                estado.bloqueantes.append(entity)
            elif isinstance(entity, (BloqueAcero, Arbol)) and hasattr(estado, "bloques_acero"):
                estado.bloques_acero.append(entity)
            elif isinstance(entity, HierbaAlta) and hasattr(estado, "hierba_alta"):
                estado.hierba_alta.append(entity)
        elif target == "suelos" and hasattr(estado, "suelos"):
            estado.suelos.append(entity)
        elif target == "enemigos" and hasattr(estado, "enemigos"):
            estado.enemigos.append(entity)
        elif target == "comidas" and hasattr(estado, "comidas"):
            estado.comidas.append(entity)

        elif entity_name == "Arbol":
            from entities.arbol import Arbol
            if hasattr(estado, "bloques_acero"):
                estado.bloques_acero.append(Arbol(x, y))
