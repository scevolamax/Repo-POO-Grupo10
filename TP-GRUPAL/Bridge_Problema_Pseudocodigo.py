# Clase Base
class Notificacion:
    def enviar(self, mensaje):
        pass

# Primer nivel de herencia (Tipos de Mensaje) 
class NotificacionUrgente(Notificacion):
    pass

class NotificacionPromocional(Notificacion):
    pass

# Segundo nivel de herencia (Explosión de clases combinando Tipo + Canal) 
### Implementaciones para Notificación Urgente ###
class NotificacionUrgenteEmail(NotificacionUrgente):
    def enviar(self, mensaje):
        print(f"[URGENTE] Enviando por Email: {mensaje}")

class NotificacionUrgenteSMS(NotificacionUrgente):
    def enviar(self, mensaje):
        print(f"[URGENTE] Enviando por SMS: {mensaje}")

class NotificacionUrgenteWhatsApp(NotificacionUrgente):
    def enviar(self, mensaje):
        print(f"[URGENTE] Enviando por WhatsApp: {mensaje}")


### Implementaciones para Notificación Promocional ###
class NotificacionPromocionalEmail(NotificacionPromocional):
    def enviar(self, mensaje):
        print(f"[PROMOCIÓN] Enviando por Email: {mensaje}")

class NotificacionPromocionalSMS(NotificacionPromocional):
    def enviar(self, mensaje):
        print(f"[PROMOCIÓN] Enviando por SMS: {mensaje}")

class NotificacionPromocionalWhatsApp(NotificacionPromocional):
    def enviar(self, mensaje):
        print(f"[PROMOCIÓN] Enviando por WhatsApp: {mensaje}")
      
