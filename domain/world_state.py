import os

from configs import TAMANO_CELDA
from configs.z_layers import Z_ARENA_JEFE
from entities.boss import Boss
from entities.boss_arena import BossArena
from entities.food import Food
from entities.portal_boss import PortalBoss
from levels.level_manager import RUTA_MAPAS
from levels.level_parser import LevelParser
from utils.helpers import generar_comida_normal


class WorldState:
    def __init__(self):
        self.paredes = []
        self.bloqueantes = []
        self.hierba_alta = []
        self.bloques_acero = []
        self.enemigos = []
        self.decorativos = []
        self.suelos = []
        self.arena_paredes = []
        self.zonas_restringidas = []
        self.terrenos_negados = set()

        self.nivel_ancho = 0
        self.nivel_alto = 0
        self.nivel_z0 = {}
        self.grid = {}
        self.grid_por_capa = {}
        self.zona_boss = None
        self.arena_boss = None
        self.boss = None
        self.portal_boss = None
        self.comida = None

        self.tile_overrides = {}
        self._saved_tile_overrides = {}

    def cargar_entidades_nivel(self, nivel):
        self.paredes = nivel['paredes']
        self.bloqueantes = nivel['bloqueantes']
        self.hierba_alta = nivel.get('hierba_alta', [])
        self.bloques_acero = nivel.get('bloques_acero', [])
        self.zona_boss = nivel.get('zona_boss', None)
        self.arena_paredes = []
        self.enemigos = nivel['enemigos']
        self.zonas_restringidas = nivel.get('zonas_restringidas', [])
        self.suelos = nivel.get('suelos', [])
        self.decorativos = nivel.get('decorativos', [])
        self.nivel_ancho = nivel['ancho']
        self.nivel_alto = nivel['alto']
        self.nivel_z0 = nivel
        self.grid = nivel.get('grid', {})
        self.grid_por_capa = nivel.get('grid_por_capa', {0: self.grid})

    def inicializar_arena_boss(self, nivel, level_manager):
        zona = nivel.get('zona_boss', None)
        if zona:
            _, _, arena_file = zona
            if arena_file:
                ruta = os.path.join(RUTA_MAPAS, arena_file)
                if not ruta.endswith('.txt'):
                    ruta += '.txt'
            else:
                nivel_id = level_manager.obtener_id_actual()
                ruta = os.path.join(RUTA_MAPAS, f"{nivel_id}-arena.txt")
            try:
                with open(ruta, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                    datos = LevelParser.parsear_mapa(contenido)
                    tipo_boss = 'tronco'
                    for linea in contenido.split('\n'):
                        if linea.startswith('# boss='):
                            tipo_boss = linea.split('=', 1)[1].strip()
                            break
            except FileNotFoundError:
                print(f"Arena {ruta} no encontrada, no hay boss en este nivel")
                datos = None
                tipo_boss = 'tronco'
            if datos and datos.get('zona_boss'):
                boss_pos = datos['zona_boss']
                boss_x, boss_y, _ = boss_pos
                entidades = []
                for r in datos['bloqueantes']:
                    entidades.append(r)
                for b in datos['bloques_acero']:
                    entidades.append(b)
                for h in datos.get('hierba_alta', []):
                    entidades.append(h)
                for e in datos['enemigos']:
                    entidades.append(e)
                self.arena_boss = BossArena(0, 0, datos['ancho'], datos['alto'],
                                           z=Z_ARENA_JEFE, paredes=datos['paredes'],
                                           entidades=entidades)
                self.boss = Boss(boss_x, boss_y, tipo_boss, z=Z_ARENA_JEFE)
                self.arena_boss.boss = self.boss
                print(f"   Arena cargada desde: {ruta}")
            else:
                self.arena_boss = BossArena(50, 50, 200, 150, z=Z_ARENA_JEFE)
                self.boss = None
                self.arena_boss.boss = None
        elif nivel.get('jefes'):
            jefes = nivel['jefes']
            self.arena_boss = BossArena(0, 0, nivel['ancho'], nivel['alto'],
                                        z=Z_ARENA_JEFE, es_nivel_completo=True)
            self.arena_boss.boss = jefes[0]
            self.boss = jefes[0]
        else:
            self.arena_boss = BossArena(50, 50, 200, 150, z=Z_ARENA_JEFE)
            self.boss = None
            self.arena_boss.boss = None

    @staticmethod
    def posicion_inicio_static(nivel):
        if nivel['inicio']:
            ix, iy = nivel['inicio']
        else:
            ix = nivel['ancho'] // 2
            iy = nivel['alto'] // 2
        ix = (ix // TAMANO_CELDA) * TAMANO_CELDA
        iy = (iy // TAMANO_CELDA) * TAMANO_CELDA
        return ix, iy

    def replace_tile_sprite(self, gx, gy, sprite_id, z=0):
        if sprite_id is None or sprite_id == "":
            self.tile_overrides[(gx, gy, z)] = None
        else:
            self.tile_overrides[(gx, gy, z)] = sprite_id

    def remove_tile_sprite(self, gx, gy, z=0):
        self.tile_overrides[(gx, gy, z)] = None

    def spawn_comida(self, snake_body, suelos=None):
        x, y = generar_comida_normal(
            snake_body,
            list(self.bloqueantes) + list(self.bloques_acero) + list(self.paredes),
            self.zonas_restringidas, self.nivel_ancho, self.nivel_alto,
            suelos or self.suelos
        )
        self.comida = Food.generar_en_posicion(x, y)

    def crear_portal_boss(self, snake):
        if self.zona_boss:
            bx, by, _ = self.zona_boss
            portal_x, portal_y = bx, by
        else:
            portal_x, portal_y = 0, 0
        posicion_salida = (
            (portal_x // TAMANO_CELDA) * TAMANO_CELDA,
            (portal_y // TAMANO_CELDA) * TAMANO_CELDA
        )
        self.portal_boss = PortalBoss(portal_x, portal_y, self.arena_boss, posicion_salida)
        if not self.zona_boss:
            self.portal_boss.activo_entrada = False

    def limpiar_persistencia_nivel(self, nivel_id):
        self.tile_overrides = self._saved_tile_overrides.pop(nivel_id, {})
