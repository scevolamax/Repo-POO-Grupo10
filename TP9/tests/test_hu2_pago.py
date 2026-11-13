"""HU 2 - Procesamiento de Pago y Emisión de Entradas."""
from decimal import Decimal

import pytest

from app.exceptions import ConflictoConcurrenciaError
from app.models import Cliente, Entrada, Venta
from app.repositories import UnidadDeTrabajo


def test_esc1_pago_exitoso_y_emision(cotizar, pagar, pasarela, entradas_del_evento):
    ids = cotizar(2).json()["entradas_ids"]

    respuesta = pagar(ids)

    assert respuesta.status_code == 201, respuesta.text
    venta = respuesta.json()
    assert venta["estado"] == "Pagada"
    assert Decimal(venta["total"]) == Decimal("24000")
    assert [e["id"] for e in venta["entradas"]] == ids
    assert all(e["estado"] == "Emitida" and e["codigo_qr"] for e in venta["entradas"])
    assert pasarela.llamadas == [Decimal("24000")]
    assert {e["id"] for e in entradas_del_evento("Emitida")} == set(ids)


def test_esc2_pago_rechazado_mantiene_entradas_disponibles(client, cotizar, pagar, pasarela, entradas_del_evento):
    ids = cotizar(2).json()["entradas_ids"]
    pasarela.aprobar = False

    respuesta = pagar(ids)

    assert respuesta.status_code == 400
    assert respuesta.json()["detail"] == "Pago denegado"
    disponibles = {e["id"]: e for e in entradas_del_evento("Disponible")}
    assert all(i in disponibles and disponibles[i]["venta_id"] is None for i in ids)
    # La venta quedó registrada como Cancelada (auditoría), nunca como Pagada.
    assert client.get("/ventas/1").json()["estado"] == "Cancelada"


def test_esc2_pasarela_simulada_rechaza_tarjeta_terminada_en_0000(client, cotizar, pagar):
    from app.dependencies import get_pasarela
    from app.main import app
    from app.pasarela import PasarelaPagosSimulada

    app.dependency_overrides[get_pasarela] = PasarelaPagosSimulada
    ids = cotizar(1).json()["entradas_ids"]
    tarjeta_rechazada = {"numero": "4111111111110000", "titular": "Ana", "vencimiento": "12/28", "cvv": "123"}

    respuesta = pagar(ids, tarjeta=tarjeta_rechazada)

    assert respuesta.status_code == 400
    assert respuesta.json()["detail"] == "Pago denegado"


def test_esc3_perdida_de_disponibilidad_aborta_antes_de_la_pasarela(cotizar, pagar, pasarela, escenario):
    # Ambos clientes cotizan las mismas entradas.
    ids_cliente_a = cotizar(2).json()["entradas_ids"]
    ids_cliente_b = cotizar(2).json()["entradas_ids"]
    assert ids_cliente_a == ids_cliente_b

    # El otro usuario concreta la compra primero.
    assert pagar(ids_cliente_a, cliente_id=escenario.otro_cliente_id).status_code == 201
    llamadas_previas = len(pasarela.llamadas)

    respuesta = pagar(ids_cliente_b)

    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == "Los lugares seleccionados ya no se encuentran disponibles"
    assert len(pasarela.llamadas) == llamadas_previas  # nunca se consultó a la pasarela


def test_seleccion_de_entradas_de_otro_sector_es_rechazada(pagar, cotizar, escenario):
    ids_vip = cotizar(1, sector_id=escenario.vip_id).json()["entradas_ids"]
    respuesta = pagar(ids_vip)  # la solicitud declara sector Platea
    assert respuesta.status_code == 400


def test_bloqueo_optimista_detecta_reserva_simultanea(session_factory, escenario):
    """Dos sesiones leen la misma entrada 'Disponible' y ambas intentan reservarla."""
    sesion_a, sesion_b = session_factory(), session_factory()
    try:
        entrada_a = sesion_a.get(Entrada, 1)
        entrada_b = sesion_b.get(Entrada, 1)
        assert entrada_a.esta_disponible() and entrada_b.esta_disponible()

        entrada_a.reservar(Venta.iniciar(sesion_a.get(Cliente, escenario.cliente_id)))
        UnidadDeTrabajo(sesion_a).confirmar()

        entrada_b.reservar(Venta.iniciar(sesion_b.get(Cliente, escenario.otro_cliente_id)))
        with pytest.raises(ConflictoConcurrenciaError):
            UnidadDeTrabajo(sesion_b).confirmar()
    finally:
        sesion_a.close()
        sesion_b.close()

