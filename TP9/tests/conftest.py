"""Fixtures compartidas: BD en memoria y dobles de prueba para pasarela y reloj."""
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db, habilitar_foreign_keys
from app.dependencies import get_pasarela, get_reloj
from app.main import app
from app.pasarela import DatosTarjeta, PasarelaPagos, ResultadoPago

TARJETA_VALIDA = {"numero": "4111111111111111", "titular": "Ana Perez", "vencimiento": "12/28", "cvv": "123"}


class PasarelaEspia(PasarelaPagos):
    """Doble de prueba: permite forzar aprobación/rechazo y registra las llamadas."""

    def __init__(self) -> None:
        self.aprobar = True
        self.llamadas: list[Decimal] = []

    def procesar_pago(self, monto: Decimal, tarjeta: DatosTarjeta) -> ResultadoPago:
        self.llamadas.append(monto)
        if self.aprobar:
            return ResultadoPago(aprobado=True, codigo_autorizacion="TEST-OK")
        return ResultadoPago(aprobado=False, motivo="Fondos insuficientes")


class RelojFijo:
    def __init__(self) -> None:
        self.actual = datetime(2026, 11, 15, 20, 30, 15)

    def __call__(self) -> datetime:
        return self.actual


@pytest.fixture
def engine():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    habilitar_foreign_keys(eng)
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def pasarela():
    return PasarelaEspia()


@pytest.fixture
def reloj():
    return RelojFijo()


@pytest.fixture
def client(session_factory, pasarela, reloj):
    def _get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_pasarela] = lambda: pasarela
    app.dependency_overrides[get_reloj] = lambda: reloj
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def escenario(client):
    """Rock Fest en Estadio Único: Platea (5 lugares, $12.000) y VIP (1 lugar, $30.000)."""
    lugar = client.post("/lugares", json={"nombre": "Estadio Unico", "direccion": "Av. 32 y 25"})
    assert lugar.status_code == 201, lugar.text
    lugar_id = lugar.json()["id"]

    platea = client.post(f"/lugares/{lugar_id}/sectores", json={"nombre": "Platea", "capacidad_maxima": 5})
    vip = client.post(f"/lugares/{lugar_id}/sectores", json={"nombre": "VIP", "capacidad_maxima": 1})
    assert platea.status_code == 201 and vip.status_code == 201

    cliente = client.post("/clientes", json={"nombre": "Ana Perez", "email": "ana@mail.com", "dni": "30123456"})
    otro_cliente = client.post("/clientes", json={"nombre": "Luis Gomez", "email": "luis@mail.com", "dni": "28999888"})
    assert cliente.status_code == 201 and otro_cliente.status_code == 201

    evento = client.post(
        "/eventos",
        json={
            "nombre": "Rock Fest",
            "fecha": "2026-11-15T21:00:00",
            "lugar_id": lugar_id,
            "precios": [
                {"sector_id": platea.json()["id"], "precio": "12000"},
                {"sector_id": vip.json()["id"], "precio": "30000"},
            ],
        },
    )
    assert evento.status_code == 201, evento.text

    return SimpleNamespace(
        lugar_id=lugar_id,
        platea_id=platea.json()["id"],
        vip_id=vip.json()["id"],
        cliente_id=cliente.json()["id"],
        otro_cliente_id=otro_cliente.json()["id"],
        evento_id=evento.json()["id"],
    )


@pytest.fixture
def cotizar(client, escenario):
    def _cotizar(cantidad: int, sector_id: int | None = None):
        return client.post(
            "/ventas/cotizar",
            json={
                "evento_id": escenario.evento_id,
                "sector_id": sector_id or escenario.platea_id,
                "cantidad": cantidad,
            },
        )

    return _cotizar


@pytest.fixture
def pagar(client, escenario):
    def _pagar(entradas_ids: list[int], cliente_id: int | None = None, tarjeta: dict | None = None):
        return client.post(
            "/ventas/iniciar-pago",
            json={
                "cliente_id": cliente_id or escenario.cliente_id,
                "evento_id": escenario.evento_id,
                "sector_id": escenario.platea_id,
                "entradas_ids": entradas_ids,
                "tarjeta": tarjeta or TARJETA_VALIDA,
            },
        )

    return _pagar


@pytest.fixture
def entradas_del_evento(client, escenario):
    def _listar(estado: str | None = None):
        params = {"estado": estado} if estado else {}
        respuesta = client.get(f"/eventos/{escenario.evento_id}/entradas", params=params)
        assert respuesta.status_code == 200
        return respuesta.json()

    return _listar

