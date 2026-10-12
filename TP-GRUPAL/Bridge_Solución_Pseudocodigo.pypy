# --- LADO DE LA IMPLEMENTACIÓN (Canales) ---
# Solo necesitamos que cada clase tenga un método 'enviar'

class Email:
    def enviar(self, texto): print(f"Vía Email: {texto}")

class SMS:
    def enviar(self, texto): print(f"Vía SMS: {texto}")

class WhatsApp:
    def enviar(self, texto): print(f"Vía WhatsApp: {texto}")


# --- LADO DE LA ABSTRACCIÓN (Tipos) ---

class Notificacion:
    def __init__(self, canal):
        self.canal = canal # El puente de composición

class NotificacionUrgente(Notificacion):
    def enviar(self, mensaje):
        self.canal.enviar(f"[URGENTE] {mensaje}")

class NotificacionPromocional(Notificacion):
    def enviar(self, mensaje):
        self.canal.enviar(f"[PROMOCIÓN] {mensaje}")


# --- EJEMPLO DE USO ---

alerta = NotificacionUrgente(Email())
alerta.enviar("Servidor caído") 
# Salida: Vía Email: [URGENTE] Servidor caído

campana = NotificacionPromocional(WhatsApp())
campana.enviar("50% de descuento") 
# Salida: Vía WhatsApp: [PROMOCIÓN] 50% de descuento
