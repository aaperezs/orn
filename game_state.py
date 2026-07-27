from camera import Camera
from configs import *
from configs.constants import ALTO, ANCHO
from configs.z_layers import Z_ARENA_JEFE, Z_MAPA_PRINCIPAL
from domain.snake_context import SnakeContext
from domain.world_state import WorldState
from entities.inventario import Inventario
from entities.snake import Snake
from levels.level_manager import LevelManager
from services.text_service import TextService
from systems.dialogo import DialogoSystem
from systems.event_bus import BusEventos
from systems.habilidades import SistemaHabilidades
from systems.particles import ParticleSystem
from systems.stack_manager import StackManager
from systems.text_screen_player import TextScreenPlayer


class GameState:
    """Application layer: orchestrates SnakeContext + WorldState + infrastructure systems."""

    def __init__(self):
        # ── Infrastructure systems ──
        self.level_manager = LevelManager()
        self.particles = ParticleSystem()
        self.habilidades = SistemaHabilidades()
        self.event_bus = BusEventos()
        self.stack_manager = StackManager(self)
        self.dialogo = DialogoSystem()
        self.ventana = TextScreenPlayer()
        self.camera = Camera(ANCHO, ALTO)
        self.inventario = Inventario()
        from systems.forja import SistemaForja
        self.sistema_forja = SistemaForja(self)

        # ── Domain objects ──
        nivel = self.level_manager.obtener_nivel_actual()
        self.stack_manager.load_stacks(self.level_manager.obtener_id_actual())
        inicio_x, inicio_y = WorldState.posicion_inicio_static(nivel)
        snake = Snake(inicio_x, inicio_y, z=Z_MAPA_PRINCIPAL)
        snake.iniciar_dormido((inicio_x, inicio_y))
        self.snake_ctx = SnakeContext(snake)
        self.world = WorldState()
        self.world.cargar_entidades_nivel(nivel)
        self.world.inicializar_arena_boss(nivel, self.level_manager)
        self.world.crear_portal_boss(snake)
        if nivel['comidas']:
            self.world.comida = nivel['comidas'][0]
        else:
            self.world.spawn_comida(snake.body)

        # ── Session state ──
        self._jefe_derrotado = False
        self.death_cause = None
        self.corriendo = True
        self.pausa = False
        self.game_over = False
        self.mostrando_trueque = False
        self.mostrando_inventario = False
        self.mostrando_forja = False
        self.proyectiles_comidos = 0
        self.proyectiles_necesarios = 3
        self.mensaje_temporal = ""
        self.tiempo_mensaje = 0
        self.cambiando_nivel = False
        self.gate_destino = None
        self.gate_salida_id = None
        self.text_service = TextService(pool_size=64)
        self.textos_flotantes = []  # legacy — migrate to text_service
        self.flags = {}
        self.god_mode = False
        self.demo_habilidad_pendiente = False
        self.mandos_bloqueados = False
        self.nivel_origen = None
        self.demo_habilidad_id = None

        self._init_habilidades_iniciales()

        print(f"Nivel cargado: {self.level_manager.obtener_id_actual()}")
        print(f"   Inicio en: ({inicio_x}, {inicio_y}) [Z={Z_MAPA_PRINCIPAL}]")
        print(f"   Paredes: {len(self.world.paredes)}, Bloqueantes: {len(self.world.bloqueantes)}, "
              f"BloquesAcero: {len(self.world.bloques_acero)}, "
              f"Hierba: {len(self.world.hierba_alta)}, Enemigos: {len(self.world.enemigos)}")
        print(f"   Arena del jefe en Z={Z_ARENA_JEFE} (aislada)")

    # ────────────────────────────────────────────
    # Backward-compatible property delegation
    # ────────────────────────────────────────────

    @property
    def snake(self): return self.snake_ctx.snake

    @property
    def segmentos_perdidos(self): return self.snake_ctx.segmentos_perdidos
    @segmentos_perdidos.setter
    def segmentos_perdidos(self, v): self.snake_ctx.segmentos_perdidos = v

    @property
    def velocidad_extra(self): return self.snake_ctx.velocidad_extra
    @velocidad_extra.setter
    def velocidad_extra(self, v): self.snake_ctx.velocidad_extra = v

    @property
    def paredes(self): return self.world.paredes
    @property
    def bloqueantes(self): return self.world.bloqueantes
    @property
    def hierba_alta(self): return self.world.hierba_alta
    @property
    def bloques_acero(self): return self.world.bloques_acero
    @property
    def enemigos(self): return self.world.enemigos
    @property
    def decorativos(self): return self.world.decorativos
    @property
    def suelos(self): return self.world.suelos
    @property
    def arena_paredes(self): return self.world.arena_paredes
    @property
    def zonas_restringidas(self): return self.world.zonas_restringidas
    @property
    def terrenos_negados(self): return self.world.terrenos_negados
    @property
    def nivel_ancho(self): return self.world.nivel_ancho
    @property
    def nivel_alto(self): return self.world.nivel_alto
    @property
    def nivel_z0(self): return self.world.nivel_z0
    @property
    def grid(self): return self.world.grid
    @property
    def grid_por_capa(self): return self.world.grid_por_capa
    @property
    def zona_boss(self): return self.world.zona_boss
    @property
    def arena_boss(self): return self.world.arena_boss
    @property
    def boss(self): return self.world.boss
    @property
    def portal_boss(self): return self.world.portal_boss
    @property
    def comida(self): return self.world.comida
    @comida.setter
    def comida(self, v): self.world.comida = v
    @property
    def tile_overrides(self): return self.world.tile_overrides
    @tile_overrides.setter
    def tile_overrides(self, v): self.world.tile_overrides = v

    # ────────────────────────────────────────────

    def _init_habilidades_iniciales(self):
        from configs.debug import HABILIDADES_INICIALES
        for habilidad_id in HABILIDADES_INICIALES:
            if habilidad_id == "golpe_cabeza":
                self.habilidades.desbloquear_habilidad(HabilidadID.GOLPE_CABEZA)
            elif habilidad_id == "manto_oscuridad":
                self.habilidades.desbloquear_habilidad(HabilidadID.MANTO_OSCURIDAD)
            elif habilidad_id == "cola_latigo":
                self.habilidades.desbloquear_habilidad(HabilidadID.COLA_LATIGO)
            elif habilidad_id == "base":
                pass

    def get_speed_multiplier(self):
        return self.snake_ctx.get_speed_multiplier(self.world.hierba_alta, self.world.terrenos_negados)

    def replace_tile_sprite(self, gx, gy, sprite_id, z=0):
        self.world.replace_tile_sprite(gx, gy, sprite_id, z)
        self._update_decorativo_override(gx, gy, sprite_id, z)

    def remove_tile_sprite(self, gx, gy, z=0):
        self.world.remove_tile_sprite(gx, gy, z)
        self._update_decorativo_override(gx, gy, None, z)

    def _update_decorativo_override(self, gx, gy, sprite_id, z):
        from configs import TAMANO_CELDA
        px = gx * TAMANO_CELDA
        py = gy * TAMANO_CELDA
        for deco in self.world.decorativos:
            if int(deco.x) == px and int(deco.y) == py and deco.z == z:
                if sprite_id is None:
                    self.world.decorativos.remove(deco)
                else:
                    deco.sprite_id = sprite_id
                    deco.animation = ""

    def cambiar_nivel(self, nivel_id):
        self.gate_destino = None

        if nivel_id == "__return__":
            nivel_id = self.nivel_origen

        nivel_anterior = self.level_manager.obtener_id_actual()
        if nivel_anterior:
            self.world._saved_tile_overrides[nivel_anterior] = dict(self.world.tile_overrides)

        if nivel_id == "1-arena":
            self._nivel_antes_arena = nivel_anterior

        if not nivel_id or not self.level_manager.ir_a_nivel(nivel_id):
            print(f"Nivel {nivel_id} no encontrado")
            self.cambiando_nivel = False
            return False

        nivel = self.level_manager.obtener_nivel_actual()
        self.stack_manager.load_stacks(nivel_id)

        salida_id = self.gate_salida_id
        self.gate_salida_id = None
        inicio_x, inicio_y = WorldState.posicion_inicio_static(nivel)
        if salida_id:
            for (gx, gy, z), stack in self.stack_manager._stacks.items():
                for ev in stack.get("eventos", []):
                    if ev.get("id") == salida_id:
                        inicio_x = gx * TAMANO_CELDA
                        inicio_y = gy * TAMANO_CELDA
                        break

        total = self.snake.get_escamas() + LONGITUD_INICIAL

        self.snake.body = [[inicio_x, inicio_y]]
        for i in range(1, total):
            self.snake.body.append([inicio_x - i * TAMANO_CELDA, inicio_y])
        self.snake.iniciar_dormido((inicio_x, inicio_y))

        self.world.cargar_entidades_nivel(nivel)
        print(f"  CAMBIAR_NIVEL bloqueantes count={len(self.world.bloqueantes)}")
        for i, r in enumerate(self.world.bloqueantes):
            print(f"  CAMBIAR_NIVEL bloqueante[{i}] x={r.x} y={r.y} tipo={getattr(r,'tipo','?')}")
        self.world.limpiar_persistencia_nivel(nivel_id)
        self.camera = Camera(self.world.nivel_ancho, self.world.nivel_alto)
        self.world.inicializar_arena_boss(nivel, self.level_manager)

        self.world.crear_portal_boss(self.snake)

        if nivel['comidas']:
            self.world.comida = nivel['comidas'][0]
        else:
            self.world.spawn_comida(self.snake.body)

        self.snake_ctx.segmentos_perdidos = []
        self.mensaje_temporal = f"¡Nivel {nivel_id}!"
        self.tiempo_mensaje = 90
        self.cambiando_nivel = False
        self._jefe_derrotado = False

        print(f"Cambio a nivel {nivel_id}")
        return True

    def reiniciar(self):
        self.__init__()
        print("¡Juego reiniciado!")
