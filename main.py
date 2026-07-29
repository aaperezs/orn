# main.py
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

_MODO_TEST = "--test" in sys.argv


import pygame

# Set up project path for editor data modules
from editor.project import set_current_project

set_current_project(os.path.dirname(os.path.abspath(__file__)))
from configs import *
from entities.food import Food
from entities.segmento_perdido import SegmentoPerdido
from game_state import GameState
from handlers.input_manager import InputManager
from managers.colision_manager import ColisionManager
from managers.combate_manager import CombateManager
from managers.comida_manager import ComidaManager
from systems.event_bus import EventoObjetoDestruido
from systems.ui import UI


# ============================================
# INICIALIZACIÓN
# ============================================

pygame.init()
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("ORM - El Vástago del Mundo")
reloj = pygame.time.Clock()

# Cargar config de pantallas una vez (splash, title, menu, prologue)
_SCREENS_CFG = {}
if not _MODO_TEST:
    import json
    try:
        with open(os.path.join(os.path.dirname(__file__), "cururo.json"), encoding="utf-8") as f:
            manifest = json.load(f)
        _SCREENS_CFG = manifest.get("screens", {})
    except Exception:
        pass

# ============================================
# FUNCIONES AUXILIARES (definidas una vez, usan `estado` como global)
# ============================================

def mostrar_mensaje(texto, duracion=60):
    estado.mensaje_temporal = texto
    estado.tiempo_mensaje = duracion



def perder_segmentos(cantidad):
    """Maneja la pérdida de segmentos - NUNCA baja de 3, pero si tiene 3 muere"""
    if estado.snake.invencible or estado.god_mode:
        return False

    longitud_actual = estado.snake.get_longitud()

    if longitud_actual <= 3:
        estado.game_over = True
        estado.death_cause = f"Longitud mínima ({longitud_actual} segs)"
        mostrar_mensaje("¡Has muerto! (longitud mínima)", 60)
        cabeza = estado.snake.get_cabeza()
        if cabeza:
            estado.particles.crear_explosion(
                cabeza[0] + TAMANO_CELDA//2,
                cabeza[1] + TAMANO_CELDA//2,
                30, ROJO
            )
        return True

    max_perder = longitud_actual - 3
    if cantidad > max_perder:
        cantidad = max_perder

    if cantidad <= 0:
        return False

    perdidos = estado.snake.perder_segmentos(cantidad)

    if perdidos:
        for pos in perdidos:
            if pos:
                segmento = SegmentoPerdido(pos[0], pos[1], estado.nivel_ancho, estado.nivel_alto)
                estado.segmentos_perdidos.append(segmento)

        cabeza = estado.snake.get_cabeza()
        if cabeza:
            estado.particles.crear_explosion(
                cabeza[0] + TAMANO_CELDA//2,
                cabeza[1] + TAMANO_CELDA//2,
                cantidad=15, color=VERDE
            )

        mostrar_mensaje(f"¡Perdiste {len(perdidos)} segmentos!", 60)

        if estado.snake.get_longitud() <= 3:
            pass

    return False

def recoger_segmentos():
    """Recoge segmentos perdidos"""
    cabeza = estado.snake.get_cabeza()
    if not cabeza:
        return

    cabeza_rect = pygame.Rect(cabeza[0], cabeza[1], TAMANO_CELDA, TAMANO_CELDA)

    for segmento in estado.segmentos_perdidos[:]:
        if segmento.esta_vivo() and not segmento.recogido:
            if cabeza_rect.colliderect(segmento.get_rect()):
                segmento.recogido = True
                estado.snake.crecer(1)
                cx = segmento.x + TAMANO_CELDA // 2
                cy = segmento.y + TAMANO_CELDA // 2
                estado.text_service.spawn("+1", cx, cy - 10, 30, VERDE_CLARO)
                estado.particles.crear_anillo_sonico(cx, cy, (100, 255, 100))
                estado.segmentos_perdidos.remove(segmento)
        elif not segmento.esta_vivo() and not segmento.recogido:
            estado.segmentos_perdidos.remove(segmento)



# ============================================
# FUNCIÓN DE DIBUJADO
# ============================================

