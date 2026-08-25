from dataclasses import dataclass, field
from typing import Any


@dataclass
class ShopItem:
    """Ítem de una tienda con estado runtime (stock, desbloqueado)."""

    item_id: str
    precio: dict[str, int] = field(default_factory=dict)  # {"oro": 500, "escamas": 50}
    moneda_compra: str = "oro"
    stock: int = 0
    max_stock: int = 0
    stock_infinito: bool = False
    max_stack: int = 1
    unlock: dict | None = None  # condicion unlock o None
    restock: dict | None = None  # triggers + cantidad
    visible_si_bloqueado: bool = False

    # Estado runtime
    desbloqueado: bool = False

    def puede_comprar(self, cantidad: int = 1) -> bool:
        if self.stock_infinito:
            return True
        return self.stock >= cantidad

    def comprar(self, cantidad: int = 1) -> bool:
        if not self.puede_comprar(cantidad):
            return False
        if not self.stock_infinito:
            self.stock -= cantidad
        return True

    def restockear(self, cantidad: int | None = None):
        if self.stock_infinito:
            return
        if cantidad is None:
            cantidad = self.max_stock - self.stock
        self.stock = min(self.max_stock, self.stock + max(0, cantidad))

    def evaluar_unlock(self, estado) -> bool:
        if self.unlock is None:
            self.desbloqueado = True
            return True
        self.desbloqueado = evaluar_unlock(self.unlock, estado)
        return self.desbloqueado


@dataclass
class Shop:
    """Tienda con items y configuración."""

    id: str
    nombre: str
    descripcion: str = ""
    moneda_principal: str = "oro"
    categorias: list[str] = field(default_factory=list)
    items: dict[str, ShopItem] = field(default_factory=dict)
    compra: dict = field(default_factory=dict)  # {items_aceptados, precios_compra}

    def get_item(self, item_id: str) -> ShopItem | None:
        return self.items.get(item_id)

    def get_items_disponibles(self, estado) -> list[ShopItem]:
        """Items desbloqueados y visibles según unlock"""
        disponibles = []
        for item in self.items.values():
            if item.evaluar_unlock(estado):
                disponibles.append(item)
            elif item.visible_si_bloqueado:
                disponibles.append(item)
        return disponibles

    def get_precio_compra(self, item_id: str) -> dict[str, int]:
        """Precio de venta al shop (trueque). None si no compra ese item."""
        if not self.compra:
            return None
        precios_compra = self.compra.get("precios_compra", {})
        if item_id in precios_compra:
            return precios_compra[item_id]
        items_aceptados = self.compra.get("items_aceptados", [])
        if items_aceptados == ["*"] or item_id in items_aceptados:
            return None  # Sin precio definido -> no compra
        return None


def evaluar_unlock(condicion: dict | None, estado) -> bool:
    """Evalúa condición de unlock recursivamente.

    Soporta:
    - AND: {"tipo": "AND", "condiciones": [...]}
    - OR:  {"tipo": "OR", "condiciones": [...]}
    - flag: {"tipo": "flag", "flag": "id", "operador": "==", "valor": 1}
    - contador: {"tipo": "contador", "contador": "id", "operador": ">=", "valor": 1}
    - item: {"tipo": "item", "item_id": "id", "cantidad": 1}
    """
    if condicion is None:
        return True

    tipo = condicion.get("tipo", "")

    if tipo == "AND":
        return all(evaluar_unlock(c, estado) for c in condicion.get("condiciones", []))
    if tipo == "OR":
        return any(evaluar_unlock(c, estado) for c in condicion.get("condiciones", []))

    if tipo == "flag":
        flag_id = condicion.get("flag", "")
        operador = condicion.get("operador", "==")
        valor = condicion.get("valor", 1)
        actual = estado.flags.get(flag_id, 0)
        if isinstance(valor, str):
            try:
                valor = int(valor)
            except ValueError:
                try:
                    valor = float(valor)
                except ValueError:
                    pass
        return _comparar(actual, operador, valor)

    if tipo == "contador":
        contador_id = condicion.get("contador", "")
        operador = condicion.get("operador", ">=")
        valor = condicion.get("valor", 1)
        if hasattr(estado, "contadores"):
            actual = estado.contadores.get(contador_id, 0)
        else:
            actual = 0
        if isinstance(valor, str):
            try:
                valor = int(valor)
            except ValueError:
                try:
                    valor = float(valor)
                except ValueError:
                    pass
        return _comparar(actual, operador, valor)

    if tipo == "item":
        item_id = condicion.get("item_id", "")
        cantidad = condicion.get("cantidad", 1)
        return estado.inventario.tiene_item(item_id, cantidad)

    return False


def _comparar(a, operador, b):
    if operador == "==":
        return a == b
    if operador == "!=":
        return a != b
    if operador == ">":
        return a > b
    if operador == ">=":
        return a >= b
    if operador == "<":
        return a < b
    if operador == "<=":
        return a <= b
    return False