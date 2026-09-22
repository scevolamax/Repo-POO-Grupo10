from Producto import Producto
from Descuento import Descuento


class LineaFactura:
    def __init__(self, cantidad: int, producto: Producto, descuentos: list[Descuento] = None):
        self._cantidad = cantidad
        self._producto = producto
        # Capturamos el estado histórico en el momento de la compra
        self._precio_unitario_facturado = producto.precio_base
        self._porcentaje_iva_facturado = producto.porcentaje_iva
        # Descuentos propios de esta línea/producto (ej: 3x2, por volumen).
        # Es una lista porque pueden encadenarse varias promociones.
        self._descuentos = list(descuentos) if descuentos else []

    def _calcular_neto(self, descuentos_adicionales: list[Descuento] = None) -> float:
        monto = self._cantidad * self._precio_unitario_facturado
        # Se aplican primero los descuentos propios de la línea (ej. 3x2)
        # y luego, en cadena, los descuentos globales que llegan desde la
        # Factura (ej. Jubilados). El orden queda definido simplemente por
        # el orden de la lista: no hay ningún if/else de por medio.
        cadena_de_descuentos = self._descuentos + (descuentos_adicionales or [])
        for descuento in cadena_de_descuentos:
            monto = descuento.aplicar(self._cantidad, monto)
        return monto

    def calcular_neto_con_descuento(self, descuentos_adicionales: list[Descuento] = None) -> float:
        return self._calcular_neto(descuentos_adicionales)

    def calcular_iva_con_descuento(self, descuentos_adicionales: list[Descuento] = None) -> float:
        return self._calcular_neto(descuentos_adicionales) * self._porcentaje_iva_facturado

    def calcular_total_linea(self, descuentos_adicionales: list[Descuento] = None) -> float:
        neto = self._calcular_neto(descuentos_adicionales)
        return neto + (neto * self._porcentaje_iva_facturado)

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

    @property
    def descuentos(self) -> list[Descuento]:
        return self._descuentos
