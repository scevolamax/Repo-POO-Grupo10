from datetime import date


class PrecioProducto:
    """
    Representa el precio de un producto vigente en un rango de fechas.

    Principios aplicados
    --------------------
    - GRASP / Information Expert: esta clase concentra toda la lógica
      de validación temporal (¿el precio estaba vigente en la fecha X?).
      Nadie más necesita saber cómo funciona esa lógica interna.
    - Ley de Demeter: expone sólo sus propios datos a través de
      propiedades; nunca delega hacia objetos de terceros.
    """

    def __init__(
        self,
        precio: float,
        fecha_desde: date,
        fecha_hasta: date | None = None,
    ) -> None:
        """
        Parámetros
        ----------
        precio      : Precio del producto (sin IVA) durante el período.
        fecha_desde : Primer día en que este precio es válido (inclusive).
        fecha_hasta : Último día en que este precio es válido (inclusive).
                      None indica que el precio sigue vigente indefinidamente
                      desde fecha_desde (período "abierto").
        """
        if precio < 0:
            raise ValueError("El precio no puede ser negativo.")
        if fecha_hasta is not None and fecha_hasta < fecha_desde:
            raise ValueError(
                f"fecha_hasta ({fecha_hasta}) no puede ser anterior "
                f"a fecha_desde ({fecha_desde})."
            )

        self._precio = precio
        self._fecha_desde = fecha_desde
        self._fecha_hasta = fecha_hasta

    # ------------------------------------------------------------------
    # Information Expert: esta clase sabe si el precio es vigente
    # ------------------------------------------------------------------
    def es_vigente(self, fecha: date) -> bool:
        """
        Retorna True si este precio está vigente en la fecha indicada.

        Un precio es vigente cuando:
          fecha_desde <= fecha <= fecha_hasta   (si fecha_hasta no es None)
          fecha_desde <= fecha                  (si fecha_hasta es None -> período abierto)
        """
        if fecha < self._fecha_desde:
            return False
        if self._fecha_hasta is not None and fecha > self._fecha_hasta:
            return False
        return True

    def cerrar_vigencia(self, fecha_fin: date) -> None:
        """
        Establece el último día en que el precio es válido.
        Útil cuando se registra un nuevo precio y hay que cerrar el anterior.
        """
        if fecha_fin < self._fecha_desde:
            raise ValueError(
                "La fecha de cierre no puede ser anterior a la fecha de inicio."
            )
        self._fecha_hasta = fecha_fin

    # ------------------------------------------------------------------
    # Properties (Ley de Demeter: acceso solo a los propios atributos)
    # ------------------------------------------------------------------
    @property
    def precio(self) -> float:
        return self._precio

    @property
    def fecha_desde(self) -> date:
        return self._fecha_desde

    @property
    def fecha_hasta(self) -> date | None:
        return self._fecha_hasta

    def __repr__(self) -> str:
        hasta_str = str(self._fecha_hasta) if self._fecha_hasta else "abierto"
        return (
            f"PrecioProducto(precio=${self._precio:.2f}, "
            f"desde={self._fecha_desde}, hasta={hasta_str})"
        )
