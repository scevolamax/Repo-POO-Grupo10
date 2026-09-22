from LineaFactura import LineaFactura
from Descuento import Descuento


class Factura:
    def __init__(self, tipo_comprobante: str, lineas: list[LineaFactura], descuentos: list[Descuento] = None):
        self._tipo_comprobante = tipo_comprobante  # "A" o "B"
        self._lineas = lineas
        # Descuentos globales de la factura (ej: Jubilados). Se aplican
        # DESPUÉS de los descuentos propios de cada línea (ver LineaFactura).
        self._descuentos = list(descuentos) if descuentos else []

    def calcular_total_neto(self) -> float:
        return sum(linea.calcular_neto_con_descuento(self._descuentos) for linea in self._lineas)

    def calcular_total_iva(self) -> float:
        return sum(linea.calcular_iva_con_descuento(self._descuentos) for linea in self._lineas)

    def calcular_total_final(self) -> float:
        return sum(linea.calcular_total_linea(self._descuentos) for linea in self._lineas)

    def calcular_iva_por_tasa(self, tasa_buscada: float) -> float:
        return sum(
            linea.calcular_iva_con_descuento(self._descuentos)
            for linea in self._lineas
            if abs(linea.porcentaje_iva_facturado - tasa_buscada) < 0.0001
        )

    @property
    def tipo_comprobante(self) -> str:
        return self._tipo_comprobante

    @property
    def descuentos(self) -> list[Descuento]:
        return self._descuentos

    @property
    def lineas(self) -> list[LineaFactura]:
        return self._lineas
