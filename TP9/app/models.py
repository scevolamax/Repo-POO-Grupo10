"""Entidades del dominio (modelos SQLAlchemy con comportamiento).

Siguiendo Experto en Información, cada entidad encapsula las reglas y
transiciones de estado sobre los datos que posee. Los servicios solo
orquestan; los routers no contienen lógica.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, TypeDecorator, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.exceptions import (
    CantidadInvalidaError,
    ConflictoError,
    EntradasNoDisponiblesError,
    EntradaYaUtilizadaError,
    ReglaNegocioError,
    TicketNoEmitidoError,
    TransicionEstadoInvalidaError,
)

CENTAVO = Decimal("0.01")


# ---------------------------------------------------------------------------
# Tipos auxiliares
# ---------------------------------------------------------------------------


class Dinero(TypeDecorator):
    """Persiste importes Decimal como centavos enteros.

    SQLite no tiene un tipo decimal nativo: guardar centavos evita errores
    de redondeo de punto flotante.
    """

    impl = Integer
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return int((Decimal(value) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return (Decimal(value) / 100).quantize(CENTAVO)


class EstadoEntrada(enum.StrEnum):
    DISPONIBLE = "Disponible"
    RESERVADA = "Reservada"
    EMITIDA = "Emitida"
    UTILIZADA = "Utilizada"


class EstadoVenta(enum.StrEnum):
    PENDIENTE = "Pendiente"
    PAGADA = "Pagada"
    CANCELADA = "Cancelada"


def _valores_enum(enum_cls: type[enum.Enum]) -> list[str]:
    return [miembro.value for miembro in enum_cls]


def _columna_enum(enum_cls: type[enum.Enum]) -> SAEnum:
    return SAEnum(enum_cls, native_enum=False, values_callable=_valores_enum, length=20)


# ---------------------------------------------------------------------------
# Lugar y Sector
# ---------------------------------------------------------------------------


class Lugar(Base):
    __tablename__ = "lugares"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    direccion: Mapped[str] = mapped_column(String(200), nullable=False)

    sectores: Mapped[list[Sector]] = relationship(
        back_populates="lugar", cascade="all, delete-orphan", order_by="Sector.id"
    )

    def capacidad_total(self) -> int:
        return sum(sector.capacidad_maxima for sector in self.sectores)

    def tiene_sector(self, nombre: str, excluir_id: int | None = None) -> bool:
        nombre_normalizado = nombre.strip().lower()
        return any(
            sector.nombre.strip().lower() == nombre_normalizado and sector.id != excluir_id
            for sector in self.sectores
        )

    def agregar_sector(self, nombre: str, capacidad_maxima: int) -> Sector:
        """Creador: el Lugar compone sus Sectores."""
        Sector.validar_capacidad(capacidad_maxima)
        if self.tiene_sector(nombre):
            raise ConflictoError(f"Ya existe un sector '{nombre}' en este lugar")
        sector = Sector(nombre=nombre, capacidad_maxima=capacidad_maxima)
        self.sectores.append(sector)
        return sector


class Sector(Base):
    __tablename__ = "sectores"
    __table_args__ = (UniqueConstraint("lugar_id", "nombre", name="uq_sector_lugar_nombre"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    capacidad_maxima: Mapped[int] = mapped_column(Integer, nullable=False)
    lugar_id: Mapped[int] = mapped_column(ForeignKey("lugares.id", ondelete="CASCADE"), nullable=False)

    lugar: Mapped[Lugar] = relationship(back_populates="sectores")

    @staticmethod
    def validar_capacidad(capacidad_maxima: int) -> None:
        if capacidad_maxima <= 0:
            raise ReglaNegocioError("La capacidad máxima del sector debe ser mayor a cero")

    def actualizar(self, nombre: str, capacidad_maxima: int) -> None:
        Sector.validar_capacidad(capacidad_maxima)
        if self.lugar.tiene_sector(nombre, excluir_id=self.id):
            raise ConflictoError(f"Ya existe un sector '{nombre}' en este lugar")
        self.nombre = nombre
        self.capacidad_maxima = capacidad_maxima


# ---------------------------------------------------------------------------
# Evento y precios por sector
# ---------------------------------------------------------------------------


class Evento(Base):
    __tablename__ = "eventos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    lugar_id: Mapped[int] = mapped_column(ForeignKey("lugares.id"), nullable=False)

    lugar: Mapped[Lugar] = relationship()
    precios: Mapped[list[PrecioEventoSector]] = relationship(
        back_populates="evento", cascade="all, delete-orphan", order_by="PrecioEventoSector.id"
    )
    entradas: Mapped[list[Entrada]] = relationship(back_populates="evento", cascade="all, delete-orphan")

    @property
    def capacidad_total(self) -> int:
        return self.lugar.capacidad_total()

    def definir_precio(self, sector: Sector, precio: Decimal) -> PrecioEventoSector:
        """Creador: el Evento compone los precios de cada sector."""
        if sector.lugar_id != self.lugar.id:
            raise ReglaNegocioError(f"El sector '{sector.nombre}' no pertenece al lugar del evento")
        if precio <= 0:
            raise ReglaNegocioError("El precio de cada sector debe ser mayor a cero")
        if any(existente.sector.id == sector.id for existente in self.precios):
            raise ReglaNegocioError(f"El precio del sector '{sector.nombre}' está duplicado")
        precio_sector = PrecioEventoSector(sector=sector, precio=Decimal(precio).quantize(CENTAVO))
        self.precios.append(precio_sector)
        return precio_sector

    def generar_entradas(self) -> list[Entrada]:
        """Creador: pre-genera una Entrada 'Disponible' por cada lugar físico de cada sector."""
        self._validar_precios_completos()
        if self.entradas:
            raise ConflictoError("Las entradas del evento ya fueron generadas")
        nuevas = [
            Entrada.nueva(precio.sector)
            for precio in self.precios
            for _ in range(precio.sector.capacidad_maxima)
        ]
        self.entradas.extend(nuevas)
        return nuevas

    def precio_para(self, sector_id: int) -> PrecioEventoSector | None:
        return next((precio for precio in self.precios if precio.sector.id == sector_id), None)

    def _validar_precios_completos(self) -> None:
        sectores_del_lugar = {sector.id: sector.nombre for sector in self.lugar.sectores}
        if not sectores_del_lugar:
            raise ReglaNegocioError("El lugar no tiene sectores definidos")
        con_precio = {precio.sector.id for precio in self.precios}
        faltantes = [nombre for sector_id, nombre in sectores_del_lugar.items() if sector_id not in con_precio]
        if faltantes:
            raise ReglaNegocioError(f"Falta definir el precio para los sectores: {', '.join(faltantes)}")


class PrecioEventoSector(Base):
    __tablename__ = "precios_evento_sector"
    __table_args__ = (UniqueConstraint("evento_id", "sector_id", name="uq_precio_evento_sector"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    evento_id: Mapped[int] = mapped_column(ForeignKey("eventos.id", ondelete="CASCADE"), nullable=False)
    sector_id: Mapped[int] = mapped_column(ForeignKey("sectores.id"), nullable=False)
    precio: Mapped[Decimal] = mapped_column(Dinero, nullable=False)

    evento: Mapped[Evento] = relationship(back_populates="precios")
    sector: Mapped[Sector] = relationship()

    @property
    def sector_nombre(self) -> str:
        return self.sector.nombre

    @staticmethod
    def validar_cantidad(cantidad: int) -> None:
        if cantidad <= 0:
            raise CantidadInvalidaError()

    def calcular_subtotal(self, cantidad: int) -> Decimal:
        """Experto en Información: el precio sabe calcular su subtotal."""
        PrecioEventoSector.validar_cantidad(cantidad)
        return (self.precio * cantidad).quantize(CENTAVO)


# ---------------------------------------------------------------------------
# Entrada
# ---------------------------------------------------------------------------


class Entrada(Base):
    __tablename__ = "entradas"
    __table_args__ = (Index("ix_entrada_evento_sector_estado", "evento_id", "sector_id", "estado"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo_qr: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    estado: Mapped[EstadoEntrada] = mapped_column(_columna_enum(EstadoEntrada), nullable=False)
    hora_ingreso: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    evento_id: Mapped[int] = mapped_column(ForeignKey("eventos.id", ondelete="CASCADE"), nullable=False)
    sector_id: Mapped[int] = mapped_column(ForeignKey("sectores.id"), nullable=False)
    venta_id: Mapped[int | None] = mapped_column(ForeignKey("ventas.id"), nullable=True)

    evento: Mapped[Evento] = relationship(back_populates="entradas")
    sector: Mapped[Sector] = relationship()
    venta: Mapped[Venta | None] = relationship(back_populates="entradas")

    # Bloqueo optimista: cada UPDATE incluye "WHERE version = <leida>".
    # Si otro proceso la modificó antes, SQLAlchemy lanza StaleDataError.
    __mapper_args__ = {"version_id_col": version}

    @classmethod
    def nueva(cls, sector: Sector) -> Entrada:
        return cls(sector=sector, codigo_qr=str(uuid.uuid4()), estado=EstadoEntrada.DISPONIBLE)

    def esta_disponible(self) -> bool:
        return self.estado == EstadoEntrada.DISPONIBLE

    def reservar(self, venta: Venta) -> None:
        if not self.esta_disponible():
            raise EntradasNoDisponiblesError()
        self.estado = EstadoEntrada.RESERVADA
        self.venta = venta

    def emitir(self) -> None:
        if self.estado != EstadoEntrada.RESERVADA:
            raise TransicionEstadoInvalidaError("Solo se puede emitir una entrada reservada")
        self.estado = EstadoEntrada.EMITIDA

    def liberar(self) -> None:
        if self.estado != EstadoEntrada.RESERVADA:
            raise TransicionEstadoInvalidaError("Solo se puede liberar una entrada reservada")
        self.estado = EstadoEntrada.DISPONIBLE
        self.venta = None

    def registrar_ingreso(self, ahora: datetime) -> None:
        """Valida el acceso. Nunca sobrescribe una hora de ingreso previa."""
        if self.estado == EstadoEntrada.UTILIZADA:
            raise EntradaYaUtilizadaError()
        if self.estado != EstadoEntrada.EMITIDA:
            raise TicketNoEmitidoError()
        self.estado = EstadoEntrada.UTILIZADA
        self.hora_ingreso = ahora


# ---------------------------------------------------------------------------
# Cliente y Venta
# ---------------------------------------------------------------------------


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    dni: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)

    ventas: Mapped[list[Venta]] = relationship(back_populates="cliente")


class Venta(Base):
    __tablename__ = "ventas"

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    estado: Mapped[EstadoVenta] = mapped_column(_columna_enum(EstadoVenta), nullable=False)
    total: Mapped[Decimal] = mapped_column(Dinero, nullable=False)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False)

    cliente: Mapped[Cliente] = relationship(back_populates="ventas")
    entradas: Mapped[list[Entrada]] = relationship(back_populates="venta", order_by="Entrada.id")

    @classmethod
    def iniciar(cls, cliente: Cliente) -> Venta:
        return cls(cliente=cliente, fecha=datetime.now(), estado=EstadoVenta.PENDIENTE, total=Decimal("0.00"))

    def agregar_entradas(self, entradas: list[Entrada], precio: PrecioEventoSector) -> None:
        """Reserva todas las entradas o ninguna, y calcula el total."""
        self._exigir_estado(EstadoVenta.PENDIENTE)
        if any(not entrada.esta_disponible() for entrada in entradas):
            raise EntradasNoDisponiblesError()
        for entrada in entradas:
            entrada.reservar(self)
        self.total = precio.calcular_subtotal(len(entradas))

    def confirmar_pago(self) -> None:
        self._exigir_estado(EstadoVenta.PENDIENTE)
        for entrada in self.entradas:
            entrada.emitir()
        self.estado = EstadoVenta.PAGADA

    def cancelar(self) -> None:
        self._exigir_estado(EstadoVenta.PENDIENTE)
        # Copia: liberar() desasocia la entrada y la quita de self.entradas.
        for entrada in list(self.entradas):
            entrada.liberar()
        self.estado = EstadoVenta.CANCELADA

    def _exigir_estado(self, esperado: EstadoVenta) -> None:
        if self.estado != esperado:
            raise TransicionEstadoInvalidaError(
                f"La venta está en estado '{self.estado}' y se esperaba '{esperado}'"
            )

