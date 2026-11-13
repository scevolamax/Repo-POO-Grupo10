"""Composition root: construcción de repositorios y servicios con Depends.

Es el único lugar que conoce las implementaciones concretas (por ejemplo,
PasarelaPagosSimulada). En tests se reemplazan con app.dependency_overrides.
"""
from datetime import datetime
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.pasarela import PasarelaPagos, PasarelaPagosSimulada
from app.repositories import (
    ClienteRepository,
    EntradaRepository,
    EventoRepository,
    LugarRepository,
    SectorRepository,
    UnidadDeTrabajo,
    VentaRepository,
)
from app.services import (
    AccesoService,
    ClienteService,
    CotizacionService,
    EventoService,
    LugarService,
    Reloj,
    SectorService,
    VentaService,
)

DbSession = Annotated[Session, Depends(get_db)]


# --- Infraestructura ---------------------------------------------------------


def get_unidad_de_trabajo(db: DbSession) -> UnidadDeTrabajo:
    return UnidadDeTrabajo(db)


def get_pasarela() -> PasarelaPagos:
    return PasarelaPagosSimulada()


def get_reloj() -> Reloj:
    # Hora local del servidor (la del predio donde se controla el acceso).
    return datetime.now


# --- Repositorios ------------------------------------------------------------


def get_lugar_repository(db: DbSession) -> LugarRepository:
    return LugarRepository(db)


def get_sector_repository(db: DbSession) -> SectorRepository:
    return SectorRepository(db)


def get_evento_repository(db: DbSession) -> EventoRepository:
    return EventoRepository(db)


def get_entrada_repository(db: DbSession) -> EntradaRepository:
    return EntradaRepository(db)


def get_cliente_repository(db: DbSession) -> ClienteRepository:
    return ClienteRepository(db)


def get_venta_repository(db: DbSession) -> VentaRepository:
    return VentaRepository(db)


UoWDep = Annotated[UnidadDeTrabajo, Depends(get_unidad_de_trabajo)]
PasarelaDep = Annotated[PasarelaPagos, Depends(get_pasarela)]
RelojDep = Annotated[Reloj, Depends(get_reloj)]
LugarRepoDep = Annotated[LugarRepository, Depends(get_lugar_repository)]
SectorRepoDep = Annotated[SectorRepository, Depends(get_sector_repository)]
EventoRepoDep = Annotated[EventoRepository, Depends(get_evento_repository)]
EntradaRepoDep = Annotated[EntradaRepository, Depends(get_entrada_repository)]
ClienteRepoDep = Annotated[ClienteRepository, Depends(get_cliente_repository)]
VentaRepoDep = Annotated[VentaRepository, Depends(get_venta_repository)]


# --- Servicios ---------------------------------------------------------------


def get_lugar_service(lugares: LugarRepoDep, eventos: EventoRepoDep, uow: UoWDep) -> LugarService:
    return LugarService(lugares, eventos, uow)


def get_sector_service(
    lugares: LugarRepoDep, sectores: SectorRepoDep, eventos: EventoRepoDep, uow: UoWDep
) -> SectorService:
    return SectorService(lugares, sectores, eventos, uow)


def get_cliente_service(clientes: ClienteRepoDep, ventas: VentaRepoDep, uow: UoWDep) -> ClienteService:
    return ClienteService(clientes, ventas, uow)


def get_evento_service(
    eventos: EventoRepoDep,
    lugares: LugarRepoDep,
    sectores: SectorRepoDep,
    entradas: EntradaRepoDep,
    uow: UoWDep,
) -> EventoService:
    return EventoService(eventos, lugares, sectores, entradas, uow)


def get_cotizacion_service(eventos: EventoRepoDep, entradas: EntradaRepoDep) -> CotizacionService:
    return CotizacionService(eventos, entradas)


def get_venta_service(
    clientes: ClienteRepoDep,
    eventos: EventoRepoDep,
    entradas: EntradaRepoDep,
    ventas: VentaRepoDep,
    uow: UoWDep,
    pasarela: PasarelaDep,
) -> VentaService:
    return VentaService(clientes, eventos, entradas, ventas, uow, pasarela)


def get_acceso_service(entradas: EntradaRepoDep, uow: UoWDep, reloj: RelojDep) -> AccesoService:
    return AccesoService(entradas, uow, reloj)


LugarServiceDep = Annotated[LugarService, Depends(get_lugar_service)]
SectorServiceDep = Annotated[SectorService, Depends(get_sector_service)]
ClienteServiceDep = Annotated[ClienteService, Depends(get_cliente_service)]
EventoServiceDep = Annotated[EventoService, Depends(get_evento_service)]
CotizacionServiceDep = Annotated[CotizacionService, Depends(get_cotizacion_service)]
VentaServiceDep = Annotated[VentaService, Depends(get_venta_service)]
AccesoServiceDep = Annotated[AccesoService, Depends(get_acceso_service)]

