import json
import os
import sys

import pygame

from configs import MOSTRAR_LOGS
from configs.constants import TAMANO_CELDA
from configs.game import VELOCIDAD_BASE
from project_paths import levels_dir
from repositories.repositorio_objetos import RepositorioObjetos

STACKS_DIR = levels_dir("mapas_stacks")


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
        self._bloqueo_por = None  # None, "timer", "dialogo", "ventana", "choice", "dialogo_tree"
        self._auto_direccion = None  # Dirección para auto_caminar
        self._arbol_dialogo = None  # Estado del arbol de diálogo en reproducción

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
                    # Migrar condición legacy "escamas" -> has_moneda (moneda="escamas")
                    for cond in ev.get("condiciones", []):
                        if cond.get("tipo") == "escamas":
                            cond["tipo"] = "has_moneda"
                            cond.setdefault("params", {}).setdefault("moneda", "escamas")
                    # Migrar acción legacy "remove_escamas" -> remove_moneda
                    for accion in ev.get("acciones", []):
                        if accion.get("tipo") == "remove_escamas":
                            accion["tipo"] = "remove_moneda"
                            accion.setdefault("params", {}).setdefault("moneda", "escamas")
                    # Homologar clave de shop: params["shop"] -> params["shop_id"]
                    for accion in ev.get("acciones", []):
                        p = accion.get("params", {})
                        if "shop" in p and "shop_id" not in p:
                            p["shop_id"] = p.pop("shop")
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
        elif self._bloqueo_por == "choice":
            if not estado.mostrando_opciones:
                self._bloqueo_por = None
        elif self._bloqueo_por == "dialogo_tree":
            if not estado.dialogo.activo and not estado.mostrando_opciones:
                self._bloqueo_por = None
        elif self._bloqueo_por == "shop":
            if not getattr(estado, "shop_actual", None):
                self._bloqueo_por = None
                self._avanzar_arbol_dialogo(estado)
        elif self._bloqueo_por == "minijuego":
            if not estado.mostrando_minijuego:
                self._bloqueo_por = None

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
        # Eventos globales que observan la finalización de este evento
        eg = getattr(self.estado, "eventos_globales", None)
        if eg is not None:
            eg.on_event_finalized(eid)
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
        # Eventos globales que reaccionan a la derrota de este boss
        eg = getattr(self.estado, "eventos_globales", None)
        if eg is not None:
            eg.on_boss_defeated(boss_id)
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

    def _check_conditions(self, condiciones, extra=None, ctx=None):
        """Evalúa condiciones de un evento.

        Acepta un EventContext opcional. Si no se pasa, construye uno interno
        con self.estado y el extra dict (compatibilidad con llamadas previas).
        """
        if ctx is None:
            from systems.event_context import EventContext
            ctx = EventContext(
                state=self.estado,
                source=getattr(self.estado, "snake", None),
                custom=extra or {},
            )
        estado = ctx.state
        extra = ctx.custom
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

            elif ct == "has_moneda":
                actual = self._moneda_valor(params.get("moneda", ""))
                if actual is None:
                    return False
                if not self._eval(actual, op, int(valor)):
                    return False

            elif ct == "item_count":
                item = params.get("item", "")
                if ctx.inventario is None:
                    return False
                actual = ctx.inventario.cantidad(item)
                if not self._eval(actual, op, int(valor)):
                    return False

            elif ct == "flag":
                flag = params.get("flag", "")
                if ctx.flags is None:
                    return False
                actual = ctx.flags.get(flag)
                if op in ("es_verdadero", "es_falso"):
                    valido = bool(actual)
                    if op == "es_verdadero" and not valido:
                        return False
                    if op == "es_falso" and valido:
                        return False
                else:
                    if actual is None:
                        return False
                    esperado = params.get("valor", 1)
                    if isinstance(actual, str) or isinstance(esperado, str):
                        if op not in ("==", "!="):
                            return False
                        if (op == "==") != (str(actual) == str(esperado)):
                            return False
                    else:
                        if not isinstance(actual, (int, float)):
                            try:
                                actual = int(actual)
                            except (ValueError, TypeError):
                                return False
                        try:
                            esperado = int(esperado)
                        except (ValueError, TypeError):
                            esperado = 1
                        if not self._eval(actual, op, esperado):
                            return False

            elif ct == "ability":
                ability = params.get("ability", "")
                if ctx.habilidades is None:
                    return False
                actual = ctx.habilidades.tiene_habilidad(ability)
                if op == "tiene" and not actual:
                    return False
                if op == "no_tiene" and actual:
                    return False

            elif ct == "ability_equipped":
                ability = params.get("ability", "")
                if ctx.habilidades is None:
                    return False
                tiene = ctx.habilidades.tiene_habilidad(ability)
                equipada = ctx.habilidades.habilidad_equipada == ability
                if op == "equipado" and not (tiene and equipada):
                    return False
                if op == "no_equipado" and (tiene and equipada):
                    return False

            elif ct == "pp":
                if ctx.habilidades is None:
                    return False
                actual = ctx.habilidades.get_pp_actual()
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

    # ── Monedas (contadores de primera clase) ──────────────
    # La moneda orm "escamas" sigue ligada a la snake (shim). Otras monedas
    # usan game_state.monedas. El desacople de "escamas == largo" es un tema aparte.

    def _moneda_valor(self, mid):
        estado = self.estado
        if mid == "escamas" and hasattr(estado, "snake"):
            return estado.snake.get_escamas()
        if hasattr(estado, "monedas"):
            if mid in estado.monedas.ids():
                return estado.monedas.get(mid, 0)
        return None

    def _moneda_dar(self, mid, cantidad):
        estado = self.estado
        if mid == "escamas" and hasattr(estado, "snake"):
            estado.snake.crecer(cantidad)
            return
        if hasattr(estado, "monedas"):
            estado.monedas.dar(mid, cantidad)

    def _moneda_quitar(self, mid, cantidad):
        estado = self.estado
        if mid == "escamas" and hasattr(estado, "snake"):
            estado.snake.perder_escamas(cantidad)
            return
        if hasattr(estado, "monedas"):
            estado.monedas.quitar(mid, cantidad)

    # ── Árbol de diálogo ──────────────────────────────────

    def _avanzar_arbol_dialogo(self, estado):
        if not self._arbol_dialogo:
            self._bloqueo_por = None
            return
        ad = self._arbol_dialogo
        personaje = ad["personaje"]
        contexto = ad["contexto"]
        from systems.dialogo import RUTA_DIALOGOS
        import json, os
        tree_data = None
        if os.path.exists(RUTA_DIALOGOS):
            with open(RUTA_DIALOGOS, "r", encoding="utf-8") as f:
                raw = json.load(f)
            ctx_data = raw.get(personaje, {}).get(contexto, {})
            if isinstance(ctx_data, dict) and "nodes" in ctx_data:
                tree_data = ctx_data

        if not tree_data:
            self._arbol_dialogo = None
            self._bloqueo_por = None
            return

        nodes = tree_data["nodes"]
        nid = ad.get("nid_actual")
        if not nid:
            if ad.get("_iniciado"):
                self._arbol_dialogo = None
                self._bloqueo_por = None
                return
            nid = tree_data.get("start", "")
            ad["_iniciado"] = True
        if not nid or nid not in nodes:
            self._arbol_dialogo = None
            self._bloqueo_por = None
            return

        node = nodes[nid]
        tipo = node.get("tipo", "")

        if tipo == "dialogo":
            texto = node.get("texto", "")
            quien = node.get("quien", personaje)
            estado.dialogo.iniciar_inline([texto], boss_nombre=quien)
            ad["nid_actual"] = node.get("next", "")
            # Cuando termine el diálogo, seguimos
            estado.dialogo.al_terminar = lambda: self._on_arbol_dialogo_end(estado)

        elif tipo == "opcion":
            choices = node.get("choices", [])
            opts = []
            for ch in choices:
                opts.append({
                    "texto": ch.get("texto", ""),
                    "acciones": [{"tipo": "_arbol_choice", "params": {"destino": ch.get("next", "")}}],
                })
            estado.mostrando_opciones = True
            estado.opciones = opts
            estado.opcion_seleccionada = -1
            self._bloqueo_por = "choice"
            # Guardamos el contexto para cuando elijan
            ad["_pendiente"] = True

        elif tipo == "condicion":
            flag = node.get("flag", "")
            operador = node.get("operador", "==")
            valor = node.get("valor", "")
            if hasattr(estado, "flags"):
                actual = estado.flags.get(flag)
                if actual is None:
                    cumple = False
                elif isinstance(actual, str) or isinstance(valor, str):
                    cumple = (operador == "==" and str(actual) == str(valor)) or \
                             (operador == "!=" and str(actual) != str(valor))
                else:
                    try:
                        cumple = self._eval(actual, operador, int(valor))
                    except (ValueError, TypeError):
                        cumple = False
            else:
                cumple = False
            ad["nid_actual"] = node.get("next" if cumple else "next_false", "")
            self._avanzar_arbol_dialogo(estado)

        elif tipo == "accion":
            tipo_accion = node.get("tipo_accion", "")
            params = node.get("params", {})
            self._ejecutar_accion(tipo_accion, params, 0, 0, 0)
            ad["nid_actual"] = node.get("next", "")
            if tipo_accion == "open_shop":
                self._bloqueo_por = "shop"
                return
            self._avanzar_arbol_dialogo(estado)

        elif tipo == "salto":
            destino = node.get("destino", "")
            if "/" in destino:
                dp, dc = destino.split("/", 1)
                ad["personaje"] = dp
                ad["contexto"] = dc
                ad["nid_actual"] = None
                self._avanzar_arbol_dialogo(estado)
            else:
                self._arbol_dialogo = None
                self._bloqueo_por = None

        else:
            self._arbol_dialogo = None
            self._bloqueo_por = None

    def _on_arbol_dialogo_end(self, estado):
        if self._arbol_dialogo:
            nid = self._arbol_dialogo.get("nid_actual", "")
            if nid:
                self._avanzar_arbol_dialogo(estado)
            else:
                self._arbol_dialogo = None
                self._bloqueo_por = None

    def _ejecutar_acciones(self, acciones, x, y, z=0):
        for i, act in enumerate(acciones):
            print(f"[EVENTO] accion {i+1}: {act.get('tipo')} params={act.get('params', {})}")
            bloquea = self._ejecutar_accion(act.get("tipo"), act.get("params", {}), x, y, z)
            if bloquea:
                self._cola_acciones = acciones[i+1:]
                self._cola_ctx = (x, y, z)
                break

    def ejecutar_secuencia(self, acciones, ctx=None):
        self._cola_acciones = acciones
        self._cola_ctx = ctx if ctx is not None else (0, 0, 0)
        self._procesar_cola()

    def _procesar_cola(self):
        if not self._cola_acciones:
            return
        acciones = self._cola_acciones
        self._cola_acciones = []
        self._ejecutar_acciones(acciones, *self._cola_ctx)

    def ejecutar_ahora(self, accion_dict):
        tipo = accion_dict.get("tipo", "")
        params = accion_dict.get("params", {})
        self._ejecutar_accion(tipo, params, 0, 0, 0)

    def _mostrar_opciones_plano(self, estado):
        """Convierte options[0] de un diálogo plano a estado.opciones (acciones directas)."""
        options = getattr(estado.dialogo, "options", []) if hasattr(estado, "dialogo") else []
        if not options:
            self._bloqueo_por = None
            return
        opt = options[0]
        choices = opt.get("choices", [])
        estado.opcion_pregunta = opt.get("text", "")
        estado.opciones = []
        for ch in choices:
            params = {k: v for k, v in ch.items() if k not in ("text", "action")}
            # Homologar clave de shop legacy -> shop_id
            if "shop" in params and "shop_id" not in params:
                params["shop_id"] = params.pop("shop")
            estado.opciones.append({
                "texto": ch.get("text", ""),
                "acciones": [{"tipo": ch.get("action", ""), "params": params}],
            })
        estado.opcion_seleccionada = -1
        estado.mostrando_opciones = True
        self._bloqueo_por = "choice"

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
                estado.dialogo.iniciar(personaje, contexto,
                                       al_terminar=lambda: self._mostrar_opciones_plano(estado))
                self._bloqueo_por = "dialogo"
                return True

        elif accion == "start_dialog":
            dialogo_id = params.get("dialog", "") or params.get("dialogo_id", "")
            if "/" in dialogo_id and hasattr(estado, "dialogo"):
                personaje, contexto = dialogo_id.split("/", 1)
                estado.dialogo.iniciar(personaje, contexto,
                                       al_terminar=lambda: self._mostrar_opciones_plano(estado))
                self._bloqueo_por = "dialogo"
                return True

        elif accion == "close_dialog":
            if hasattr(estado, "dialogo"):
                estado.dialogo.activo = False
                estado.dialogo.terminado = True
                estado.dialogo.al_terminar = None
            estado.mostrando_opciones = False
            estado.opciones = []
            self._bloqueo_por = None
            return True

        elif accion == "iniciar_dialogo":
            dialogo_id = params.get("dialogo_id", "")
            if "/" in dialogo_id and hasattr(estado, "dialogo"):
                personaje, contexto = dialogo_id.split("/", 1)
                estado.dialogo.iniciar(personaje, contexto,
                                       al_terminar=lambda: self._mostrar_opciones_plano(estado))
                self._bloqueo_por = "dialogo"
                return True

        elif accion == "dialogo_inline":
            lineas = params.get("lineas", [])
            quien = params.get("quien", "")
            if lineas and hasattr(estado, "dialogo"):
                estado.dialogo.iniciar_inline(lineas, boss_nombre=quien)
                self._bloqueo_por = "dialogo"
                return True

        elif accion == "dialogo_tree":
            dialogo_id = params.get("dialogo_id", "")
            if "/" in dialogo_id and hasattr(estado, "dialogo"):
                personaje, contexto = dialogo_id.split("/", 1)
                self._arbol_dialogo = {
                    "personaje": personaje,
                    "contexto": contexto,
                    "nid_actual": None,
                    "_iniciado": False,
                }
                self._avanzar_arbol_dialogo(estado)
                self._bloqueo_por = "dialogo_tree"
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

        elif accion == "abrir_menu":
            menu_id = params.get("menu_id", "")
            if menu_id and hasattr(estado, "menu") and hasattr(estado.menu, "abrir_menu"):
                estado.mostrando_inventario = True
                estado.menu.abrir_menu(menu_id)

        elif accion == "give_item":
            item = params.get("item", "")
            cantidad = int(params.get("cantidad", 1))
            if item and hasattr(estado, "inventario"):
                estado.inventario.agregar_item(item, cantidad)
                repo = RepositorioObjetos()
                cfg = repo.get_objeto(item)
                es_clave = cfg.get("tipo") == "objeto_clave" if cfg else False
                nombre = cfg.get("nombre", item) if cfg else item
                if es_clave:
                    mensaje = f"¡Obtuviste [Objeto Clave] {nombre}!"
                    estado.tiempo_mensaje = 90
                    if hasattr(estado, "menu") and hasattr(estado.menu, "abrir_apartado"):
                        estado.menu.abrir_apartado("key_items")
                else:
                    mensaje = f"¡{nombre} x{cantidad}!"
                    estado.tiempo_mensaje = 60
                estado.mensaje_temporal = mensaje

        elif accion == "examinar_key_item":
            item = params.get("item", "")
            if item and hasattr(estado, "inventario"):
                repo = RepositorioObjetos()
                cfg = repo.get_objeto(item)
                desc = cfg.get("descripcion", "Sin descripción") if cfg else "Sin descripción"
                estado.mensaje_temporal = f"{desc}"
                estado.tiempo_mensaje = 120

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
            valor = params.get("valor", True)
            if flag and hasattr(estado, "flags"):
                estado.flags.set(flag, valor)

        elif accion == "add_flag":
            flag = params.get("flag", "")
            cantidad = int(params.get("cantidad", 1))
            if flag and hasattr(estado, "flags"):
                estado.flags.add(flag, cantidad)

        elif accion == "clear_flag":
            flag = params.get("flag", "")
            if flag and hasattr(estado, "flags"):
                estado.flags.set(flag, False)

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

        elif accion == "give_moneda":
            self._moneda_dar(params.get("moneda", ""),
                             int(params.get("cantidad", 1)))

        elif accion == "remove_moneda":
            self._moneda_quitar(params.get("moneda", ""),
                                int(params.get("cantidad", 1)))

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

        elif accion == "iniciar_minijuego":
            minijuego_id = params.get("minijuego_id", "")
            if minijuego_id and hasattr(estado, "sistema_minijuego"):
                ok = estado.sistema_minijuego.iniciar(minijuego_id)
                if ok:
                    estado.mostrando_minijuego = True
                    estado.minijuego_id = minijuego_id
                    self._bloqueo_por = "minijuego"
                    return True

        elif accion == "ir_a_escena":
            capitulo_idx = int(params.get("capitulo", 0))
            escena_idx = int(params.get("escena", 0))
            if hasattr(estado, "_scene_navegacion"):
                estado._scene_navegacion = (capitulo_idx, escena_idx)
            estado.cambiando_nivel = True
            if hasattr(estado, "audio") and estado.audio.get_current_bgm():
                estado.audio.stop_bgm(500)

        elif accion == "play_bgm":
            asset_id = params.get("asset_id", "")
            fade_ms = int(params.get("fade_ms", 0))
            if asset_id and hasattr(estado, "audio"):
                estado.audio.play_bgm(asset_id, fade_ms)

        elif accion == "stop_bgm":
            fade_ms = int(params.get("fade_ms", 0))
            if hasattr(estado, "audio"):
                estado.audio.stop_bgm(fade_ms)

        elif accion == "play_sfx":
            asset_id = params.get("asset_id", "")
            if asset_id and hasattr(estado, "audio"):
                estado.audio.play_sfx(asset_id)

        elif accion == "set_bgm_volume":
            vol = float(params.get("volumen", 1.0))
            if hasattr(estado, "audio"):
                estado.audio.set_bgm_volume(vol)

        elif accion == "set_sfx_volume":
            vol = float(params.get("volumen", 1.0))
            if hasattr(estado, "audio"):
                estado.audio.set_sfx_volume(vol)

        elif accion == "set_resolution":
            ancho = int(params.get("ancho", 0))
            alto = int(params.get("alto", 0))
            if ancho > 0 and alto > 0:
                from display import set_window_size
                set_window_size((ancho, alto))
                from systems import user_prefs
                prefs = user_prefs.load()
                prefs["resolution"] = f"{ancho}x{alto}"
                user_prefs.save(prefs)

        elif accion == "set_volume":
            vol = float(params.get("volumen", 1.0))
            if hasattr(estado, "audio"):
                estado.audio.set_bgm_volume(vol)
                estado.audio.set_sfx_volume(vol)
                from systems import user_prefs
                prefs = user_prefs.load()
                prefs["bgm_volume"] = vol
                prefs["sfx_volume"] = vol
                user_prefs.save(prefs)

        elif accion == "cambiar_fondo":
            sprite_id = params.get("sprite_id", "")
            if sprite_id and hasattr(estado, "fondo_activo"):
                estado.fondo_activo = sprite_id
                estado.fondo_modo = params.get("modo", "fill")

        elif accion == "mostrar_personaje":
            personaje_id = params.get("personaje_id", "")
            posicion = params.get("posicion", "centro")
            expresion = params.get("expresion", "normal")
            if personaje_id and hasattr(estado, "personajes_visibles"):
                sprite_name = f"personajes/{personaje_id}_{expresion}"
                pos_map = {"izquierda": 0, "centro": 1, "derecha": 2}
                estado.personajes_visibles[personaje_id] = {
                    "sprite": sprite_name,
                    "posicion": pos_map.get(posicion, 1),
                    "x": 0,
                    "y": 0,
                }

        elif accion == "ocultar_personaje":
            personaje_id = params.get("personaje_id", "")
            if personaje_id and hasattr(estado, "personajes_visibles"):
                estado.personajes_visibles.pop(personaje_id, None)

        elif accion == "ocultar_todos_personajes":
            if hasattr(estado, "personajes_visibles"):
                estado.personajes_visibles.clear()

        elif accion == "mostrar_opciones":
            opciones_data = params.get("opciones", [])
            if opciones_data and hasattr(estado, "mostrando_opciones"):
                estado.mostrando_opciones = True
                estado.opciones = opciones_data
                estado.opcion_seleccionada = -1
                self._bloqueo_por = "choice"
                return True

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
                if hasattr(estado, "ejecutar_golpe_q"):
                    estado.ejecutar_golpe_q()
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

        elif accion == "_arbol_choice":
            destino = params.get("destino", "")
            if self._arbol_dialogo:
                self._arbol_dialogo["nid_actual"] = destino
                self._avanzar_arbol_dialogo(estado)

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

        elif accion == "open_shop":
            shop_id = params.get("shop_id", "") or params.get("shop", "")
            if shop_id and hasattr(estado, "shop_system"):
                shop = estado.shop_system.get_shop(shop_id)
                if shop:
                    estado.shop_actual = shop
                    if hasattr(estado, "menu") and hasattr(estado.menu, "abrir_menu"):
                        estado.menu.abrir_menu("shop")
                    estado.mostrando_inventario = True

        elif accion == "open_save_menu":
            if hasattr(estado, "menu") and hasattr(estado.menu, "abrir_menu"):
                estado.mostrando_inventario = True
                estado.menu.abrir_menu("save")

        elif accion == "open_load_menu":
            if hasattr(estado, "menu") and hasattr(estado.menu, "abrir_menu"):
                estado.mostrando_inventario = True
                estado.menu.abrir_menu("load")

        elif accion == "close_shop":
            if hasattr(estado, "shop_actual"):
                estado.shop_actual = None
            estado.mostrando_inventario = False
            if hasattr(estado, "menu") and hasattr(estado.menu, "cerrar"):
                estado.menu.cerrar()

        elif accion == "close_save_menu":
            if hasattr(estado, "menu") and hasattr(estado.menu, "cerrar"):
                estado.menu.cerrar()
            estado.mostrando_inventario = False

        elif accion == "increment_contador":
            contador_id = params.get("contador_id", "")
            cantidad = int(params.get("cantidad", 1))
            if contador_id and hasattr(estado, "contadores"):
                estado.contadores.add(contador_id, cantidad)

        elif accion == "set_contador":
            contador_id = params.get("contador_id", "")
            valor = int(params.get("valor", 0))
            if contador_id and hasattr(estado, "contadores"):
                estado.contadores.set(contador_id, valor)

        elif accion == "restock_shop":
            shop_id = params.get("shop_id", "")
            item_id = params.get("item_id", "")
            if shop_id and hasattr(estado, "shop_system"):
                estado.shop_system.restockear(shop_id, item_id or None)

        elif accion == "add_shop_stock":
            shop_id = params.get("shop_id", "")
            item_id = params.get("item_id", "")
            cantidad = int(params.get("cantidad", 1))
            if shop_id and item_id and hasattr(estado, "shop_system"):
                estado.shop_system.anadir_stock(shop_id, item_id, cantidad)

        elif accion == "modify_shop_price":
            shop_id = params.get("shop_id", "")
            item_id = params.get("item_id", "")
            moneda = params.get("moneda", "")
            nuevo_precio = int(params.get("precio", 0))
            if shop_id and item_id and moneda and hasattr(estado, "shop_system"):
                estado.shop_system.modificar_precio(shop_id, item_id, moneda, nuevo_precio)

        elif accion == "trigger_restock":
            # Mecanismo v1 eliminado: el restock lo manejan los eventos globales.
            pass

        elif accion == "save_game":
            slot = int(params.get("slot", 1))
            dev = params.get("dev", False)
            if isinstance(dev, str):
                dev = dev.lower() in ("true", "1", "si")
            if hasattr(estado, "save_system"):
                ok, msg = estado.save_system.guardar_slot(slot, dev=dev)
                estado.mensaje_temporal = msg
                estado.tiempo_mensaje = 90

        elif accion == "load_game":
            slot = int(params.get("slot", 1))
            dev = params.get("dev", False)
            if isinstance(dev, str):
                dev = dev.lower() in ("true", "1", "si")
            if hasattr(estado, "save_system"):
                ok, msg = estado.save_system.cargar_slot(slot, dev=dev)
                estado.mensaje_temporal = msg
                estado.tiempo_mensaje = 90

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
