from repositories.repositorio_tiendas import RepositorioTiendas
from repositories.repositorio_objetos import RepositorioObjetos
from repositories.repositorio_monedas import RepositorioMonedas
from entities.shop import Shop, ShopItem, evaluar_unlock


class ShopSystem:
    """Sistema central de tiendas: carga, unlock, stock, compra/venta, restock."""

    def __init__(self):
        self._repo_tiendas = RepositorioTiendas()
        self._repo_objetos = RepositorioObjetos()
        self._repo_monedas = RepositorioMonedas()
        self._shops: dict[str, Shop] = {}
        self._cargar_tiendas()

    def _cargar_tiendas(self):
        self._shops = {}
        for shop_data in self._repo_tiendas.get_shops():
            shop = self._crear_shop_desde_data(shop_data)
            self._shops[shop.id] = shop

    def _crear_shop_desde_data(self, data: dict) -> Shop:
        items = {}
        for item_data in data.get("items", []):
            item_id = item_data.get("item_id", "")
            if not item_id:
                continue
            shop_item = ShopItem(
                item_id=item_id,
                precio=item_data.get("precio", {}),
                moneda_compra=item_data.get("moneda_compra", "oro"),
                stock=item_data.get("stock", 0),
                max_stock=item_data.get("max_stock", 0),
                stock_infinito=item_data.get("stock_infinito", False),
                max_stack=item_data.get("max_stack", 1),
                unlock=item_data.get("unlock"),
                restock=item_data.get("restock"),
                visible_si_bloqueado=item_data.get("visible_si_bloqueado", False),
            )
            items[item_id] = shop_item

        shop = Shop(
            id=data.get("id", ""),
            nombre=data.get("nombre", ""),
            descripcion=data.get("descripcion", ""),
            moneda_principal=data.get("moneda_principal", "oro"),
            categorias=data.get("categorias", []),
            items=items,
            compra=data.get("compra", {}),
        )
        return shop

    def get_shop(self, shop_id: str) -> Shop | None:
        return self._shops.get(shop_id)

    def get_todas_las_tiendas(self) -> list[Shop]:
        return list(self._shops.values())

    def refrescar_unlocks(self, estado):
        """Reevalúa unlocks de todos los items de todas las tiendas."""
        for shop in self._shops.values():
            for item in shop.items.values():
                item.evaluar_unlock(estado)

    def puede_comprar(self, estado, shop_id: str, item_id: str, cantidad: int = 1) -> tuple[bool, str]:
        shop = self.get_shop(shop_id)
        if not shop:
            return False, "Tienda no encontrada"
        item = shop.get_item(item_id)
        if not item:
            return False, "Ítem no existe en la tienda"
        if not item.desbloqueado and not item.visible_si_bloqueado:
            return False, "Ítem no disponible"
        if not item.puede_comprar(cantidad):
            return False, "Sin stock"
        # Verificar moneda
        precio = item.precio
        moneda = item.moneda_compra
        costo = precio.get(moneda, 0) * cantidad
        if estado.monedas.get(moneda, 0) < costo:
            return False, f"Faltan {moneda}"
        # Verificar max_stack en inventario
        actual = estado.inventario.cantidad(item_id)
        if actual + cantidad > item.max_stack:
            return False, f"Límite de pila ({item.max_stack})"
        return True, ""

    def comprar(self, estado, shop_id: str, item_id: str, cantidad: int = 1) -> tuple[bool, str]:
        ok, msg = self.puede_comprar(estado, shop_id, item_id, cantidad)
        if not ok:
            return False, msg

        shop = self.get_shop(shop_id)
        item = shop.get_item(item_id)
        precio = item.precio
        moneda = item.moneda_compra
        costo = precio.get(moneda, 0) * cantidad

        estado.monedas.quitar(moneda, costo)
        estado.inventario.agregar_item(item_id, cantidad)
        item.comprar(cantidad)

        return True, f"Comprado {item_id} x{cantidad} por {costo} {moneda}"

    def puede_vender(self, estado, shop_id: str, item_id: str, cantidad: int = 1) -> tuple[bool, str, dict | None]:
        shop = self.get_shop(shop_id)
        if not shop:
            return False, "Tienda no encontrada", None
        if not estado.inventario.tiene_item(item_id, cantidad):
            return False, "No tienes ese ítem", None
        precio_compra = shop.get_precio_compra(item_id)
        if not precio_compra:
            return False, "Esta tienda no compra ese ítem", None
        return True, "", precio_compra

    def vender(self, estado, shop_id: str, item_id: str, cantidad: int = 1) -> tuple[bool, str]:
        ok, msg, precio_compra = self.puede_vender(estado, shop_id, item_id, cantidad)
        if not ok:
            return False, msg

        estado.inventario.remover_item(item_id, cantidad)
        for moneda, valor in precio_compra.items():
            total = valor * cantidad
            estado.monedas.dar(moneda, total)

        return True, f"Vendido {item_id} x{cantidad} por {total} {moneda}"

    def restockear(self, estado, shop_id: str, item_id: str | None = None):
        shop = self.get_shop(shop_id)
        if not shop:
            return
        if item_id:
            item = shop.get_item(item_id)
            if item and item.restock:
                item.restockear(item.restock.get("cantidad"))
        else:
            for item in shop.items.values():
                if item.restock:
                    item.restockear(item.restock.get("cantidad"))

    def procesar_triggers_restock(self, estado, trigger_evento: str):
        """Llamado cuando ocurre un evento que puede disparar restock (ej. derrota_jefe_2)."""
        for shop in self._shops.values():
            for item in shop.items.values():
                if not item.restock:
                    continue
                triggers = item.restock.get("triggers", [])
                for trigger in triggers:
                    if trigger.get("tipo") == "evento" and trigger.get("evento") == trigger_evento:
                        item.restockear(item.restock.get("cantidad"))

    def anadir_stock(self, shop_id: str, item_id: str, cantidad: int):
        shop = self.get_shop(shop_id)
        if not shop:
            return
        item = shop.get_item(item_id)
        if item:
            if item.stock_infinito:
                return
            item.stock = min(item.max_stock, item.stock + cantidad)

    def modificar_precio(self, shop_id: str, item_id: str, moneda: str, nuevo_precio: int):
        shop = self.get_shop(shop_id)
        if not shop:
            return
        item = shop.get_item(item_id)
        if item:
            item.precio[moneda] = nuevo_precio

    def get_estado_save(self) -> dict:
        """Estado para guardar en savegame."""
        estado = {}
        for shop_id, shop in self._shops.items():
            estado[shop_id] = {}
            for item_id, item in shop.items.items():
                estado[shop_id][item_id] = {
                    "stock": item.stock,
                    "desbloqueado": item.desbloqueado,
                }
        return estado

    def cargar_estado_save(self, estado_save: dict):
        """Carga estado desde savegame."""
        for shop_id, items_estado in estado_save.items():
            shop = self._shops.get(shop_id)
            if not shop:
                continue
            for item_id, item_estado in items_estado.items():
                item = shop.items.get(item_id)
                if item:
                    item.stock = item_estado.get("stock", item.stock)
                    item.desbloqueado = item_estado.get("desbloqueado", item.desbloqueado)

    def get_config_item(self, item_id: str) -> dict | None:
        """Obtiene config base del item desde repositorio objetos."""
        return self._repo_objetos.get_objeto(item_id)