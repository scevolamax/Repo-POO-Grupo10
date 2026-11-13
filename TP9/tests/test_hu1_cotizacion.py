"""HU 1 - Selección y Cotización."""
from decimal import Decimal

import pytest


def test_esc1_cotizacion_exitosa_con_disponibilidad(cotizar, entradas_del_evento):
    respuesta = cotizar(2)

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert Decimal(cuerpo["precio_unitario"]) == Decimal("12000")
    assert Decimal(cuerpo["subtotal"]) == Decimal("24000")
    assert Decimal(cuerpo["total"]) == Decimal("24000")
    assert len(cuerpo["entradas_ids"]) == 2
    # Cotizar no reserva: todas siguen disponibles.
    assert len(entradas_del_evento("Disponible")) == 6


def test_esc2_cotizacion_rechazada_por_falta_de_disponibilidad(cotizar, escenario):
    respuesta = cotizar(3, sector_id=escenario.vip_id)

    assert respuesta.status_code == 400
    assert respuesta.json()["detail"] == "Capacidad insuficiente o entradas no disponibles"


@pytest.mark.parametrize("cantidad", [0, -1, -10])
def test_esc3_cotizacion_rechazada_por_cantidad_invalida(cotizar, cantidad):
    respuesta = cotizar(cantidad)

    assert respuesta.status_code == 400
    assert respuesta.json()["detail"] == "La cantidad de entradas solicitadas debe ser mayor a cero"


def test_cotizacion_de_evento_o_sector_inexistente(client):
    respuesta = client.post("/ventas/cotizar", json={"evento_id": 999, "sector_id": 999, "cantidad": 1})
    assert respuesta.status_code == 404

