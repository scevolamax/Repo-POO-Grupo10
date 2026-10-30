# Parte A: Excepciones personalizadas del dominio.
# Todas heredan de la clase base Exception para representar errores específicos.


class StringException(Exception):
    """Se lanza cuando una cadena de texto no cumple con el formato o longitud mínima."""
    pass


class EnteroPositivoException(Exception):
    """Se lanza cuando un valor numérico requerido como positivo es nulo o menor/igual a cero."""
    pass


class CollectionVaciaException(Exception):
    """Se lanza al intentar operar sobre una colección que no contiene elementos."""
    pass


class NoEncontradoException(Exception):
    """Se lanza cuando no se encuentra un elemento buscado dentro de la colección."""
    pass
