# TODO: Menú e Inventario RPG (Orm)

## Filosofía
- Runtime genérico, data-driven por juego (archivos en data/ del proyecto).
- Estilo RPG clásico (referencia: RPG Maker / Mega Man X4): listado de apartados
  lateral, primero abierto por defecto, ↑↓ selección, Enter aceptar, ESC cancelar.
- Sin rarezas en items: la visibilidad se logra con tipo/efectos, no con color de rareza.

## Controles (pendiente de archivo de mapeo .MD aparte)
- Base de referencia estilo PSX: □ Menú, ○ Aceptar, ✕ Cancelar, △ Opciones,
  D-Pad mover, R1/L1 cambiar habilidad, START Pausa.
- En teclado por ahora: I Menú, Enter Aceptar, ESC Cancelar, TAB cambiar
  habilidad/pestaña, ↑↓ navegar, Q habilidad activa, E sub-habilidad.
- TODAS las teclas deben salir de un mapeo configurable (ACTION → tecla).
  → PENDIENTE: crear docs/mapeo-controles.md y data/controles.json.

## Fases
### Fase 1 — Esqueleto multi-apartado
- [x] data/inventario.json: apartados + slots_equipo (cabeza/cuello/cola).
- [x] systems/menu.py: MenuSystem (activo, apartado_actual, seleccion).
- [x] Refactor InventoryMenu → paneles por apartado registrados por id.
- [x] input_manager._handle_inventory: navegación completa.
- [x] Apartado Habilidades = render actual, sin cambios de mecánica.

### Fase 2 — Apartado Items
- [ ] Lista con icono (obtener_sprite), cantidad, descripción.
- [ ] Acciones: usar consumible, soltar. Agrupar por tipo.

### Fase 3 — Apartado Equipo
- [ ] SLOTS dinámicos desde data/inventario.json (generalizar inventario.py:3).
- [ ] Panel: slots + botiquín; Enter equipa/desequipa; aplicar_todos_efectos.
- [ ] objetos.json/items.json: agregar sprite_id + tipo (avisar antes, son datos).

### Fase 4 — Habilidades del equipo
- [ ] Objetos equipables declaran sub_habilidad_id y/o pasivas.
- [ ] SistemaHabilidades: sub_habilidad_equipada + pasivas_activas.
- [ ] Segunda tecla sub-habilidad (E); HUD muestra activa + sub.
- [ ] habilidades.json: campo "origen" (jefe/collar/casco/cola).

### Fase 5 — Persistencia de partida
- [ ] systems/save_manager.py (patrón user_prefs): items, equipo, habilidades,
      nivel, escamas, flags. Guardar en cambio de nivel/salir; cargar al inicio.

## Notas
- No tocar data/ del usuario sin avisar (ver AGENTS.md).
- Mapeo de botones configurable queda como dependencia transversal.
