"""Acciones migradas a ActionRegistry (Sprint 3 + Fase 1 + Fase 2).

Importar este paquete registra las acciones en action_registry.
"""

from systems.actions.audio import *  # noqa: F401,F403
from systems.actions.flags import *  # noqa: F401,F403
from systems.actions.items import *  # noqa: F401,F403
from systems.actions.mensaje import *  # noqa: F401,F403
# Fase 1: acciones triviales migradas
from systems.actions.display import *  # noqa: F401,F403
from systems.actions.player import *  # noqa: F401,F403
from systems.actions.flags_extra import *  # noqa: F401,F403
from systems.actions.boss import *  # noqa: F401,F403
from systems.actions.game_flow import *  # noqa: F401,F403
from systems.actions.audio_settings import *  # noqa: F401,F403
from systems.actions.display_settings import *  # noqa: F401,F403
from systems.actions.ui import *  # noqa: F401,F403
from systems.actions.shop_extras import *  # noqa: F401,F403
from systems.actions.counters import *  # noqa: F401,F403
# Fase 2 Wave 1: acciones triviales con dependencias de manager
from systems.actions.remove_sprite import *  # noqa: F401,F403
from systems.actions.give_moneda import *  # noqa: F401,F403
from systems.actions.remove_moneda import *  # noqa: F401,F403
from systems.actions.abrir_menu import *  # noqa: F401,F403
from systems.actions.examinar_key_item import *  # noqa: F401,F403
from systems.actions.mostrar_ventana import *  # noqa: F401,F403
# Fase 2 Wave 3: acciones de diálogo
from systems.actions.dialog import *  # noqa: F401,F403
# Fase 2 Wave 4: acciones pesadas
from systems.actions.change_map import *  # noqa: F401,F403
from systems.actions.consume_pp import *  # noqa: F401,F403
from systems.actions.desbloquear_habilidad import *  # noqa: F401,F403
from systems.actions.equipar_habilidad import *  # noqa: F401,F403
from systems.actions.save_game import *  # noqa: F401,F403
from systems.actions.load_game import *  # noqa: F401,F403
from systems.actions.open_shop import *  # noqa: F401,F403
from systems.actions.run_script import *  # noqa: F401,F403
from systems.actions.ir_a_escena import *  # noqa: F401,F403
from systems.actions.iniciar_minijuego import *  # noqa: F401,F403
from systems.actions.mostrar_opciones import *  # noqa: F401,F403
from systems.actions.iniciar_demo import *  # noqa: F401,F403
from systems.actions.mover_a import *  # noqa: F401,F403
from systems.actions.spawn_entity import *  # noqa: F401,F403
from systems.actions.start_boss_fight import *  # noqa: F401,F403
from systems.actions.damage import *  # noqa: F401,F403
