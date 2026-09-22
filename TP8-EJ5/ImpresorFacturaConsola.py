from Factura import Factura

class ImpresorFacturaConsola:
    def imprimir(self, factura: Factura):
        print("===============================================================")
        print("           SUPERMERCADO \"LA GRAN PROVISIÓN\"                  ")
        print(f"                     FACTURA TIPO: {factura.tipo_comprobante}")
        print("===============================================================")
        print(f"{'Producto':<15} | {'Cant':<4} | {'Neto (c/Desc)':<12} | {'Tasa IVA':<10} | {'Total':<10}")
        print("---------------------------------------------------------------")
        
        for linea in factura.lineas:
            neto_linea = linea.calcular_neto_con_descuento(factura.porcentaje_descuento)
            total_linea = linea.calcular_total_linea(factura.porcentaje_descuento)
            tasa_iva_pct = linea.porcentaje_iva_facturado * 100
            
            print(f"{linea.producto.nombre:<15} | {linea.cantidad:<4} | ${neto_linea:<11.2f} | {tasa_iva_pct:>8.1f}% | ${total_linea:<9.2f}")
        
        print("---------------------------------------------------------------")
        print(f"Total Neto Gravado:                        ${factura.calcular_total_neto():<10.2f}")
        
        print("Desglose de Impuestos:")
        print(f"  -> IVA Cobrado Alícuota 21%:             ${factura.calcular_iva_por_tasa(0.21):<10.2f}")
        print(f"  -> IVA Cobrado Alícuota 10.5%:           ${factura.calcular_iva_por_tasa(0.105):<10.2f}")
        print(f"  -> IVA Cobrado Alícuota Exento (0%):      ${factura.calcular_iva_por_tasa(0.0):<10.2f}")
        print(f"Monto Total de IVA:                        ${factura.calcular_total_iva():<10.2f}")
        
        print("---------------------------------------------------------------")
        print(f"TOTAL FINAL FACTURADO:                     ${factura.calcular_total_final():<10.2f}")
        print("===============================================================\n")
