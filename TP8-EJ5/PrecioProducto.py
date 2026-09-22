from datetime import date


class PrecioProducto: # para representa el precio de un producto vigente en un rango de fechas.


    def __init__(
        self,
        precio: float,
        fecha_desde: date,
        fecha_hasta: date | None = None,
    ) -> None:

        #precio       : Precio del producto (sin IVA) durante el período.
        #fecha_desde  : Primer día en que este precio es válido (inclusive).
        #fecha_hasta  : Último día en que este precio es válido (inclusive).
        #None indica que el precio sigue vigente desde la fecha_desde.

        if precio < 0:
            raise ValueError("El precio no puede ser negativo.")
        if fecha_hasta is not None and fecha_hasta < fecha_desde:
            raise ValueError(f"fecha_hasta ({fecha_hasta}) no puede ser anterior a fecha_desde ({fecha_desde}).")

        self._precio = precio
        self._fecha_desde = fecha_desde
        self._fecha_hasta = fecha_hasta

    def es_vigente(self, fecha: date) -> bool:
        #Retorna True si este precio está vigente en la fecha indicada.

        #Un precio es vigente cuando:
          #fecha_desde <= fecha <= fecha_hasta   (si fecha_hasta no es None)
          #fecha_desde <= fecha                  (si fecha_hasta es None → precio abierto)

        if fecha < self._fecha_desde:
            return False
        if self._fecha_hasta is not None and fecha > self._fecha_hasta:
            return False
        return True

    def cerrar_vigencia(self, fecha_fin: date) -> None:
        if fecha_fin < self._fecha_desde:
            raise ValueError("La fecha de cierre no puede ser anterior a la fecha de inicio.")
        self._fecha_hasta = fecha_fin


    @property
    def precio(self) -> float:
        return self._precio

    @property
    def fecha_desde(self) -> date:
        return self._fecha_desde

    @property
    def fecha_hasta(self) -> date | None:
        return self._fecha_hasta


#esta es solo una representacion 
    def __repr__(self) -> str:
        hasta_str = str(self._fecha_hasta) if self._fecha_hasta else "abierto"
        return ( f"PrecioProducto(precio=${self._precio:.2f} desde={self._fecha_desde}, hasta={hasta_str})")
