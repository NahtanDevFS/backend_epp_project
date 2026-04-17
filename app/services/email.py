import smtplib
from email.message import EmailMessage
import os

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USER = os.getenv("SMTP_USER", "jonathan007franco@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "llmahbsguklrdcwj")

def send_alert_email(destinatario: str, camera_location: str, missing_helmet: bool, missing_vest: bool):
    try:
        msg = EmailMessage()
        msg['Subject'] = f'ALERTA DE SEGURIDAD - {camera_location}'
        msg['From'] = SMTP_USER
        msg['To'] = destinatario

        faltas = []
        if missing_helmet: faltas.append("Casco")
        if missing_vest: faltas.append("Chaleco Reflectante")
        faltas_str = ", ".join(faltas)

        contenido = f"""
        Estimado Supervisor,

        El sistema Vision Guard ha detectado una infracción de seguridad crítica.

        Detalles de la alerta:
        - Ubicación: {camera_location}
        - Equipo faltante: {faltas_str}

        Por favor, revise el panel de administración (Historial de Alertas) inmediatamente para ver la evidencia fotográfica y tomar las medidas correspondientes.

        Atentamente,
        Sistema Automatizado Vision Guard
        """

        msg.set_content(contenido)

        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"Correo de alerta enviado exitosamente a {destinatario}")

    except Exception as e:
        print(f"Error al enviar correo: {e}")