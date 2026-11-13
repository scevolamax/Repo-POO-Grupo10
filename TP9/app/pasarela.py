"""Pasarela de pagos: abstracción (DIP) + implementación simulada.

VentaService depende únicamente de PasarelaPagos. La implementación
concreta se elige en dependencies.py y puede reemplazarse sin modificar
el servicio (OCP / Polimorfismo).
"""
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class DatosTarjeta:
    numero: str
    titular: str
    vencimiento: str
    cvv: str


@dataclass(frozen=True)
class ResultadoPago:
    aprobado: bool
    codigo_autorizacion: str | None = None
    motivo: str | None = None


class PasarelaPagos(ABC):
    @abstractmethod
    def procesar_pago(self, monto: Decimal, tarjeta: DatosTarjeta) -> ResultadoPago:
        """Intenta cobrar el monto. Debe retornar un resultado, no lanzar por rechazo."""


class PasarelaPagosSimulada(PasarelaPagos):
    """Aprueba todos los pagos salvo tarjetas terminadas en '0000'."""

    SUFIJO_RECHAZO = "0000"

    def procesar_pago(self, monto: Decimal, tarjeta: DatosTarjeta) -> ResultadoPago:
        if tarjeta.numero.endswith(self.SUFIJO_RECHAZO):
            return ResultadoPago(aprobado=False, motivo="Fondos insuficientes")
        return ResultadoPago(aprobado=True, codigo_autorizacion=uuid.uuid4().hex[:12].upper())

