"""Repositorios (Indirección / Fabricación Pura sobre la persistencia).

Los repositorios no confirman transacciones: eso lo decide el servicio a
través de la UnidadDeTrabajo, que además traduce errores de SQLAlchemy a
excepciones de dominio para que los servicios no dependan del ORM.
"""
from collections.abc import Sequence

from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from app.exceptions import ConflictoConcurrenciaError, IntegridadDatosError
from app.models import (
    Cliente,
    Entrada,
    EstadoEntrada,
    Evento,
    Lugar,
    PrecioEventoSector,
    Sector,
    Venta,
)


class UnidadDeTrabajo:
    def __init__(self, db: Session) -> None:
        self._db = db

    def confirmar(self) -> None:
        try:
            self._db.commit()
        except StaleDataError as exc:
            self._db.rollback()
            raise ConflictoConcurrenciaError() from exc
        except IntegrityError as exc:
            self._db.rollback()
            raise IntegridadDatosError() from exc

    def revertir(self) -> None:
        self._db.rollback()


class LugarRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def agregar(self, lugar: Lugar) -> Lugar:
        self._db.add(lugar)
        return lugar

    def obtener(self, lugar_id: int) -> Lugar | None:
        return self._db.get(Lugar, lugar_id)

    def listar(self) -> Sequence[Lugar]:
        return self._db.scalars(select(Lugar).order_by(Lugar.id)).all()

    def eliminar(self, lugar: Lugar) -> None:
        self._db.delete(lugar)


class SectorRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def obtener(self, sector_id: int) -> Sector | None:
        return self._db.get(Sector, sector_id)

    def listar_por_lugar(self, lugar_id: int) -> Sequence[Sector]:
        return self._db.scalars(select(Sector).where(Sector.lugar_id == lugar_id).order_by(Sector.id)).all()

    def eliminar(self, sector: Sector) -> None:
        self._db.delete(sector)


class EventoRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def agregar(self, evento: Evento) -> Evento:
        self._db.add(evento)
        return evento

    def obtener(self, evento_id: int) -> Evento | None:
        return self._db.get(Evento, evento_id)

    def listar(self) -> Sequence[Evento]:
        return self._db.scalars(select(Evento).order_by(Evento.fecha, Evento.id)).all()

    def obtener_precio(self, evento_id: int, sector_id: int) -> PrecioEventoSector | None:
        consulta = select(PrecioEventoSector).where(
            PrecioEventoSector.evento_id == evento_id,
            PrecioEventoSector.sector_id == sector_id,
        )
        return self._db.scalars(consulta).first()

    def existe_para_lugar(self, lugar_id: int) -> bool:
        return bool(self._db.scalar(select(exists().where(Evento.lugar_id == lugar_id))))

    def existe_para_sector(self, sector_id: int) -> bool:
        return bool(self._db.scalar(select(exists().where(PrecioEventoSector.sector_id == sector_id))))


class EntradaRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def buscar_disponibles(self, evento_id: int, sector_id: int, limite: int) -> Sequence[Entrada]:
        consulta = (
            select(Entrada)
            .where(
                Entrada.evento_id == evento_id,
                Entrada.sector_id == sector_id,
                Entrada.estado == EstadoEntrada.DISPONIBLE,
            )
            .order_by(Entrada.id)
            .limit(limite)
        )
        return self._db.scalars(consulta).all()

    def obtener_por_ids(self, ids: Sequence[int]) -> Sequence[Entrada]:
        return self._db.scalars(select(Entrada).where(Entrada.id.in_(ids)).order_by(Entrada.id)).all()

    def buscar_por_qr(self, codigo_qr: str) -> Entrada | None:
        return self._db.scalars(select(Entrada).where(Entrada.codigo_qr == codigo_qr)).first()

    def listar_por_evento(self, evento_id: int, estado: EstadoEntrada | None = None) -> Sequence[Entrada]:
        consulta = select(Entrada).where(Entrada.evento_id == evento_id)
        if estado is not None:
            consulta = consulta.where(Entrada.estado == estado)
        return self._db.scalars(consulta.order_by(Entrada.id)).all()


class ClienteRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def agregar(self, cliente: Cliente) -> Cliente:
        self._db.add(cliente)
        return cliente

    def obtener(self, cliente_id: int) -> Cliente | None:
        return self._db.get(Cliente, cliente_id)

    def listar(self) -> Sequence[Cliente]:
        return self._db.scalars(select(Cliente).order_by(Cliente.id)).all()

    def obtener_por_email(self, email: str) -> Cliente | None:
        return self._db.scalars(select(Cliente).where(Cliente.email == email)).first()

    def obtener_por_dni(self, dni: str) -> Cliente | None:
        return self._db.scalars(select(Cliente).where(Cliente.dni == dni)).first()

    def eliminar(self, cliente: Cliente) -> None:
        self._db.delete(cliente)


class VentaRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def agregar(self, venta: Venta) -> Venta:
        self._db.add(venta)
        return venta

    def obtener(self, venta_id: int) -> Venta | None:
        return self._db.get(Venta, venta_id)

    def existe_para_cliente(self, cliente_id: int) -> bool:
        return bool(self._db.scalar(select(exists().where(Venta.cliente_id == cliente_id))))

