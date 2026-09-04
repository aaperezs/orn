# Backlog - Fases Posteriores a Homologación

> Estado: Fase 1 completada (homologación de `start_dialogue` + parámetro único `dialogo_id`)

---

## Fase 2: Callback Automático para Options

### Objetivo
Que al ejecutar una acción desde un `choice` de un `Options` (shop, diálogo externo, etc.), al terminar esa acción se restaure automáticamente el `Options` original, **excepto** si la acción es de "salida explícita" (`close_dialog`).

### Casos de Uso
| Choice Action | Comportamiento al terminar |
|---------------|---------------------------|
| `open_shop` | Vuelve al Options |
| `start_dialogue` (diálogo externo) | Vuelve al Options |
| `call_dialog` (sub-diálogo) | Vuelve al Options |
| `close_dialog` / "salir" | **NO vuelve**, cierra todo |

### Diseño Técnico Propuesto

#### 1. Detección de modo Options
```python
# En _ejecutar_accion (stack_manager.py)
en_modo_options = (self._bloqueo_por == "choice")
```

#### 2. Registro de callback al ejecutar acción bloqueante
```python
if en_modo_options and bloquea:
    self._registrar_restaurar_options(accion, params)
```

#### 3. Restauración automática
- Detectar transición `_bloqueo_por` de `"dialogo"/"shop"/"minijuego"` → `"choice"`
- En `_actualizar_bloqueos()` o similar, restaurar Options

#### 4. Opt-out explícito
```python
# Acciones que NO restauran
NO_RESTAURAR_OPTIONS = {"close_dialog"}

# O propiedad en la acción
class CloseDialog(GameAction):
    no_restore_options = True
```

### Preguntas Pendientes
1. ¿Dónde detectar la transición? En `_ejecutar_accion` vs `_actualizar_bloqueos()` llamado cada frame?
2. ¿Opt-out por nombre hardcodeado vs propiedad en clase acción?
3. ¿Manejo de anidación múltiple? (Stack simple vs solo primer nivel)
4. ¿El editor debe generar algo en JSON o es 100% automático?

---

## Fase 3: Homologación de Parámetros en JSON de Diálogos

### Objetivo
Actualizar `data/dialogos.json` para usar `dialogo_id` en lugar de `dialog` en las choices de options.

### Ejemplo Actual (data/dialogos.json)
```json
{
  "bienvenida": {
    "dialog": [...],
    "options": [{
      "choices": [
        { "action": "start_dialog", "dialog": "fenryr_store/historia" }
      ]
    }]
  }
}
```

### Objetivo
```json
{
  "bienvenida": {
    "dialog": [...],
    "options": [{
      "choices": [
        { "action": "start_dialogue", "dialogo_id": "fenryr_store/historia" }
      ]
    }]
  }
}
```

### Tareas
- [ ] Script de migración automática `dialog` → `dialogo_id` y `start_dialog` → `start_dialogue`
- [ ] Validar que todos los JSONs de diálogo funcionan
- [ ] Actualizar editor para generar `dialogo_id` + `start_dialogue`

---

## Fase 4: Sistema de Callbacks Explícitos (Stack de Contextos)

### Objetivo
Permitir anidación controlada: Options → Acción → Sub-diálogo → Acción → ... → Volver al Options base.

### Diseño
```python
# En DialogoSystem
_contexto_stack = []  # Stack de contextos guardados

def iniciar(self, ..., al_terminar=None):
    if self.activo:
        # Guardar contexto actual ANTES de iniciar nuevo
        self._contexto_stack.append(self._serializar_contexto())
    # ... iniciar nuevo ...

def _terminar_y_restaurar(self):
    if self._contexto_stack:
        # Restaurar contexto padre
        ctx = self._contexto_stack.pop()
        self._restaurar_contexto(ctx)
    else:
        # Comportamiento normal
        if self.al_terminar: self.al_terminar()
        self.activo = False
```

### Acciones relacionadas
- `call_dialog` - llama sub-diálogo y restaura al terminar (usa stack)
- `start_dialogue` - comportamiento actual (NO usa stack, limpia options)
- `return_to_options` - acción explícita para forzar retorno

---

## Fase 5: Editor - Soporte para Nuevos Patrones

### Tareas
- [ ] Paleta de enemigos con selector de patrón dinámico (desde `enemigos.json`)
- [ ] Modal de propiedades que lea parámetros editables desde `enemigos.json`
- [ ] Preview en grid con indicador visual de patrón
- [ ] Selector de capas Z en toolbar
- [ ] Registry dinámico con hot-reload (`enemy_registry.py` + watcher)

---

## Fase 6: Comportamientos Compuestos

### Objetivo
Permitir combinar múltiples comportamientos en un enemigo: movimiento + ataque + defensa.

### Estructura
```json
{
  "behavior": "enemigo_composite",
  "properties": {
    "behaviors": [
      {"type": "movement", "subtype": "zigzag", "params": {"amplitud": 3}},
      {"type": "attack", "subtype": "shoot_on_turn", "params": {"intervalo": 45}}
    ]
  }
}
```

### Tareas
- [ ] Factory `enemigo_composite` en motor
- [ ] UI compositor en editor (drag & drop, params por componente)
- [ ] Serialización a `elementos.json`

---

## Fase 7: Sistema de Plugins / Hot-Reload

### Objetivo
Editor detecta automáticamente nuevos tipos de enemigos añadidos al motor sin reiniciar.

### Componentes
- `EnemyTypeRegistry` - escanea `orm/data/elementos.json`, `enemigos.json`, `behaviors.json`
- File watcher en `orm/data/*.json` → evento `enemy_registry_changed`
- Paleta se reconstruye automáticamente

---

## Notas de Implementación

### Orden de Prioridad Sugerido
1. **Fase 2** - Callback automático (alto valor, desbloquea UX)
2. **Fase 3** - Migración JSON (limpieza técnica)
3. **Fase 4** - Stack callbacks (power feature)
4. **Fase 5** - Editor UX (polish)
5. **Fase 6** - Composite (extensibilidad)
6. **Fase 7** - Hot-reload (DX)

### Archivos Clave a Tocar
| Archivo | Fases Afectadas |
|---------|----------------|
| `orm/systems/stack_manager.py` | 2, 4 |
| `orm/systems/dialogo.py` | 2, 4 |
| `orm/systems/actions/dialog/*.py` | 2, 4 |
| `orm/data/dialogos.json` | 3 |
| `orm/scripts/validate_event_contract.py` | 1, 3 |
| `editor/widgets/enemy_palette.py` | 5 |
| `editor/widgets/enemy_property_modal.py` | 5 |
| `editor/enemy_registry.py` | 5, 7 |
| `editor/enemy_params.py` | 5 |

---

## Comandos Útiles

```bash
# Tests
cd orm && python -m pytest tests/ -x -v

# Drift Killer
cd orm && python scripts/validate_event_contract.py

# Migración JSON (cuando se implemente)
cd orm && python scripts/migrate_dialog_params.py
```