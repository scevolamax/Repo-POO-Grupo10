"""Excepciones de dominio.

No conocen HTTP: la traducción a códigos de estado se hace en main.py
mediante un exception handler, según la clase base de cada excepción.
"""


class DomainError(Exception):
    """Raíz de todos los errores de negocio."""

    mensaje_por_defecto = "Error de dominio"

    def __init__(self, mensaje: str | None = None) -> None:
        self.mensaje = mensaje or self.mensaje_por_defecto
        super().__init__(self.mensaje)


# --- Familias (cada una se mapea a un código HTTP) -------------------------


class RecursoNoEncontradoError(DomainError):
    mensaje_por_defecto = "Recurso no encontrado"


class ReglaNegocioError(DomainError):
    mensaje_por_defecto = "La operación viola una regla de negocio"


class ConflictoError(DomainError):
    mensaje_por_defecto = "La operación entra en conflicto con el estado actual"


# --- HU 1: Cotización -------------------------------------------------------


class CantidadInvalidaError(ReglaNegocioError):
    mensaje_por_defecto = "La cantidad de entradas solicitadas debe ser mayor a cero"


class StockInsuficienteError(ReglaNegocioError):
    mensaje_por_defecto = "Capacidad insuficiente o entradas no disponibles"


# --- HU 2: Pago y emisión ---------------------------------------------------


class PagoDenegadoError(ReglaNegocioError):
    mensaje_por_defecto = "Pago denegado"


class EntradasNoDisponiblesError(ConflictoError):
    mensaje_por_defecto = "Los lugares seleccionados ya no se encuentran disponibles"


# --- HU 3: Control de acceso ------------------------------------------------


class TicketInexistenteError(RecursoNoEncontradoError):
    mensaje_por_defecto = "Ticket Inválido o Inexistente"


class EntradaYaUtilizadaError(ConflictoError):
    mensaje_por_defecto = "Entrada ya utilizada"


class TicketNoEmitidoError(ReglaNegocioError):
    mensaje_por_defecto = "Ticket no emitido / Falta de pago"


# --- Invariantes e infraestructura -----------------------------------------


class TransicionEstadoInvalidaError(ConflictoError):
    mensaje_por_defecto = "Transición de estado inválida"


class ConflictoConcurrenciaError(ConflictoError):
    """Otro proceso modificó el mismo registro (bloqueo optimista)."""

    mensaje_por_defecto = "El recurso fue modificado por otra operación"


class IntegridadDatosError(ConflictoError):
    mensaje_por_defecto = "Conflicto de integridad de datos"

