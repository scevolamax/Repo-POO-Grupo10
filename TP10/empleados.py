from excepciones import EnteroPositivoException, StringException

# Parte B: Clase Empleado refactorizada aplicando Programación Defensiva (Fail-Fast).


class Empleado:
    def __init__(self, nombre: str, sueldo: int):
        self.legajo = None
        # Se delega la asignación a los setters para reutilizar las validaciones
        # y evitar que el objeto se instancie en un estado inconsistente.
        self.set_nombre(nombre)
        self.set_sueldo(sueldo)

    def set_nombre(self, nombre: str):
        # Validación fail-fast: falla inmediatamente si el nombre es nulo o tiene menos de 3 caracteres.
        if nombre is None or len(nombre) < 3:
            raise StringException("El nombre del empleado debe tener 3 o mas caracteres.")
        self.nombre = nombre

    def set_sueldo(self, sueldo: int):
        # Validación fail-fast: el sueldo debe existir y ser estrictamente mayor a 0.
        if sueldo is None or sueldo <= 0:
            raise EnteroPositivoException("El sueldo del empleado debe ser mayor a 0.")
        self.sueldo = sueldo

    def set_legajo(self, legajo: int):
        # Validación fail-fast: el legajo debe existir y ser estrictamente mayor a 0.
        if legajo is None or legajo <= 0:
            raise EnteroPositivoException("El legajo del empleado debe ser mayor a 0.")
        self.legajo = legajo
