"""Esquemas Pydantic (DTOs de entrada y salida de la API)."""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models import EstadoEntrada, EstadoVenta
from app.pasarela import DatosTarjeta


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ErrorRead(BaseModel):
    detail: str


# --- Lugar / Sector --------------------------------------------------------


class SectorCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=80, examples=["Platea"])
    capacidad_maxima: int = Field(examples=[500])


class SectorUpdate(SectorCreate):
    pass


class SectorRead(ORMModel):
    id: int
    nombre: str
    capacidad_maxima: int
    lugar_id: int


class LugarCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=120, examples=["Estadio Único"])
    direccion: str = Field(min_length=1, max_length=200, examples=["Av. 32 y 25, La Plata"])


class LugarUpdate(LugarCreate):
    pass


class LugarRead(ORMModel):
    id: int
    nombre: str
    direccion: str
    sectores: list[SectorRead] = []


# --- Evento -----------------------------------------------------------------


class PrecioSectorIn(BaseModel):
    sector_id: int
    precio: Decimal = Field(gt=0, max_digits=12, decimal_places=2, examples=["12000.00"])


class EventoCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=150, examples=["Rock Fest"])
    fecha: datetime
    lugar_id: int
    precios: list[PrecioSectorIn] = Field(min_length=1)


class PrecioSectorRead(ORMModel):
    sector_id: int
    sector_nombre: str
    precio: Decimal


class EventoRead(ORMModel):
    id: int
    nombre: str
    fecha: datetime
    lugar_id: int
    capacidad_total: int
    precios: list[PrecioSectorRead]


class EntradaRead(ORMModel):
    id: int
    codigo_qr: str
    estado: EstadoEntrada
    hora_ingreso: datetime | None
    evento_id: int
    sector_id: int
    venta_id: int | None


# --- Cliente ----------------------------------------------------------------


class ClienteCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=120, examples=["Ana Pérez"])
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=150, examples=["ana@mail.com"])
    dni: str = Field(pattern=r"^\d{7,8}$", examples=["30123456"])


class ClienteUpdate(ClienteCreate):
    pass


class ClienteRead(ORMModel):
    id: int
    nombre: str
    email: str
    dni: str


# --- HU 1: Cotización -------------------------------------------------------


class CotizacionRequest(BaseModel):
    evento_id: int
    sector_id: int
    # Sin Field(gt=0) a propósito: la regla es de negocio y debe responder 400
    # con un mensaje exacto (Pydantic respondería 422 genérico).
    cantidad: int = Field(examples=[2])


class CotizacionRead(ORMModel):
    evento_id: int
    sector_id: int
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal
    total: Decimal
    entradas_ids: list[int]


# --- HU 2: Pago -------------------------------------------------------------


class TarjetaIn(BaseModel):
    numero: str = Field(pattern=r"^\d{13,19}$", examples=["4111111111111111"])
    titular: str = Field(min_length=1, max_length=120, examples=["Ana Pérez"])
    vencimiento: str = Field(pattern=r"^(0[1-9]|1[0-2])/\d{2}$", examples=["12/28"])
    cvv: str = Field(pattern=r"^\d{3,4}$", examples=["123"])

    def a_dominio(self) -> DatosTarjeta:
        """Convierte el DTO en el value object que entiende la pasarela."""
        return DatosTarjeta(numero=self.numero, titular=self.titular, vencimiento=self.vencimiento, cvv=self.cvv)


class SolicitudPagoRequest(BaseModel):
    cliente_id: int
    evento_id: int
    sector_id: int
    entradas_ids: list[int] = Field(min_length=1)
    tarjeta: TarjetaIn


class VentaRead(ORMModel):
    id: int
    fecha: datetime
    estado: EstadoVenta
    total: Decimal
    cliente_id: int
    entradas: list[EntradaRead]


# --- HU 3: Acceso -----------------------------------------------------------


class EscaneoRequest(BaseModel):
    codigo_qr: str = Field(min_length=1, max_length=64)


class AccesoRead(ORMModel):
    mensaje: str
    entrada_id: int
    hora_ingreso: datetime
