"""Acciones migradas a ActionRegistry (Sprint 3 + Fase 1).

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