def dibujar():
    pantalla.fill(FOREST_BG)
    ox, oy = estado.camera.get_offset()
    from utils.sprite_manager import obtener as obtener_sprite
    pasto_sprite = obtener_sprite("pasto")
    deco_sprites = [obtener_sprite(f"deco_{i}") for i in range(4)]
    deco_hash = (estado.nivel_ancho + estado.nivel_alto) ^ 42

    en_arena = estado.arena_boss.activa and estado.boss and estado.boss.vivo
    z_overlay = []

    if not en_arena or estado.arena_boss.es_nivel_completo:
        cols_totales = estado.nivel_ancho // TAMANO_CELDA
        rows_totales = estado.nivel_alto // TAMANO_CELDA
        first_col = max(0, -ox // TAMANO_CELDA)
        first_row = max(0, -oy // TAMANO_CELDA)
        last_col = min(cols_totales - 1, (-ox + ANCHO) // TAMANO_CELDA)
        last_row = min(rows_totales - 1, (-oy + ALTO) // TAMANO_CELDA)
        z_layers = sorted(estado.grid_por_capa.keys())
        z_ground = [z for z in z_layers if z <= 1]
        z_overlay[:] = [z for z in z_layers if z >= 2]

        def _draw_tiles(z_list):
            for row in range(first_row, last_row + 1):
                for col in range(first_col, last_col + 1):
                    px = col * TAMANO_CELDA + ox
                    py = row * TAMANO_CELDA + oy
                    for z in z_list:
                        layer_grid = estado.grid_por_capa[z]
                        override_key = (col, row, z)
                        if override_key in estado.tile_overrides:
                            ov = estado.tile_overrides[override_key]
                            if ov is not None:
                                sp = obtener_sprite(ov)
                                if sp:
                                    pantalla.blit(sp, (px, py))
                        else:
                            sprite_id = layer_grid.get((col, row))
                            if sprite_id:
                                sp = obtener_sprite(sprite_id)
                                if sp:
                                    pantalla.blit(sp, (px, py))

        # Pass 1: ground tiles (Z <= Z_MAPA_PRINCIPAL)
        for row in range(first_row, last_row + 1):
            for col in range(first_col, last_col + 1):
                px = col * TAMANO_CELDA + ox
                py = row * TAMANO_CELDA + oy
                pantalla.blit(pasto_sprite, (px, py))
                d = (col * 7 + row * 13 + deco_hash) % 25
                if d < 4 and deco_sprites[d]:
                    pantalla.blit(deco_sprites[d], (px, py))
                for z in z_ground:
                    layer_grid = estado.grid_por_capa[z]
                    override_key = (col, row, z)
                    if override_key in estado.tile_overrides:
                        ov = estado.tile_overrides[override_key]
                        if ov is not None:
                            sp = obtener_sprite(ov)
                            if sp:
                                pantalla.blit(sp, (px, py))
                    else:
                        sprite_id = layer_grid.get((col, row))
                        if sprite_id:
                            sp = obtener_sprite(sprite_id)
                            if sp:
                                pantalla.blit(sp, (px, py))

        # Entities (Z-sorted)
        _entity_groups = {}
        _entity_groups = {}
        def _add_entity(e, z_attr="z"):
            z = getattr(e, z_attr, 0)
            _entity_groups.setdefault(z, []).append(e)
        for e in estado.decorativos:  _add_entity(e)
        for e in estado.hierba_alta:  _add_entity(e)
        for e in estado.paredes:      _add_entity(e)
        for e in estado.bloqueantes:  _add_entity(e)
        for e in estado.bloques_acero: _add_entity(e)
        for z in sorted(_entity_groups.keys()):
            for e in _entity_groups[z]:
                e.dibujar(pantalla, ox, oy)
        # Food always drawn on top of all Z-sorted entities
        if comida_manager.comida_disponible():
            estado.comida.dibujar(pantalla, ox, oy)

    # Always draw arena boss (handles inactive/active internally)
    estado.arena_boss.dibujar(pantalla, ox, oy)
    estado.portal_boss.dibujar(pantalla, ox, oy)

    if not estado.arena_boss.activa:
        for enemigo in estado.enemigos:
            enemigo.dibujar(pantalla, ox, oy)

    for segmento in estado.segmentos_perdidos:
        segmento.dibujar(pantalla, ox, oy)

    habilidad_equipada = estado.habilidades.get_habilidad_equipada()
    tiene_manto = (habilidad_equipada and
                  habilidad_equipada.get("efecto") == "manto" and
                  estado.habilidades.get_pp_actual() > 0)

    estado.snake.dibujar(pantalla, tiene_manto, ox, oy)
    estado.particles.dibujar(pantalla, ox, oy)

    # Pass 2: overlay tiles (Z > Z_MAPA_PRINCIPAL) — se dibujan encima de entidades y snake
    if not en_arena and z_overlay:
        for row in range(first_row, last_row + 1):
            for col in range(first_col, last_col + 1):
                px = col * TAMANO_CELDA + ox
                py = row * TAMANO_CELDA + oy
                for z in z_overlay:
                    layer_grid = estado.grid_por_capa.get(z, {})
                    override_key = (col, row, z)
                    if override_key in estado.tile_overrides:
                        ov = estado.tile_overrides[override_key]
                        if ov is not None:
                            sp = obtener_sprite(ov)
                            if sp:
                                pantalla.blit(sp, (px, py))
                    else:
                        sprite_id = layer_grid.get((col, row))
                        if sprite_id:
                            sp = obtener_sprite(sprite_id)
                            if sp:
                                pantalla.blit(sp, (px, py))

    # Textos flotantes (nuevo sistema)
    estado.text_service.draw(pantalla)
    # Legacy floating texts
    fuente_flotante = pygame.font.SysFont("Arial", 18, bold=True)
    for tf in estado.textos_flotantes:
        alpha = int(255 * (tf["timer"] / max(tf["max_timer"], 1)))
        color = (*tf["color"][:3], alpha)
        surf = pygame.Surface((60, 30), pygame.SRCALPHA)
        txt = fuente_flotante.render(tf["texto"], True, color[:3])
        txt.set_alpha(alpha)
        surf.blit(txt, (30 - txt.get_width() // 2, 0))
        pantalla.blit(surf, (tf["x"] + ox - 30, tf["y"] + oy))

    ui.dibujar(pantalla, estado.snake, estado.comida, estado.mensaje_temporal)
    estado.habilidades.dibujar_ui(pantalla)

    fuente = pygame.font.SysFont("Arial", 12)
    texto = fuente.render("E: Interactuar | Q: Habilidad | TAB: Cambiar", True, GRIS)
    pantalla.blit(texto, (ANCHO - 310, 80))

    # Oscurecer fondo durante diálogo post-boss para evitar teleport visual
    if estado.dialogo.activo and estado.arena_boss.activa and estado.boss:
        overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        pantalla.blit(overlay, (0, 0))

# ============================================
# BUCLE PRINCIPAL (outer: menu → juego → menu ...)
# ============================================

while True:
    estado = GameState()
    ui = UI()
    move_accumulator = 0.0

    # ── Managers ──
    combate_manager = CombateManager(estado, mostrar_mensaje, perder_segmentos)
    comida_manager = ComidaManager(estado)
    colision_manager = ColisionManager(estado, perder_segmentos, mostrar_mensaje)
    event_handler = InputManager(estado, mostrar_mensaje)

    # ── Botín al destruir objetos ──
    from repositories import RepositorioBotin

    def _on_objeto_destruido(evento):
        """Cuando un objeto se destruye, puede dropear minerales"""
        if evento.tipo != "bloqueante":
            return
        _repo_botin = RepositorioBotin()
        evento_id, config = _repo_botin.obtener_drop_aleatorio()
        if evento_id and config:
            tipo = config.get("tipo")
            nombre = config.get("nombre", evento_id)
            icono = config.get("icono", "")
            if tipo == "mineral":
                estado.inventario.agregar_item(evento_id, 1)
                mostrar_mensaje(f"{icono} ¡Encontraste {nombre}!", 60)
            elif tipo == "gema":
                estado.inventario.agregar_item(evento_id, 1)
                estado.habilidades.recargar_pp(cantidad=5)
                mostrar_mensaje(f"{icono} ¡{nombre}! PP recuperados!", 60)
            elif tipo == "escama":
                estado.snake.crecer(1)
                mostrar_mensaje(f"{icono} ¡{nombre}! +1 segmento!", 60)

    estado.event_bus.suscribir(EventoObjetoDestruido, _on_objeto_destruido)

    # ── Pantallas (splash, título, menú, prólogo) ──
    if SCREENS_ENABLED and not _MODO_TEST:
        from systems.screen_manager import ScreenManager
        sm = ScreenManager(pantalla, _SCREENS_CFG)
        sm.run()

    # ── Game loop ──
    while estado.corriendo:
        # --- INPUT (siempre, incluso durante game over / dialogos) ---
        event_handler.process_events()

        # --- PAUSA ---
        if estado.pausa:
            ui.mostrar_pausa(pantalla)
            pygame.display.flip()
            reloj.tick(10)
            continue

        # --- FORJA ---
        if estado.mostrando_forja:
            estado.sistema_forja.actualizar()
            dibujar()
            estado.sistema_forja.dibujar(pantalla)
            pygame.display.flip()
            reloj.tick(10)
            continue

        # --- MENÚS ---
        if estado.mostrando_trueque:
            ui.mostrar_menu_trueque(pantalla, estado.snake)
            continue

        if estado.mostrando_inventario:
            ui.mostrar_inventario(pantalla, estado.habilidades)
            continue

        # --- GAME OVER ---
        if estado.game_over:
            if estado.death_cause:
                print(f"[MUERTE] {estado.death_cause}")
                estado.death_cause = ""
            ui.mostrar_game_over(pantalla, estado.snake, estado)
            pygame.display.flip()
            reloj.tick(10)
            continue

        # --- DIALOGO (pausa el juego) ---
        if estado.dialogo.activo:
            estado.dialogo.actualizar()
            estado.stack_manager.actualizar(estado)
            dibujar()
            estado.dialogo.dibujar(pantalla)
            pygame.display.flip()
            reloj.tick(10)
            continue

        # --- VENTANA (pantalla completa tipo cutscene) ---
        if estado.ventana.activo:
            estado.ventana.actualizar()
            estado.stack_manager.actualizar(estado)
            estado.ventana.dibujar(pantalla)
            pygame.display.flip()
            reloj.tick(10)
            continue

        # --- MOVIMIENTO (FPS fijo, movimiento por acumulador) ---
        move_accumulator += estado.get_speed_multiplier()
        movio = False
        while move_accumulator >= 1.0:
            estado.snake.mover(desplazar=True)
            move_accumulator -= 1.0
            movio = True
        if not movio:
            estado.snake.mover(desplazar=False)

        # Actualizar cooldown de enroscamiento (previene bucle infinito roca-pared)
        if hasattr(estado.snake, '_no_enroscar_hasta') and estado.snake._no_enroscar_hasta > 0:
            estado.snake._no_enroscar_hasta -= 1

        # --- PROCESAR ACCIONES DE EVENTOS (esperar, comando_automatico, etc.) ---
        estado.stack_manager.actualizar(estado)

        # --- CÁMARA ---
        cabeza = estado.snake.get_cabeza()
        if cabeza:
            estado.camera.seguir(cabeza)
            estado.camera.actualizar()

        # --- CAMBIO DE NIVEL ---
        if estado.cambiando_nivel:
            destino = estado.gate_destino
            estado.cambiar_nivel(destino)
            continue

        # --- COMIDA ---
        comida_manager.actualizar()

        # --- COLISIONES ---
        if colision_manager.verificar_colisiones():
            continue
        if colision_manager.verificar_autocolision():
            continue
        colision_manager.verificar_gate()
        colision_manager.verificar_avance_libre()

        # --- COMBATE ---
        if combate_manager.actualizar_enemigos():
            continue
        if combate_manager.actualizar_jefe():
            continue

        # --- EFECTOS DE EQUIPO ---
        estado.inventario.aplicar_todos_efectos(estado.snake, estado)

        # Regeneración de PP si hay objeto equipado que lo conceda
        for slot, obj in estado.inventario.equipo.items():
            for efecto in obj.efectos:
                if efecto.get("tipo") == "regeneracion_pp":
                    estado.habilidades.recargar_pp(cantidad=0.01)

        # --- SEGMENTOS PERDIDOS ---
        recoger_segmentos()
        for segmento in estado.segmentos_perdidos[:]:
            segmento.actualizar()
            if not segmento.esta_vivo() and not segmento.recogido:
                estado.segmentos_perdidos.remove(segmento)

        # --- TEXTOS FLOTANTES ---
        estado.text_service.update()
        for tf in estado.textos_flotantes[:]:
            tf["timer"] -= 1
            tf["y"] -= 1
            if tf["timer"] <= 0:
                estado.textos_flotantes.remove(tf)

        # --- PARTÍCULAS ---
        estado.particles.actualizar()

        # --- MENSAJE TEMPORAL ---
        if estado.tiempo_mensaje > 0:
            estado.tiempo_mensaje -= 1
            if estado.tiempo_mensaje == 0:
                estado.mensaje_temporal = ""

        # --- DIBUJADO ---
        dibujar()
        pygame.display.flip()
        reloj.tick(VELOCIDAD_DEUDA if estado.snake.tiene_deuda() else VELOCIDAD_BASE)

    # ── ¿Volver al menú o salir del juego? ──
    if not estado.volver_a_menu:
        break

pygame.quit()
