from datetime import date
from Factura import Factura
from ImpresorFacturaConsola import ImpresorFacturaConsola
from LineaFactura import LineaFactura
from Producto import Producto
from Descuento import DescuentoPromocionNxM, DescuentoPorVolumen, DescuentoPorCategoria

if __name__ == "__main__":
    # ---------------------------------------------------------------
    # 1. Catálogo de productos con historial de precios
    # ---------------------------------------------------------------
    leche = Producto("Leche Entera", 1000.0, 0.0)      # Exento
    leche.agregar_precio(900.0,  date(2025, 1, 1),  date(2025, 6, 30))
    leche.agregar_precio(1000.0, date(2025, 7, 1),  date(2025, 12, 31))
    leche.agregar_precio(1100.0, date(2026, 1, 1))   # vigente hasta hoy

    carne = Producto("Asado Vacuno", 6000.0, 0.105)   # 10.5%
    carne.agregar_precio(5500.0, date(2025, 1, 1),  date(2025, 9, 30))
    carne.agregar_precio(6000.0, date(2025, 10, 1), date(2025, 12, 31))
    carne.agregar_precio(6800.0, date(2026, 1, 1))   # vigente hasta hoy

    fernet = Producto("Fernet", 2000.0, 0.21)         # 21%
    fernet.agregar_precio(1800.0, date(2025, 1, 1),  date(2025, 12, 31))
    fernet.agregar_precio(2000.0, date(2026, 1, 1))  # vigente hasta hoy

    # ---------------------------------------------------------------
    # 2. Armado del carrito con precios actuales y descuentos
    # ---------------------------------------------------------------
    lineas = [
        LineaFactura(2, leche),  # sin promoción

        LineaFactura(3, carne, [
            DescuentoPromocionNxM(3, 2)  # Promo 3x2: paga 2 de 3
        ]),

        LineaFactura(6, fernet, [
            DescuentoPorVolumen(5, 0.10)  # 10% off llevando 5 o más
        ]),
    ]

    # ---------------------------------------------------------------
    # 3. Factura "B" con descuento global por categoría de cliente
    #    (se aplica DESPUÉS de las promociones de cada línea)
    # ---------------------------------------------------------------
    factura_b = Factura("B", lineas, [
        DescuentoPorCategoria("Jubilados", 0.15)
    ])

    # ---------------------------------------------------------------
    # 4. Invocar la Fabricación Pura para la visualización
    # ---------------------------------------------------------------
    impresor = ImpresorFacturaConsola()
    impresor.imprimir(factura_b)
