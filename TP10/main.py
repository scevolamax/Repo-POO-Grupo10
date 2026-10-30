from empleado_service import EmpleadoService
from empleados import Empleado
from excepciones import (
    CollectionVaciaException,
    EnteroPositivoException,
    NoEncontradoException,
    StringException,
)

# Parte D: Script principal para probar el manejo de excepciones con bloques try-except independientes.
if __name__ == "__main__":
    # Caso 1: Intentar calcular el promedio cuando la lista de empleados está vacía.
    try:
        EmpleadoService.sueldo_promedio()
    except CollectionVaciaException as e:
        print(f"CollectionVaciaException capturada: {e}")

    # Caso 2: Intentar instanciar un empleado con un sueldo inválido (negativo).
    try:
        Empleado("Juan", -500)
    except EnteroPositivoException as e:
        print(f"EnteroPositivoException capturada: {e}")

    # Caso 3: Intentar instanciar un empleado con un nombre inválido (menos de 3 caracteres).
    try:
        Empleado("Al", 1000)
    except StringException as e:
        print(f"StringException capturada: {e}")

    # Caso 4: Agregar empleados válidos e intentar eliminar uno que no existe en la lista.
    try:
        EmpleadoService.agregar(Empleado("Ana", 1500))
        EmpleadoService.agregar(Empleado("Luis", 2000))
        EmpleadoService.eliminar("Carlos")
    except NoEncontradoException as e:
        print(f"NoEncontradoException capturada: {e}")
