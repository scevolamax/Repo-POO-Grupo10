"""Servicios de aplicación (Controladores de caso de uso en términos GRASP).

Orquestan repositorios y entidades. Las reglas y transiciones de estado
viven en las entidades (models.py); aquí solo se coordina el flujo y se
define el límite transaccional.
"""
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app import schemas
from app.exceptions import (
    ConflictoConcurrenciaError,
    ConflictoError,
    EntradasNoDisponiblesError,
    EntradaYaUtilizadaError,
    PagoDenegadoError,
    RecursoNoEncontradoError,
    ReglaNegocioError,
    StockInsuficienteError,
    TicketInexistenteError,
)
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
from app.pasarela import DatosTarjeta, PasarelaPagos
from app.repositories import (
    ClienteRepository,
    EntradaRepository,
    EventoRepository,
    LugarRepository,
    SectorRepository,
    UnidadDeTrabajo,
    VentaRepository,
)

Reloj = Callable[[], datetime]


# ===========================================================================
# CRUDs
# ===========================================================================


class LugarService:
    def __init__(self, lugares: LugarRepository, eventos: EventoRepository, uow: UnidadDeTrabajo) -> None:
        self._lugares = lugares
        self._eventos = eventos
        self._uow = uow

    def crear(self, datos: schemas.LugarCreate) -> Lugar:
        lugar = Lugar(nombre=datos.nombre, direccion=datos.direccion, sectores=[])
        self._lugares.agregar(lugar)
        self._uow.confirmar()
        return lugar

    def listar(self) -> Sequence[Lugar]:
        return self._lugares.listar()

    def obtener(self, lugar_id: int) -> Lugar:
        lugar = self._lugares.obtener(lugar_id)
        if lugar is None:
            raise RecursoNoEncontradoError("Lugar no encontrado")
        return lugar

    def actualizar(self, lugar_id: int, datos: schemas.LugarUpdate) -> Lugar:
        lugar = self.obtener(lugar_id)
        lugar.nombre = datos.nombre
        lugar.direccion = datos.direccion
        self._uow.confirmar()
        return lugar

    def eliminar(self, lugar_id: int) -> None:
        lugar = self.obtener(lugar_id)
        if self._eventos.existe_para_lugar(lugar_id):
            raise ConflictoError("No se puede eliminar un lugar con eventos asociados")
        self._lugares.eliminar(lugar)
        self._uow.confirmar()


class SectorService:
    def __init__(
        self,
        lugares: LugarRepository,
        sectores: SectorRepository,
        eventos: EventoRepository,
        uow: UnidadDeTrabajo,
    ) -> None:
        self._lugares = lugares
        self._sectores = sectores
        self._eventos = eventos
        self._uow = uow

    def crear(self, lugar_id: int, datos: schemas.SectorCreate) -> Sector:
        lugar = self._lugares.obtener(lugar_id)
        if lugar is None:
            raise RecursoNoEncontradoError("Lugar no encontrado")
        sector = lugar.agregar_sector(datos.nombre, datos.capacidad_maxima)
        self._uow.confirmar()
        return sector

    def listar_por_lugar(self, lugar_id: int) -> Sequence[Sector]:
        if self._lugares.obtener(lugar_id) is None:
            raise RecursoNoEncontradoError("Lugar no encontrado")
        return self._sectores.listar_por_lugar(lugar_id)

    def obtener(self, sector_id: int) -> Sector:
        sector = self._sectores.obtener(sector_id)
        if sector is None:
            raise RecursoNoEncontradoError("Sector no encontrado")
        return sector

    def actualizar(self, sector_id: int, datos: schemas.SectorUpdate) -> Sector:
        sector = self.obtener(sector_id)
        self._exigir_sin_eventos(sector_id, "modificar")
        sector.actualizar(datos.nombre, datos.capacidad_maxima)
        self._uow.confirmar()
        return sector

    def eliminar(self, sector_id: int) -> None:
        sector = self.obtener(sector_id)
        self._exigir_sin_eventos(sector_id, "eliminar")
        self._sectores.eliminar(sector)
        self._uow.confirmar()

    def _exigir_sin_eventos(self, sector_id: int, accion: str) -> None:
        # Las entradas se generan a partir de la capacidad: cambiarla después
        # dejaría eventos inconsistentes.
        if self._eventos.existe_para_sector(sector_id):
            raise ConflictoError(f"No se puede {accion} un sector con eventos asociados")


