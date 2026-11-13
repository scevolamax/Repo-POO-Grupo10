"""HU 3 - Control de Acceso en Puerta."""
from datetime import datetime

import pytest

from app.models import Entrada, EstadoEntrada


@pytest.fixture
def entrada_emitida(cotizar, pagar):
    ids = cotizar(1).json()["entradas_ids"]
    venta = pagar(ids).json()
    return venta["entradas"][0]


def escanear(client, codigo_qr: str):
    return client.post("/accesos/escanear-acceso", json={"codigo_qr": codigo_qr})


def test_esc1_ingreso_exitoso(client, entrada_emitida, reloj, entradas_del_evento):
    respuesta = escanear(client, entrada_emitida["codigo_qr"])

    assert respuesta.status_code == 200
    assert respuesta.json()["mensaje"] == "Acceso Permitido"
    assert datetime.fromisoformat(respuesta.json()["hora_ingreso"]) == reloj.actual
    utilizada = entradas_del_evento("Utilizada")[0]
    assert utilizada["id"] == entrada_emitida["id"]
    assert datetime.fromisoformat(utilizada["hora_ingreso"]) == reloj.actual


def test_esc2_entrada_ya_utilizada_no_sobrescribe_hora(client, entrada_emitida, reloj, entradas_del_evento):
    hora_original = reloj.actual
    assert escanear(client, entrada_emitida["codigo_qr"]).status_code == 200

    reloj.actual = datetime(2026, 11, 15, 22, 0, 0)  # intento de reingreso más tarde
    respuesta = escanear(client, entrada_emitida["codigo_qr"])

    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == "Entrada ya utilizada"
    utilizada = entradas_del_evento("Utilizada")[0]
    assert datetime.fromisoformat(utilizada["hora_ingreso"]) == hora_original


def test_esc3_qr_inexistente(client, escenario):
    respuesta = escanear(client, "qr-falso-generado-por-otro-sistema")

    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == "Ticket Inválido o Inexistente"


def test_esc4_entrada_disponible_no_emitida(client, entradas_del_evento):
    disponible = entradas_del_evento("Disponible")[0]

    respuesta = escanear(client, disponible["codigo_qr"])

    assert respuesta.status_code == 400
    assert respuesta.json()["detail"] == "Ticket no emitido / Falta de pago"
    assert len(entradas_del_evento("Utilizada")) == 0


def test_esc4_entrada_reservada_colgada(client, session_factory, entradas_del_evento):
    disponible = entradas_del_evento("Disponible")[0]
    with session_factory() as db:  # simula una venta que nunca se completó
        db.get(Entrada, disponible["id"]).estado = EstadoEntrada.RESERVADA
        db.commit()

    respuesta = escanear(client, disponible["codigo_qr"])

    assert respuesta.status_code == 400
    assert respuesta.json()["detail"] == "Ticket no emitido / Falta de pago"

