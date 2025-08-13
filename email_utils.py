
import yagmail
import os
from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()

EMAIL = os.getenv("EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# enviar correos electrónicos de notificación horas extra
def enviar_correo_extra(nombre_empleado, fecha, horas, email_jefe):
    yag = yagmail.SMTP(EMAIL, EMAIL_PASSWORD)
    asunto = f"Horas extra - {nombre_empleado}"
    cuerpo = f"""<h3>Registro de horas extra</h3>
    <p>Empleado: <b>{nombre_empleado}</b><br>
    Fecha: <b>{fecha}</b><br>
    Horas: <b>{horas}</b></p>"""
    yag.send(to=email_jefe, subject=asunto, contents=cuerpo)

# enviar correos electrónicos de notificación de día de la familia
def enviar_correo_familia(nombre_empleado, fecha, email_jefe):
    yag = yagmail.SMTP(EMAIL, EMAIL_PASSWORD)
    asunto = f"Día de la Familia - {nombre_empleado}"
    cuerpo = f"""<h3>Solicitud de Día de la Familia</h3>
    <p>Empleado: <b>{nombre_empleado}</b><br>
    Fecha: <b>{fecha}</b></p>"""
    yag.send(to=email_jefe, subject=asunto, contents=cuerpo)

def enviar_correo_incapacidad(archivo, destinatario, nombre, fecha, area_pe):
    yag = yagmail.SMTP(EMAIL, EMAIL_PASSWORD)
    asunto = f"Incapacidad - {nombre}"
    cuerpo = f"""<h3>Incapacidad registrada</h3>
    <p>Empleado: <b>{nombre}</b><br>
    Fecha: <b>{fecha}</b><br>
    Área Personal: <b>{area_pe}</b></p>"""
    
    if archivo:
        yag.send(to=destinatario, subject=asunto, contents=[cuerpo, archivo])
    else:

        yag.send(to=destinatario, subject=asunto, contents=cuerpo)

def enviar_correo_vacaciones(archivo, correo_jefe, nombre, fecha_inicio, fecha_fin, area_pe):
    import yagmail

    yag = yagmail.SMTP(EMAIL, EMAIL_PASSWORD)

    # Asunto del correo
    asunto = f"Solicitud de Vacaciones - {nombre}"
 # Cuerpo del correo mejorado con HTML
    cuerpo = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h3 style="color: #0056b3;">Solicitud de Vacaciones</h3>
            <p style="font-size: 16px;">
                Estimado(a) 
                El empleado <b>{nombre}</b> ha solicitado sus vacaciones con la siguiente información:<br><br>
                 <b>Fecha de inicio:</b> {fecha_inicio}<br>
                <b>Fecha de fin:</b> {fecha_fin}<br>
                <b>Área de trabajo:</b> {area_pe}<br><br>
            
                <p>Por favor, confirma la aprobación de las vacaciones o proporciona cualquier comentario o requerimiento adicional.</p>
                <hr style="border: 1px solid #ccc;"/>
                <p style="font-size: 14px;">
                    Quedamos atentos a cualquier comentario o requerimiento adicional.<br><br>
                    Atentamente,<br>
                    <i>Área de TI</i>
                </p>
            </p>
        </body>
    </html>
    """

    #Lista de destinatarios
    destinatarios = [
        correo_jefe,
        "tic3@repuestossimonbolivar.com"  # Correo adicional si es necesario
    ]

    # Eliminar duplicados si hay
    destinatarios = list(set(destinatarios))

    # Enviar correo
    if archivo:
        yag.send(to=destinatarios, subject=asunto, contents=[cuerpo, archivo])
    else:
        yag.send(to=destinatarios, subject=asunto, contents=cuerpo)