class ClienteService:
    def __init__(self, clientes: ClienteRepository, ventas: VentaRepository, uow: UnidadDeTrabajo) -> None:
        self._clientes = clientes
        self._ventas = ventas
        self._uow = uow

    def crear(self, datos: schemas.ClienteCreate) -> Cliente:
        self._exigir_datos_unicos(datos.email, datos.dni)
        cliente = Cliente(nombre=datos.nombre, email=datos.email.lower(), dni=datos.dni)
        self._clientes.agregar(cliente)
        self._uow.confirmar()
        return cliente

    def listar(self) -> Sequence[Cliente]:
        return self._clientes.listar()

    def obtener(self, cliente_id: int) -> Cliente:
        cliente = self._clientes.obtener(cliente_id)
        if cliente is None:
            raise RecursoNoEncontradoError("Cliente no encontrado")
        return cliente

    def actualizar(self, cliente_id: int, datos: schemas.ClienteUpdate) -> Cliente:
        cliente = self.obtener(cliente_id)
        self._exigir_datos_unicos(datos.email, datos.dni, excluir_id=cliente_id)
        cliente.nombre = datos.nombre
        cliente.email = datos.email.lower()
        cliente.dni = datos.dni
        self._uow.confirmar()
        return cliente

    def eliminar(self, cliente_id: int) -> None:
        cliente = self.obtener(cliente_id)
        if self._ventas.existe_para_cliente(cliente_id):
            raise ConflictoError("No se puede eliminar un cliente con ventas registradas")
        self._clientes.eliminar(cliente)
        self._uow.confirmar()

    def _exigir_datos_unicos(self, email: str, dni: str, excluir_id: int | None = None) -> None:
        por_email = self._clientes.obtener_por_email(email.lower())
        if por_email is not None and por_email.id != excluir_id:
            raise ConflictoError("Ya existe un cliente con ese email")
        por_dni = self._clientes.obtener_por_dni(dni)
        if por_dni is not None and por_dni.id != excluir_id:
            raise ConflictoError("Ya existe un cliente con ese DNI")


class EventoService:
    def __init__(
        self,
        eventos: EventoRepository,
        lugares: LugarRepository,
        sectores: SectorRepository,
        entradas: EntradaRepository,
        uow: UnidadDeTrabajo,
    ) -> None:
        self._eventos = eventos
        self._lugares = lugares
        self._sectores = sectores
        self._entradas = entradas
        self._uow = uow

    def crear(self, datos: schemas.EventoCreate) -> Evento:
        """Crea el evento, define precios por sector y pre-genera las entradas (una sola transacción)."""
        lugar = self._lugares.obtener(datos.lugar_id)
        if lugar is None:
            raise RecursoNoEncontradoError("Lugar no encontrado")

        evento = Evento(nombre=datos.nombre, fecha=datos.fecha, lugar=lugar)
        for item in datos.precios:
            sector = self._sectores.obtener(item.sector_id)
            if sector is None:
                raise RecursoNoEncontradoError(f"Sector {item.sector_id} no encontrado")
            evento.definir_precio(sector, item.precio)
        evento.generar_entradas()

        self._eventos.agregar(evento)
        self._uow.confirmar()
        return evento

    def listar(self) -> Sequence[Evento]:
        return self._eventos.listar()

    def obtener(self, evento_id: int) -> Evento:
        evento = self._eventos.obtener(evento_id)
        if evento is None:
            raise RecursoNoEncontradoError("Evento no encontrado")
        return evento

    def listar_entradas(self, evento_id: int, estado: EstadoEntrada | None = None) -> Sequence[Entrada]:
        self.obtener(evento_id)
        return self._entradas.listar_por_evento(evento_id, estado)


# ===========================================================================
# HU 1 - Selección y Cotización
# ===========================================================================


@dataclass(frozen=True)
class Cotizacion:
    evento_id: int
    sector_id: int
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal
    total: Decimal
    entradas_ids: list[int]


class CotizacionService:
    def __init__(self, eventos: EventoRepository, entradas: EntradaRepository) -> None:
        self._eventos = eventos
        self._entradas = entradas

    def cotizar(self, evento_id: int, sector_id: int, cantidad: int) -> Cotizacion:
        # 1. Validación inmediata, antes de tocar la base de datos.
        PrecioEventoSector.validar_cantidad(cantidad)

        precio = self._eventos.obtener_precio(evento_id, sector_id)
        if precio is None:
            raise RecursoNoEncontradoError("Evento o sector no encontrado")

        # 2. Stock físico: no se reserva nada; solo se verifica disponibilidad.
        disponibles = self._entradas.buscar_disponibles(evento_id, sector_id, limite=cantidad)
        if len(disponibles) < cantidad:
            raise StockInsuficienteError()

        # 3. Cálculo delegado al Experto (el precio del sector).
        subtotal = precio.calcular_subtotal(cantidad)
        return Cotizacion(
            evento_id=evento_id,
            sector_id=sector_id,
            cantidad=cantidad,
            precio_unitario=precio.precio,
            subtotal=subtotal,
            total=subtotal,
            entradas_ids=[entrada.id for entrada in disponibles],
        )


# ===========================================================================
# HU 2 - Procesamiento de Pago y Emisión
# ===========================================================================


