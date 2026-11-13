"""CRUDs básicos y regla de creación de eventos (pre-generación de entradas)."""


def test_crud_lugar(client):
    creado = client.post("/lugares", json={"nombre": "Teatro Colon", "direccion": "Cerrito 628"})
    assert creado.status_code == 201
    lugar_id = creado.json()["id"]

    assert client.get(f"/lugares/{lugar_id}").json()["nombre"] == "Teatro Colon"
    assert len(client.get("/lugares").json()) == 1

    modificado = client.put(f"/lugares/{lugar_id}", json={"nombre": "Teatro Colón", "direccion": "Cerrito 628"})
    assert modificado.json()["nombre"] == "Teatro Colón"

    assert client.delete(f"/lugares/{lugar_id}").status_code == 204
    assert client.get(f"/lugares/{lugar_id}").status_code == 404


def test_crud_sector_y_nombre_duplicado(client):
    lugar_id = client.post("/lugares", json={"nombre": "Luna Park", "direccion": "Bouchard 465"}).json()["id"]
    sector = client.post(f"/lugares/{lugar_id}/sectores", json={"nombre": "Campo", "capacidad_maxima": 100})
    assert sector.status_code == 201

    duplicado = client.post(f"/lugares/{lugar_id}/sectores", json={"nombre": "campo", "capacidad_maxima": 10})
    assert duplicado.status_code == 409

    capacidad_invalida = client.post(f"/lugares/{lugar_id}/sectores", json={"nombre": "Pullman", "capacidad_maxima": 0})
    assert capacidad_invalida.status_code == 400

    sector_id = sector.json()["id"]
    modificado = client.put(f"/sectores/{sector_id}", json={"nombre": "Campo VIP", "capacidad_maxima": 50})
    assert modificado.json()["capacidad_maxima"] == 50
    assert client.get(f"/lugares/{lugar_id}").json()["sectores"][0]["nombre"] == "Campo VIP"
    assert client.delete(f"/sectores/{sector_id}").status_code == 204


def test_crud_cliente_y_unicidad(client):
    datos = {"nombre": "Ana Perez", "email": "ana@mail.com", "dni": "30123456"}
    creado = client.post("/clientes", json=datos)
    assert creado.status_code == 201
    cliente_id = creado.json()["id"]

    assert client.post("/clientes", json={**datos, "dni": "11111111"}).status_code == 409
    assert client.post("/clientes", json={**datos, "email": "otra@mail.com"}).status_code == 409

    modificado = client.put(f"/clientes/{cliente_id}", json={**datos, "nombre": "Ana María Pérez"})
    assert modificado.json()["nombre"] == "Ana María Pérez"
    assert client.delete(f"/clientes/{cliente_id}").status_code == 204
    assert client.get(f"/clientes/{cliente_id}").status_code == 404


def test_crear_evento_genera_entradas_disponibles_segun_capacidad(client, escenario, entradas_del_evento):
    evento = client.get(f"/eventos/{escenario.evento_id}").json()
    assert evento["capacidad_total"] == 6
    assert {p["sector_nombre"]: p["precio"] for p in evento["precios"]} == {"Platea": "12000.00", "VIP": "30000.00"}

    entradas = entradas_del_evento()
    assert len(entradas) == 6
    assert all(e["estado"] == "Disponible" for e in entradas)
    assert sum(e["sector_id"] == escenario.platea_id for e in entradas) == 5
    assert sum(e["sector_id"] == escenario.vip_id for e in entradas) == 1
    assert len({e["codigo_qr"] for e in entradas}) == 6


def test_crear_evento_exige_precio_para_todos_los_sectores(client, escenario):
    respuesta = client.post(
        "/eventos",
        json={
            "nombre": "Jazz Night",
            "fecha": "2026-12-01T20:00:00",
            "lugar_id": escenario.lugar_id,
            "precios": [{"sector_id": escenario.platea_id, "precio": "5000"}],
        },
    )
    assert respuesta.status_code == 400
    assert "VIP" in respuesta.json()["detail"]


def test_crear_evento_rechaza_sector_de_otro_lugar(client, escenario):
    otro_lugar = client.post("/lugares", json={"nombre": "Club", "direccion": "Calle 1"}).json()["id"]
    sector_ajeno = client.post(f"/lugares/{otro_lugar}/sectores", json={"nombre": "Pista", "capacidad_maxima": 3})
    respuesta = client.post(
        "/eventos",
        json={
            "nombre": "Fiesta",
            "fecha": "2026-12-01T20:00:00",
            "lugar_id": escenario.lugar_id,
            "precios": [
                {"sector_id": escenario.platea_id, "precio": "1000"},
                {"sector_id": escenario.vip_id, "precio": "2000"},
                {"sector_id": sector_ajeno.json()["id"], "precio": "3000"},
            ],
        },
    )
    assert respuesta.status_code == 400
    assert "no pertenece" in respuesta.json()["detail"]


def test_no_se_modifica_ni_elimina_sector_o_lugar_con_eventos(client, escenario):
    assert client.put(f"/sectores/{escenario.platea_id}", json={"nombre": "Platea", "capacidad_maxima": 99}).status_code == 409
    assert client.delete(f"/sectores/{escenario.platea_id}").status_code == 409
    assert client.delete(f"/lugares/{escenario.lugar_id}").status_code == 409

