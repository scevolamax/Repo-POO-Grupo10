########### Solucion al problema de diseño con Bridge ################

from abc import ABC, abstractmethod

# 1. LADO DE LA IMPLEMENTACIÓN (Canales de envío)
class CanalEnvio(ABC):
    """Interfaz del Implementador: define las operaciones de bajo nivel."""

    @abstractmethod
    def enviar_mensaje(self, cuerpo: str):
        pass


class Email(CanalEnvio):
    def enviar_mensaje(self, cuerpo: str):
        print(f"[EMAIL] Conectando a servidor SMTP... Enviando: {cuerpo}")

class SMS(CanalEnvio):
    def enviar_mensaje(self, cuerpo: str):
        print(f"[SMS] Conectando a Gateway GSM... Enviando: {cuerpo}")

class WhatsApp(CanalEnvio):
    def enviar_mensaje(self, cuerpo: str):
        print(f"[WHATSAPP] Conectando a API de Meta... Enviando: {cuerpo}")


# 2. LADO DE LA ABSTRACCIÓN (Lógica de negocio/ Tipos de Notificación)

class Notificacion(ABC):
    """Abstracción Base: contiene la referencia (el Puente) hacia el Implementador."""

    def __init__(self, canal: CanalEnvio):
        self._canal = canal  # EL PUENTE (Composición/Asociación)

    @abstractmethod
    def enviar(self, contenido: str):
        pass

class NotificacionUrgente(Notificacion):
    def enviar(self, contenido: str):
        mensaje_formateado = f" [ATENCIÓN URGENTE]: {contenido}"
        # Delega hacia el implementador a través del puente
        self._canal.enviar_mensaje(mensaje_formateado)


class NotificacionPromocional(Notificacion):
    def enviar(self, contenido: str):
        mensaje_formateado = f" ¡OFERTA ESPECIAL!: {contenido} "
        # Delega hacia el implementador a través del puente
        self._canal.enviar_mensaje(mensaje_formateado)


# =====================================================================
# 3. EJEMPLO DE USO DEL CLIENTE
if __name__ == "__main__":
    # Instanciamos las implementaciones concretas
    canal_email = Email()
    canal_sms = SMS()


    # 1. Enviamos una alerta urgente por Email
    alerta = NotificacionUrgente(canal_email)
    alerta.enviar("Servidor fuera de línea")

    # 2. Las pasamos a las abstracciones deseadas (Composición)
    alerta_sistema = NotificacionUrgente(canal_email)
    campana_marketing = NotificacionPromocional(canal_SMS)

    # 3. Ejecutamos
    alerta_sistema.enviar("Servidor de base de datos caído.")
    campana_marketing.enviar("50% de descuento en todos los cursos.")


# Diferencias clave respecto a la versión sin Bridge:Cero código duplicado: 
#     La lógica de conexión SMTP o la API de WhatsApp está encapsulada en una única clase (EmailCanal, WhatsAppCanal).
#     Reducción de clases: En lugar de 6 clases combinadas rígidas, ahora tenemos 5 clases (2 notificaciones + 3 canales). Si agregamos un canal nuevo (Push), solo creamos 1 clase (PushCanal).
#     Intercambio dinámico: Gracias al método set_canal(), el cliente puede cambiar el medio de transporte en tiempo de ejecución sin cambiar el tipo de mensaje