class VentaService:
    def __init__(
        self,
        clientes: ClienteRepository,
        eventos: EventoRepository,
        entradas: EntradaRepository,
        ventas: VentaRepository,
        uow: UnidadDeTrabajo,
        pasarela: PasarelaPagos,
    ) -> None:
        self._clientes = clientes
        self._eventos = eventos
        self._entradas = entradas
        self._ventas = ventas
        self._uow = uow
        self._pasarela = pasarela  # DIP: abstracción, no implementación concreta

    def obtener(self, venta_id: int) -> Venta:
        venta = self._ventas.obtener(venta_id)
        if venta is None:
            raise RecursoNoEncontradoError("Venta no encontrada")
        return venta

    def iniciar_pago(
        self,
        cliente_id: int,
        evento_id: int,
        sector_id: int,
        entradas_ids: Sequence[int],
        tarjeta: DatosTarjeta,
    ) -> Venta:
        cliente = self._clientes.obtener(cliente_id)
        if cliente is None:
            raise RecursoNoEncontradoError("Cliente no encontrado")
        precio = self._eventos.obtener_precio(evento_id, sector_id)
        if precio is None:
            raise RecursoNoEncontradoError("Evento o sector no encontrado")
        entradas = self._obtener_entradas_seleccionadas(evento_id, sector_id, entradas_ids)

        venta = self._reservar(cliente, entradas, precio)  # Fase 1
        resultado = self._cobrar(venta, tarjeta)  # Fase 2
        self._confirmar_o_cancelar(venta, resultado.aprobado)  # Fase 3
        return venta

    def _obtener_entradas_seleccionadas(
        self, evento_id: int, sector_id: int, entradas_ids: Sequence[int]
    ) -> Sequence[Entrada]:
        if len(set(entradas_ids)) != len(entradas_ids):
            raise ReglaNegocioError("La selección contiene entradas repetidas")
        entradas = self._entradas.obtener_por_ids(entradas_ids)
        pertenecen = all(e.evento_id == evento_id and e.sector_id == sector_id for e in entradas)
        if len(entradas) != len(entradas_ids) or not pertenecen:
            raise ReglaNegocioError("Las entradas seleccionadas no corresponden al evento y sector indicados")
        return entradas

    def _reservar(self, cliente: Cliente, entradas: Sequence[Entrada], precio: PrecioEventoSector) -> Venta:
        """Control de concurrencia ANTES de consultar a la pasarela."""
        venta = Venta.iniciar(cliente)
        self._ventas.agregar(venta)
        try:
            venta.agregar_entradas(list(entradas), precio)
            self._uow.confirmar()
        except EntradasNoDisponiblesError:
            self._uow.revertir()
            raise
        except ConflictoConcurrenciaError as exc:
            # Otro cliente las reservó entre nuestra lectura y nuestra escritura.
            raise EntradasNoDisponiblesError() from exc
        return venta

    def _cobrar(self, venta: Venta, tarjeta: DatosTarjeta):
        try:
            return self._pasarela.procesar_pago(venta.total, tarjeta)
        except Exception:
            # Falla técnica de la pasarela: compensar para no dejar entradas colgadas.
            venta.cancelar()
            self._uow.confirmar()
            raise

    def _confirmar_o_cancelar(self, venta: Venta, aprobado: bool) -> None:
        if not aprobado:
            venta.cancelar()  # las entradas vuelven a 'Disponible'
            self._uow.confirmar()
            raise PagoDenegadoError()
        venta.confirmar_pago()  # venta 'Pagada', entradas 'Emitida'
        self._uow.confirmar()


# ===========================================================================
# HU 3 - Control de Acceso en Puerta
# ===========================================================================


@dataclass(frozen=True)
class ResultadoAcceso:
    mensaje: str
    entrada_id: int
    hora_ingreso: datetime


class AccesoService:
    MENSAJE_ACCESO_PERMITIDO = "Acceso Permitido"

    def __init__(self, entradas: EntradaRepository, uow: UnidadDeTrabajo, reloj: Reloj) -> None:
        self._entradas = entradas
        self._uow = uow
        self._reloj = reloj  # DIP: la hora se inyecta (testeable)

    def escanear(self, codigo_qr: str) -> ResultadoAcceso:
        entrada = self._entradas.buscar_por_qr(codigo_qr)
        if entrada is None:
            raise TicketInexistenteError()

        entrada.registrar_ingreso(self._reloj())
        try:
            self._uow.confirmar()
        except ConflictoConcurrenciaError as exc:
            # Dos escaneos simultáneos del mismo QR: solo el primero gana.
            raise EntradaYaUtilizadaError() from exc

        return ResultadoAcceso(
            mensaje=self.MENSAJE_ACCESO_PERMITIDO,
            entrada_id=entrada.id,
            hora_ingreso=entrada.hora_ingreso,
        )

