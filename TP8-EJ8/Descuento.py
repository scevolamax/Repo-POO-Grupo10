from abc import ABC, abstractmethod


class Descuento(ABC):
    """
    Estrategia de descuento (Strategy Pattern).

    Cada descuento sabe cómo transformar un monto de acuerdo a su propia
    lógica (que puede depender de la cantidad de unidades, o no). De esta
    forma, Factura y LineaFactura no necesitan conocer las reglas de
    negocio de cada promoción: solo saben que reciben una lista de
    "cosas que se aplican en cadena" (Principio Abierto/Cerrado).
    """

    @abstractmethod
    def aplicar(self, cantidad: int, monto_base: float) -> float:
        """
        Recibe la cantidad de unidades de la línea y el monto acumulado
        hasta el momento (que puede ya venir con otros descuentos
        aplicados), y devuelve el nuevo monto resultante.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def descripcion(self) -> str:
        """Texto legible para mostrar en el comprobante."""
        raise NotImplementedError


class DescuentoPromocionNxM(Descuento):
    """
    Promociones tipo '3x2', '2x1', etc: por cada N unidades llevadas,
    el cliente paga M. Esto NO es un porcentaje fijo: requiere evaluar
    la cantidad comprada (lógica condicional), por eso no puede vivir
    en un simple atributo double.

    Ejemplos con N=3, M=2:
      cantidad=3 -> paga 2   | cantidad=4 -> paga 3   | cantidad=5 -> paga 4
    """

    def __init__(self, unidades_requeridas: int, unidades_pagadas: int):
        if unidades_requeridas <= 0 or unidades_pagadas <= 0 or unidades_pagadas > unidades_requeridas:
            raise ValueError("Parámetros de promoción NxM inválidos")
        self._n = unidades_requeridas
        self._m = unidades_pagadas

    def aplicar(self, cantidad: int, monto_base: float) -> float:
        if cantidad <= 0:
            return monto_base
        grupos_completos = cantidad // self._n
        resto = cantidad % self._n
        unidades_a_pagar = grupos_completos * self._m + resto
        factor_a_pagar = unidades_a_pagar / cantidad
        return monto_base * factor_a_pagar

    @property
    def descripcion(self) -> str:
        return f"Promoción {self._n}x{self._m}"


class DescuentoPorVolumen(Descuento):
    """
    Descuento porcentual que solo se activa si se compra una cantidad
    mínima de unidades del mismo producto (ej: 10% off llevando 5 o más).
    """

    def __init__(self, cantidad_minima: int, porcentaje: float):
        self._cantidad_minima = cantidad_minima
        self._porcentaje = porcentaje

    def aplicar(self, cantidad: int, monto_base: float) -> float:
        if cantidad >= self._cantidad_minima:
            return monto_base * (1.0 - self._porcentaje)
        return monto_base

    @property
    def descripcion(self) -> str:
        return f"Desc. por volumen ({self._cantidad_minima}+ u.): {self._porcentaje * 100:.0f}%"


class DescuentoPorCategoria(Descuento):
    """
    Descuento porcentual plano asociado a una categoría/condición del
    cliente (ej: Jubilados, Empleados, Club de Beneficios). No depende
    de la cantidad comprada, solo del monto.
    """

    def __init__(self, nombre_categoria: str, porcentaje: float):
        self._nombre_categoria = nombre_categoria
        self._porcentaje = porcentaje

    def aplicar(self, cantidad: int, monto_base: float) -> float:
        return monto_base * (1.0 - self._porcentaje)

    @property
    def descripcion(self) -> str:
        return f"Desc. {self._nombre_categoria}: {self._porcentaje * 100:.0f}%"
