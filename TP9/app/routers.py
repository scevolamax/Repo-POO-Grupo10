"""Controladores HTTP.

Regla (SRP): cada endpoint solo recibe la request, delega en el servicio
y devuelve la respuesta. Sin if, sin cálculos, sin try/except: los errores
de dominio los traduce el exception handler de main.py.
"""
from fastapi import APIRouter, status

from app import schemas
from app.dependencies import (
    AccesoServiceDep,
    ClienteServiceDep,
    CotizacionServiceDep,
    EventoServiceDep,
    LugarServiceDep,
    SectorServiceDep,
    VentaServiceDep,
)
from app.models import EstadoEntrada

E400 = {400: {"model": schemas.ErrorRead, "description": "Regla de negocio violada"}}
E404 = {404: {"model": schemas.ErrorRead, "description": "Recurso no encontrado"}}
E409 = {409: {"model": schemas.ErrorRead, "description": "Conflicto con el estado actual"}}


# --- Lugares -----------------------------------------------------------------

lugares_router = APIRouter(prefix="/lugares", tags=["Lugares"])


@lugares_router.post("", response_model=schemas.LugarRead, status_code=status.HTTP_201_CREATED, summary="Crear lugar")
def crear_lugar(datos: schemas.LugarCreate, service: LugarServiceDep):
    return service.crear(datos)


@lugares_router.get("", response_model=list[schemas.LugarRead], summary="Listar lugares")
def listar_lugares(service: LugarServiceDep):
    return service.listar()


@lugares_router.get("/{lugar_id}", response_model=schemas.LugarRead, responses=E404, summary="Obtener lugar")
def obtener_lugar(lugar_id: int, service: LugarServiceDep):
    return service.obtener(lugar_id)


@lugares_router.put("/{lugar_id}", response_model=schemas.LugarRead, responses=E404, summary="Modificar lugar")
def actualizar_lugar(lugar_id: int, datos: schemas.LugarUpdate, service: LugarServiceDep):
    return service.actualizar(lugar_id, datos)


@lugares_router.delete(
    "/{lugar_id}", status_code=status.HTTP_204_NO_CONTENT, responses={**E404, **E409}, summary="Eliminar lugar"
)
def eliminar_lugar(lugar_id: int, service: LugarServiceDep) -> None:
    service.eliminar(lugar_id)


@lugares_router.post(
    "/{lugar_id}/sectores",
    response_model=schemas.SectorRead,
    status_code=status.HTTP_201_CREATED,
    responses={**E400, **E404, **E409},
    summary="Agregar sector a un lugar",
)
def crear_sector(lugar_id: int, datos: schemas.SectorCreate, service: SectorServiceDep):
    return service.crear(lugar_id, datos)


@lugares_router.get(
    "/{lugar_id}/sectores", response_model=list[schemas.SectorRead], responses=E404, summary="Listar sectores"
)
def listar_sectores(lugar_id: int, service: SectorServiceDep):
    return service.listar_por_lugar(lugar_id)


# --- Sectores ----------------------------------------------------------------

sectores_router = APIRouter(prefix="/sectores", tags=["Sectores"])


@sectores_router.get("/{sector_id}", response_model=schemas.SectorRead, responses=E404, summary="Obtener sector")
def obtener_sector(sector_id: int, service: SectorServiceDep):
    return service.obtener(sector_id)


@sectores_router.put(
    "/{sector_id}", response_model=schemas.SectorRead, responses={**E400, **E404, **E409}, summary="Modificar sector"
)
def actualizar_sector(sector_id: int, datos: schemas.SectorUpdate, service: SectorServiceDep):
    return service.actualizar(sector_id, datos)


@sectores_router.delete(
    "/{sector_id}", status_code=status.HTTP_204_NO_CONTENT, responses={**E404, **E409}, summary="Eliminar sector"
)
def eliminar_sector(sector_id: int, service: SectorServiceDep) -> None:
    service.eliminar(sector_id)


# --- Eventos -----------------------------------------------------------------

eventos_router = APIRouter(prefix="/eventos", tags=["Eventos"])


@eventos_router.post(
    "",
    response_model=schemas.EventoRead,
    status_code=status.HTTP_201_CREATED,
    responses={**E400, **E404},
    summary="Crear evento (define precios y genera las entradas)",
)
def crear_evento(datos: schemas.EventoCreate, service: EventoServiceDep):
    return service.crear(datos)


