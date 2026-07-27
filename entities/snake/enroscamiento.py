# entities/snake/enroscamiento.py
from configs import *
from .movimiento import _DESPLAZAMIENTO


class EnroscamientoMixin:

    def enroscar(self, posicion=None, duracion=30, estado=None):
        if getattr(self, '_no_enroscar_hasta', 0) > 0:
            return

        self.enroscado = True
        self.etapa = 1
        self.segmentos_enroscados = 0
        self.direccion_original = self.direccion
        self.direccion_prohibida = self.direccion_original

        self._configurar_direcciones_permitidas()
        self._calcular_longitud_inicial()
        self.segmentos_visibles = self.body.copy()

    def _procesar_enroscamiento(self):
        if len(self.segmentos_visibles) > 1:
            self.segmentos_visibles.pop()
            self.segmentos_enroscados += 1
            self.body = self.segmentos_visibles.copy()
            self.longitud = len(self.body)

    def _iniciar_desenroscamiento(self):
        self.etapa = 2
        self.direccion_desenroscado = self.direccion

        longitud_perdida = self.largo_original - len(self.body)

        nueva_cabeza = self._calcular_proxima_cabeza()
        self.body.insert(0, nueva_cabeza)

        self.segmentos_a_restaurar = max(0, longitud_perdida - 1)
        self.creciendo = (self.segmentos_a_restaurar > 0)
        self.longitud = len(self.body)

        self._restablecer_estado_post_enroscado()

    def desenroscar(self):
        self.enroscado = False
        self.etapa = 0
        self.segmentos_guardados = []

    # ── Auxiliares ────────────────────────────────────────

    def _configurar_direcciones_permitidas(self):
        if self.direccion_original in ("ARRIBA", "ABAJO"):
            self.direcciones_permitidas = ["IZQUIERDA", "DERECHA"]
        else:
            self.direcciones_permitidas = ["ARRIBA", "ABAJO"]

    def _calcular_longitud_inicial(self):
        if self.segmentos_a_restaurar > 0:
            self.largo_original = len(self.body) + self.segmentos_a_restaurar
            self.segmentos_a_restaurar = 0
            self.creciendo = False
        else:
            self.largo_original = len(self.body)

    def _calcular_proxima_cabeza(self):
        cabeza = self.body[0].copy()
        dx, dy = _DESPLAZAMIENTO.get(self.direccion, (0, 0))
        cabeza[0] += dx
        cabeza[1] += dy
        return cabeza

    def _restablecer_estado_post_enroscado(self):
        self.etapa = 0
        self.enroscado = False
        self.segmentos_guardados = []
        self.segmentos_visibles = self.body.copy()
        self._no_enroscar_hasta = 2
