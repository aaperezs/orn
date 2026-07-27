import json
import os

RUTA_DATA = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


class RepositorioBase:
    """Base para todos los repositorios que cargan datos desde JSON"""

    def __init__(self, archivo):
        self._data = {}
        self._cargar(archivo)

    def _cargar(self, archivo):
        ruta = os.path.join(RUTA_DATA, archivo)
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        except FileNotFoundError:
            print(f"[REPO] Archivo no encontrado: {ruta}")
            self._data = {}
