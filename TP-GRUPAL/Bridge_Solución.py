########### Solucion al problema de diseño con Bridge ################

from abc import ABC, abstractmethod

# 1. LADO DE LA IMPLEMENTACIÓN (Canales técnicos)
class CanalEnvio(ABC):
    """Interfaz del Implementador: define las operaciones de bajo nivel."""

    @abstractmethod
    def enviar_mensaje(self, cuerpo: str):
        pass


class EmailCanal(CanalEnvio):
    def enviar_mensaje(self, cuerpo: str):
        print(f"[EMAIL] Conectando a servidor SMTP... Enviando: {cuerpo}")


class SMSCanal(CanalEnvio):
    def enviar_mensaje(self, cuerpo: str):
        print(f"[SMS] Conectando a Gateway GSM... Enviando: {cuerpo}")


class WhatsAppCanal(CanalEnvio):
    def enviar_mensaje(self, cuerpo: str):
        print(f"[WHATSAPP] Conectando a API de Meta... Enviando: {cuerpo}")


# 2. LADO DE LA ABSTRACCIÓN (Lógica de negocio)

class Notificacion(ABC):
    """Abstracción Base: contiene la referencia (el Puente) hacia el Implementador."""

    def __init__(self, canal: CanalEnvio):
        self._canal = canal  # EL PUENTE (Composición/Asociación)

    def set_canal(self, canal: CanalEnvio):
        """Permite cambiar el canal dinámicamente en tiempo de ejecución."""
        self._canal = canal

    @abstractmethod
    def enviar(self, contenido: str):
        pass


class NotificacionUrgente(Notificacion):
    """Abstracción Refinada A"""

    def enviar(self, contenido: str):
        mensaje_formateado = f" [ATENCIÓN URGENTE]: {contenido}"
        # Delegación hacia el implementador a través del puente
        self._canal.enviar_mensaje(mensaje_formateado)


class NotificacionPromocional(Notificacion):
    """Abstracción Refinada B"""

    def enviar(self, contenido: str):
        mensaje_formateado = f" ¡OFERTA ESPECIAL!: {contenido} "
        # Delegación hacia el implementador a través del puente
        self._canal.enviar_mensaje(mensaje_formateado)


# =====================================================================
# 3. USO POR PARTE DEL CLIENTE
if __name__ == "__main__":
    # Instanciamos los canales independientes
    canal_email = EmailCanal()
    canal_sms = SMSCanal()
    canal_wsp = WhatsAppCanal()

    # 1. Enviamos una alerta urgente por Email
    alerta = NotificacionUrgente(canal_email)
    alerta.enviar("Servidor fuera de línea")

    # 2. ¡Cambiamos dinámicamente el canal a WhatsApp sin recrear la notificación!
    alerta.set_canal(canal_wsp)
    alerta.enviar("Servidor fuera de línea (Reintento urgente)")

    # 3. Enviamos una promoción por SMS
    promo = NotificacionPromocional(canal_sms)
    promo.enviar("50% de descuento en tu suscripción")


# Diferencias clave respecto a la versión sin Bridge:Cero código duplicado: 
#     La lógica de conexión SMTP o la API de WhatsApp está encapsulada en una única clase (EmailCanal, WhatsAppCanal).
#     Reducción de clases: En lugar de 6 clases combinadas rígidas, ahora tenemos 5 clases (2 notificaciones + 3 canales). Si agregamos un canal nuevo (Push), solo creamos 1 clase (PushCanal).
#     Intercambio dinámico: Gracias al método set_canal(), el cliente puede cambiar el medio de transporte en tiempo de ejecución sin cambiar el tipo de mensaje
