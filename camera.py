# camera.py
from configs import *


class Camera:
    def __init__(self, ancho_mundo, alto_mundo):
        self.ancho_mundo = ancho_mundo
        self.alto_mundo = alto_mundo
        self.x = 0
        self.y = 0
        self.target = None
        self.smooth = True

    def seguir(self, target):
        """Establece el objetivo de la cámara"""
        self.target = target

    def actualizar(self):
        """Actualiza la posición de la cámara"""
        if not self.target:
            return

        target_x = self.target[0] - ANCHO // 2
        target_y = self.target[1] - ALTO // 2

        # Limitar la cámara al mundo
        target_x = max(0, min(target_x, self.ancho_mundo - ANCHO))
        target_y = max(0, min(target_y, self.alto_mundo - ALTO))

        if self.smooth:
            # Movimiento suave
            self.x += (target_x - self.x) * 0.1
            self.y += (target_y - self.y) * 0.1
        else:
            self.x = target_x
            self.y = target_y

    def aplicar(self, posicion):
        """Aplica el offset de cámara a una posición"""
        x, y = posicion
        return (x - self.x, y - self.y)

    def get_offset(self):
        """Devuelve el offset de cámara (negativo: el mundo se mueve opuesto a la cámara)"""
        return (-int(self.x), -int(self.y))
