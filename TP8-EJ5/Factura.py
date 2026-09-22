from LineaFactura import LineaFactura

class Factura:
    def __init__(self, tipo_comprobante: str, porcentaje_descuento: float, lineas: list[LineaFactura]):
        self._tipo_comprobante = tipo_comprobante  # "A" o "B"
        self._porcentaje_descuento = porcentaje_descuento  # Ej: 0.15
        self._lineas = lineas

    def calcular_total_neto(self) -> float:
        return sum(linea.calcular_neto_con_descuento(self._porcentaje_descuento) for linea in self._lineas)

    def calcular_total_iva(self) -> float:
        return sum(linea.calcular_iva_con_descuento(self._porcentaje_descuento) for linea in self._lineas)

    def calcular_total_final(self) -> float:
        return sum(linea.calcular_total_linea(self._porcentaje_descuento) for linea in self._lineas)

    def calcular_iva_por_tasa(self, tasa_buscada: float) -> float:
        return sum(
            linea.calcular_iva_con_descuento(self._porcentaje_descuento)
            for linea in self._lineas
            if abs(linea.porcentaje_iva_facturado - tasa_buscada) < 0.0001
        )

    @property
    def tipo_comprobante(self) -> str:
        return self._tipo_comprobante

    @property
    def porcentaje_descuento(self) -> float:
        return self._porcentaje_descuento

    @property
    def lineas(self) -> list[LineaFactura]:
        return self._lineas
