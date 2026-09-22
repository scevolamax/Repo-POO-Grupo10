from Producto import Producto

class LineaFactura:
    def __init__(self, cantidad: int, producto: Producto):
        self._cantidad = cantidad
        self._producto = producto
        # Capturamos el estado histórico en el momento de la compra
        self._precio_unitario_facturado = producto.precio_base
        self._porcentaje_iva_facturado = producto.porcentaje_iva

    def calcular_neto_con_descuento(self, porcentaje_descuento_global: float) -> float:
        subtotal_base = self._cantidad * self._precio_unitario_facturado
        return subtotal_base * (1.0 - porcentaje_descuento_global)

    def calcular_iva_con_descuento(self, porcentaje_descuento_global: float) -> float:
        return self.calcular_neto_con_descuento(porcentaje_descuento_global) * self._porcentaje_iva_facturado

    def calcular_total_linea(self, porcentaje_descuento_global: float) -> float:
        return (self.calcular_neto_con_descuento(porcentaje_descuento_global) + 
                self.calcular_iva_con_descuento(porcentaje_descuento_global))

    @property
    def producto(self) -> Producto:
        return self._producto

    @property
    def cantidad(self) -> int:
        return self._cantidad

    @property
    def precio_unitario_facturado(self) -> float:
        return self._precio_unitario_facturado

    @property
    def porcentaje_iva_facturado(self) -> float:
        return self._porcentaje_iva_facturado