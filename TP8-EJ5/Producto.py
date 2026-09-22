from datetime import date
from typing import Optional


class Producto:
    """
    Representa un artículo del catálogo del supermercado.

    Principios GRASP aplicados:
    - Creator: Producto contiene y compone su propio historial de precios.
      Por eso es responsable de crear instancias de PrecioProducto mediante
      agregar_precio().
    - Information Expert: Producto conoce su colección de precios históricos.
      Para saber el precio en una fecha dada, delega en cada PrecioProducto
      (es_vigente) y devuelve el precio vigente.
    - High Cohesion: delega la lógica temporal a PrecioProducto, manteniendo
      a Producto enfocado en definir el artículo y su carga tributaria.
    """

    def __init__(self, nombre: str, precio_base: float, porcentaje_iva: float):
        self._nombre = nombre
        self._precio_base = precio_base
        self._porcentaje_iva = porcentaje_iva  # Expresado en decimal (ej: 0.21)
        self._historial_precios: list = []  # list[PrecioProducto]

    # ------------------------------------------------------------------
    # Creator: Producto construye y registra sus propios PrecioProducto
    # ------------------------------------------------------------------
    def agregar_precio(
        self,
        precio: float,
        fecha_desde: date,
        fecha_hasta: Optional[date] = None,
    ) -> None:
        """
        Registra un nuevo precio histórico para este producto.

        Parámetros
        ----------
        precio      : Valor del precio (sin IVA) durante el período.
        fecha_desde : Primer día en que el precio es válido (inclusive).
        fecha_hasta : Último día en que el precio es válido (inclusive).
                      None indica precio vigente indefinidamente (precio "abierto").
        """
        from PrecioProducto import PrecioProducto
        nuevo = PrecioProducto(precio, fecha_desde, fecha_hasta)
        self._historial_precios.append(nuevo)

    # ------------------------------------------------------------------
    # Information Expert: sabe cuál precio estuvo vigente en una fecha
    # ------------------------------------------------------------------
    def obtener_precio_en(self, fecha: date) -> float:
        """
        Retorna el precio vigente del producto en la fecha indicada.

        Si no hay historial, retorna precio_base como valor de respaldo.

        Raises
        ------
        ValueError: si hay historial pero ningún precio cubre la fecha dada.
        """
        if not self._historial_precios:
            return self._precio_base

        # Recorremos en orden inverso: el último registrado tiene precedencia
        for pp in reversed(self._historial_precios):
            if pp.es_vigente(fecha):
                return pp.precio

        raise ValueError(
            f"No hay precio registrado para '{self._nombre}' "
            f"en la fecha {fecha}."
        )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------
    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def porcentaje_iva(self) -> float:
        return self._porcentaje_iva

    @property
    def historial_precios(self) -> list:
        """Retorna una copia de la lista de precios históricos."""
        return list(self._historial_precios)

    @property
    def precio_base(self) -> float:
        """
        Precio usado al momento de la compra (LineaFactura lo captura).
        Si hay historial, refleja el precio vigente a la fecha de hoy.
        Si no hay historial, retorna el valor original del constructor.
        """
        if self._historial_precios:
            try:
                return self.obtener_precio_en(date.today())
            except ValueError:
                pass
        return self._precio_base

    def __repr__(self) -> str:
        return (
            f"Producto('{self._nombre}', "
            f"Precio Actual=${self.precio_base:.2f}, "
            f"IVA={self._porcentaje_iva * 100:.1f}%)"
        )