@eventos_router.get("", response_model=list[schemas.EventoRead], summary="Listar eventos")
def listar_eventos(service: EventoServiceDep):
    return service.listar()


@eventos_router.get("/{evento_id}", response_model=schemas.EventoRead, responses=E404, summary="Obtener evento")
def obtener_evento(evento_id: int, service: EventoServiceDep):
    return service.obtener(evento_id)


@eventos_router.get(
    "/{evento_id}/entradas",
    response_model=list[schemas.EntradaRead],
    responses=E404,
    summary="Listar entradas del evento",
)
def listar_entradas(evento_id: int, service: EventoServiceDep, estado: EstadoEntrada | None = None):
    return service.listar_entradas(evento_id, estado)


# --- Clientes ----------------------------------------------------------------

clientes_router = APIRouter(prefix="/clientes", tags=["Clientes"])


@clientes_router.post(
    "", response_model=schemas.ClienteRead, status_code=status.HTTP_201_CREATED, responses=E409, summary="Crear cliente"
)
def crear_cliente(datos: schemas.ClienteCreate, service: ClienteServiceDep):
    return service.crear(datos)


@clientes_router.get("", response_model=list[schemas.ClienteRead], summary="Listar clientes")
def listar_clientes(service: ClienteServiceDep):
    return service.listar()


@clientes_router.get("/{cliente_id}", response_model=schemas.ClienteRead, responses=E404, summary="Obtener cliente")
def obtener_cliente(cliente_id: int, service: ClienteServiceDep):
    return service.obtener(cliente_id)


@clientes_router.put(
    "/{cliente_id}", response_model=schemas.ClienteRead, responses={**E404, **E409}, summary="Modificar cliente"
)
def actualizar_cliente(cliente_id: int, datos: schemas.ClienteUpdate, service: ClienteServiceDep):
    return service.actualizar(cliente_id, datos)


@clientes_router.delete(
    "/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT, responses={**E404, **E409}, summary="Eliminar cliente"
)
def eliminar_cliente(cliente_id: int, service: ClienteServiceDep) -> None:
    service.eliminar(cliente_id)


# --- Ventas (HU 1 y HU 2) ----------------------------------------------------

ventas_router = APIRouter(prefix="/ventas", tags=["Ventas"])


@ventas_router.post(
    "/cotizar",
    response_model=schemas.CotizacionRead,
    responses={**E400, **E404},
    summary="HU 1 - Cotizar entradas",
)
def cotizar(solicitud: schemas.CotizacionRequest, service: CotizacionServiceDep):
    return service.cotizar(solicitud.evento_id, solicitud.sector_id, solicitud.cantidad)


@ventas_router.post(
    "/iniciar-pago",
    response_model=schemas.VentaRead,
    status_code=status.HTTP_201_CREATED,
    responses={**E400, **E404, **E409},
    summary="HU 2 - Pagar y emitir entradas",
)
def iniciar_pago(solicitud: schemas.SolicitudPagoRequest, service: VentaServiceDep):
    return service.iniciar_pago(
        solicitud.cliente_id,
        solicitud.evento_id,
        solicitud.sector_id,
        solicitud.entradas_ids,
        solicitud.tarjeta.a_dominio(),
    )


@ventas_router.get("/{venta_id}", response_model=schemas.VentaRead, responses=E404, summary="Obtener venta")
def obtener_venta(venta_id: int, service: VentaServiceDep):
    return service.obtener(venta_id)


# --- Accesos (HU 3) ----------------------------------------------------------

accesos_router = APIRouter(prefix="/accesos", tags=["Accesos"])


@accesos_router.post(
    "/escanear-acceso",
    response_model=schemas.AccesoRead,
    responses={**E400, **E404, **E409},
    summary="HU 3 - Escanear QR en puerta",
)
def escanear_acceso(solicitud: schemas.EscaneoRequest, service: AccesoServiceDep):
    return service.escanear(solicitud.codigo_qr)


TODOS_LOS_ROUTERS = (
    lugares_router,
    sectores_router,
    eventos_router,
    clientes_router,
    ventas_router,
    accesos_router,
)

