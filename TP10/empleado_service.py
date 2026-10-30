from empleados import Empleado
from excepciones import CollectionVaciaException, NoEncontradoException

# Parte C: Clase EmpleadoService con validaciones de estado y negocio.


class EmpleadoService:
    empleados = []
    proximo_legajo = 1

    @classmethod
    def agregar(cls, empleado: Empleado) -> bool:
        # No se captura EnteroPositivoException para que se propague al llamador si el legajo es inválido.
        empleado.set_legajo(cls.proximo_legajo)
        cls.proximo_legajo += 1
        cls.empleados.append(empleado)
        return True

    @classmethod
    def mayor_sueldo(cls) -> Empleado:
        # Guardia: verifica que la lista no esté vacía antes de buscar el máximo.
        if not cls.empleados:
            raise CollectionVaciaException("No hay empleados.")
        return max(cls.empleados, key=lambda e: e.sueldo)

    @classmethod
    def sueldo_promedio(cls) -> float:
        # Guardia: evita dividir por cero y operar sobre una colección vacía.
        if not cls.empleados:
            raise CollectionVaciaException("No hay empleados.")
        return sum(e.sueldo for e in cls.empleados) / len(cls.empleados)

    @classmethod
    def eliminar(cls, nombre: str):
        # 1. Verifica primero si la colección está vacía.
        if not cls.empleados:
            raise CollectionVaciaException("No hay empleados.")
        # 2. Verifica si existe al menos un empleado con el nombre indicado.
        if not any(e.nombre == nombre for e in cls.empleados):
            raise NoEncontradoException("No se encontro el empleado.")
        # 3. Conserva únicamente los empleados cuyo nombre sea distinto al eliminado.
        cls.empleados = [e for e in cls.empleados if e.nombre != nombre]
