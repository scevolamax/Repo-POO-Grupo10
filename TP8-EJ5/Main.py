from datetime import date

from Factura import Factura
from ImpresorFacturaConsola import ImpresorFacturaConsola
from LineaFactura import LineaFactura
from Producto import Producto

if __name__ == "__main__":
    leche      = Producto("Leche Entera", 1000.0, 0.0)       # Exento
    carne      = Producto("Asado Vacuno", 6000.0, 0.105)     # 10.5%
    detergente = Producto("Lavavajillas",  2000.0, 0.21)      # 21%

    #### Registro de precios históricos ###

    # Leche: tres períodos de precio
    leche.agregar_precio(800.0,  date(2024, 1,  1), date(2024, 6, 30))
    leche.agregar_precio(900.0,  date(2024, 7,  1), date(2024, 12, 31))
    leche.agregar_precio(1000.0, date(2025, 1,  1))   # Precio abierto (sin vencimiento)

    # Carne: dos períodos de precio
    carne.agregar_precio(5000.0, date(2024, 1,  1), date(2024, 12, 31))
    carne.agregar_precio(6000.0, date(2025, 1,  1))   # Precio abierto

    # Detergente: dos períodos de precio
    detergente.agregar_precio(1500.0, date(2024, 1,  1), date(2024, 12, 31))
    detergente.agregar_precio(2000.0, date(2025, 1,  1))   # Precio abierto


    print("=" * 60)
    print("         CONSULTA DE PRECIOS HISTÓRICOS")
    print("=" * 60)

    fechas_consulta = [
        date(2024, 3, 15),   # En el primer período
        date(2024, 9,  1),   # En el segundo período (leche) / único (carne y detergente)
        date(2025, 6, 20),   # Precio actual (abierto)
    ]

    for producto in [leche, carne, detergente]:
        print(f"\n  Producto: {producto.nombre}")
        print(f"  {'Fecha':<15} {'Precio vigente':>15}")
        print(f"  {'-'*30}")
        for f in fechas_consulta:
            try:
                precio = producto.obtener_precio_en(f)
                print(f"  {str(f):<15} ${precio:>12.2f}")
            except ValueError as e:
                print(f"  {str(f):<15}  Sin precio: {e}")

    print()
    print("  Historial completo de Leche Entera:")
    for entrada in leche.historial_precios:
        print(f"    {entrada}")

    print()

    #### Carrito de compras. LineaFactura captura el precio_base vigente HOY al momento de crear la línea ####
    lineas = [
        LineaFactura(2, leche),       # Neto Base: $2000 (precio actual)
        LineaFactura(1, carne),       # Neto Base: $6000
        LineaFactura(1, detergente),  # Neto Base: $2000
    ]
    factura_b = Factura("B", 0.15, lineas)

    impresor = ImpresorFacturaConsola()
    impresor.imprimir(factura_b)

