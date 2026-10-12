#problema de diseño basado únicamente en Herencia (Sin Bridge)
# 1\. Clase Base Abstracta 

class Notificacion: 
    def enviar(self, mensaje: str): 
        raise NotImplementedError("Subclase debe implementar 'enviar'") 
    
# 2\. Primer Nivel de Herencia: Por Tipo de Notificación 

class NotificacionUrgente(Notificacion): 
    def aplicar_formato_urgente(self, mensaje: str) -> str: 
        return f" [ATENCIÓN URGENTE]: {mensaje}" 
    
class NotificacionPromocional(Notificacion): 
    def aplicar_formato_promo(self, mensaje: str) -> str: 
        return f" ¡OFERTA ESPECIAL!: {mensaje}" 
    
    
# 3\. Segundo Nivel de Herencia: Combinación rígida con el Canal de Envío # --- Ramal de Notificaciones Urgentes --- 

class NotificacionUrgenteEmail(NotificacionUrgente): 
    def enviar(self, mensaje: str): 
        texto = self.aplicar_formato_urgente(mensaje) 
    # Lógica técnica de Email duplicada
    print(f"Conectando a servidor SMTP... Enviando Email: {texto}") 

class NotificacionUrgenteSMS(NotificacionUrgente): 
    def enviar(self, mensaje: str): 
        texto = self.aplicar_formato_urgente(mensaje)
        # Lógica técnica de SMS duplicada 
        print(f"Conectando a Gateway GSM... Enviando SMS: {texto}") 
        
        
class NotificacionUrgenteWhatsApp(NotificacionUrgente): 
    def enviar(self, mensaje: str): 
        texto = self.aplicar_formato_urgente(mensaje)  
        # Lógica técnica de WhatsApp duplicada 
        print(f"Conectando a API WhatsApp... Enviando mensaje: {texto}") 
        
        # --- Ramal de Notificaciones Promocionales --- 

class NotificacionPromocionalEmail(NotificacionPromocional): 
    def enviar(self, mensaje: str): 
        texto = self.aplicar_formato_promo(mensaje) 
        # La misma lógica de Email repetida aquí 
        print(f"Conectando a servidor SMTP... Enviando Email: {texto}") 
        
class NotificacionPromocionalSMS(NotificacionPromocional): 
    def enviar(self, mensaje: str): 
        texto = self.aplicar_formato_promo(mensaje) 
        # La misma lógica de SMS repetida aquí 
        print(f"Conectando a Gateway GSM... Enviando SMS: {texto}") 

class NotificacionPromocionalWhatsApp(NotificacionPromocional): 
    def enviar(self, mensaje: str): 
        texto = self.aplicar_formato_promo(mensaje) 
        # La misma lógica de WhatsApp repetida aquí 
        print(f"Conectando a API WhatsApp... Enviando mensaje: {texto}")

\# --- Uso por parte del Cliente --- 
if __name__ == "__main__": 
  # El cliente debe conocer la clase exacta combinada 
  alerta = NotificacionUrgenteEmail() 
  alerta.enviar("Servidor caído") 
  # Si quiere enviar la misma alerta por SMS, debe instanciar otra clase totalmente distinta 
  alerta_sms = NotificacionUrgenteSMS() 
  alerta_sms.enviar("Servidor caído")

 
