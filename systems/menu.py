import json

from project_paths import data_dir


class MenuSystem:
    """Menú RPG data-driven: listado de apartados + estado de navegación.

    Configuración desde data/inventario.json:
      - apartados: lista de {"id", "nombre"} — apartados del menú (orden).
      - slots_equipo: lista de {"id", "nombre"} — slots de equipo del juego.
    """

    def __init__(self):
        self.activo = False
        self.apartados = []
        self.slots_equipo = []
        self.apartado_actual = 0
        self.seleccion = 0
        self._cargar()

    def _cargar(self):
        try:
            with open(data_dir("inventario.json"), encoding="utf-8") as f:
                cfg = json.load(f)
        except FileNotFoundError:
            cfg = {}
        self.apartados = cfg.get("apartados", [])
        self.slots_equipo = cfg.get("slots_equipo", [])
        if not self.apartados:
            self.apartados = [
                {"id": "habilidades", "nombre": "Habilidades"},
                {"id": "items", "nombre": "Items"},
                {"id": "equipo", "nombre": "Equipo"},
            ]
        if not self.slots_equipo:
            self.slots_equipo = [
                {"id": "cabeza", "nombre": "Cabeza"},
                {"id": "cuello", "nombre": "Cuello"},
                {"id": "cola", "nombre": "Cola"},
            ]

    def abrir(self):
        """Abre el menú: primer apartado abierto por defecto."""
        self.activo = True
        self.apartado_actual = 0
        self.seleccion = 0

    def cerrar(self):
        self.activo = False

    @property
    def apartado_id(self):
        if 0 <= self.apartado_actual < len(self.apartados):
            return self.apartados[self.apartado_actual]["id"]
        return None

    @property
    def apartado_nombre(self):
        if 0 <= self.apartado_actual < len(self.apartados):
            return self.apartados[self.apartado_actual]["nombre"]
        return ""

    def cambiar_apartado(self, direccion=1):
        """Cambia de apartado en el listado (ciclo)."""
        if not self.apartados:
            return
        self.apartado_actual = (self.apartado_actual + direccion) % len(self.apartados)
        self.seleccion = 0
