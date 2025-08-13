import pandas as pd
import streamlit as st
from scheduler import asignar_turnos_con_descanso as asignar_turnos
from extras import (
    registrar_horas_extra,
    generar_pdf_horas_extra,
    enviar_correo_horas_extra_agrupado,
    registrar_dia_familia,
    generar_pdf_dia_familia,
    enviar_correo_dia_familia_agrupado,
    generar_pdf_permiso,
    enviar_correo_permiso,
    cargar_registros,
    enviar_correo_vacaciones
)
from datetime import datetime, timedelta
from io import BytesIO
from empleados import EMPLEADOS_POR_AREA
from email_utils import enviar_correo_incapacidad,enviar_correo_vacaciones
from correos import CORREOS_JEFES
import streamlit as st
import yagmail

EMAIL = st.secrets["EMAIL_REMITENTE"]
EMAIL_PASSWORD = st.secrets["EMAIL_P"]

yag = yagmail.SMTP(EMAIL, EMAIL_PASSWORD)

# Constantes para archivos
ARCHIVO_DIA_FAMILIA = "dia_familia.json"
# Función para obtener los días de la semana
def obtener_dia(fecha):
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    return dias[pd.to_datetime(fecha).weekday()]
# Función para generar el archivo Excel para descarga
def generar_excel_descarga(df, sheet_name):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()
# Función principal de la aplicación
#titulo de la aplicación
def main():
    st.set_page_config(page_title="Sistema de Turnos", layout="wide")
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image("logo.png", width=200)
    with col2:
        st.markdown("""
        <style>
            body {
                background-color: #e6f0ff !important;
            }
            .stApp {
                background-color: #f4f9ff !important;
            }
        </style>
        <div style='text-align: center; padding: 20px 10px; font-family: Arial, Helvetica, sans-serif;'>
            <h1 style='color:#19277F; margin-bottom: 10px;'>MUELLES Y FRENOS SIMON BOLIVAR<br>Solicitudes</h1>
        </div>""", unsafe_allow_html=True)

    st.markdown("<hr style='border: none; height: 4px; background-color: #fab70e;'>", unsafe_allow_html=True)
# Crear pestañas para las diferentes funcionalidades
    tabs = st.tabs(["Día de la Familia", "Permisos", "Incapacidades", "Vacaciones"])
   
#Día de la Familia
    with tabs[0]:
        #titulo de la pestaña
        st.markdown("<h3 style='color: #19277F;'>Solicitar Día de la Familia 🏠</h3>", unsafe_allow_html=True)       
        num2 = st.number_input("¿Cuántos empleados solicitan el día de la familia?", 1, 20, 1)
        filas = []
        for i in range(num2):
            st.markdown(f"**Empleado #{i+1}**")
            cols = st.columns(5)
            #Campos para ingresar datos del empleado
            with cols[0]: nombre = st.text_input("Empleado", key=f"df_nombre_{i}")
            with cols[1]: fecha = st.date_input("Fecha solicitada", key=f"df_fecha_{i}")
            with cols[2]: area_df = st.selectbox("Área de trabajo", ["Logistica","Compras","Ventas","Marketing","Mensajeria","Juridica","Gestion Humana","SST","TI"], key=f"df_area_{i}")
            with cols[3]: correo_em = st.text_input("Correo del empleado", key=f"df_correo_{i}")
            with cols[4]: correo_jefe = st.text_input("Correo del jefe directo", value=CORREOS_JEFES.get(area_df, ""), key=f"df_jefe_{i}")
            filas.append((nombre, fecha, area_df))
        #Botón para registrar y enviar el día de la familia
        if st.button("Registrar y enviar dia de la familia"):
            registros = []
            historial = cargar_registros(ARCHIVO_DIA_FAMILIA)  
            empleados_alerta = []
            for nombre, fecha, area_df in filas:
                if not nombre:
                    st.error("Completa todos los campos.")
                    break
                #Cuántas veces está el empleado en el historial
                veces = sum(1 for r in historial if r["empleado"].strip().lower() == nombre.strip().lower())
                if veces >= 2:
                    empleados_alerta.append(nombre)
                registro = registrar_dia_familia(nombre, fecha, area_df, ARCHIVO_DIA_FAMILIA, correo_em, correo_jefe)
                registros.append(registro)
            else:
                if empleados_alerta:
                # Mostrar alerta si algún empleado ha solicitado más de dos veces
                    st.warning(f"Atención: Los siguientes empleados ya han solicitado el Día de la Familia más de dos veces: {', '.join(empleados_alerta)}")
                if registros:
                    pdf = generar_pdf_dia_familia(registros)
                    st.download_button(
                        "Descargar PDF Día de la Familia",
                        pdf,
                        file_name="dia_familia_solicitud.pdf",
                        mime="application/pdf"
                    )
                    # Enviar correo con los registros del día de la familia
                    enviar_correo_dia_familia_agrupado(registros)
                    st.success("Día de la Familia registrado y correo enviado.")
#Permisos   
    with tabs[1]:
        #titulo de la pestaña
        st.markdown("<h3 style='color: #19277F;'>Registrar Permiso 📆</h3>", unsafe_allow_html=True)        
        #Campo para registrar tipo permisos
        tipo_permiso = st.selectbox("Tipo de Permiso", ["Seleccione un tipo","Cita medica","Medio dia", "Dia completo","Diligencia personal","Permiso especial"])
        #Campos para ingresar datos del permiso
        if tipo_permiso == "Permiso especial":
            # campo para escribir el motivo del permiso especial
            motivo_permiso = st.text_area("Motivo del Permiso Especial", key="pe_motivo")
            if not motivo_permiso:
                st.warning("Por favor, escribe el motivo del permiso especial.")
        nombre = st.text_input("Nombre empleado", key="pe_nombre")
        correo_em = st.text_input("Correo del empleado", key="e_correo")
        fecha = st.date_input("Fecha del Permiso", key="pe_fecha")
        # Campo para seleccionar área de trabajo
        area_pe = st.selectbox(
            "Área de trabajo",
            ["Seleccione un área"] + list(CORREOS_JEFES.keys()),  # Mostrar las áreas disponibles
            key="pe_area"
        )
        # Al seleccionar un área, el campo de correo del jefe se actualiza automáticamente
        if area_pe != "Seleccione un área":
            correo_jefe = CORREOS_JEFES[area_pe]
        else:
            correo_jefe = ""  # Si no se selecciona área, dejar vacío
        # Campo de correo del jefe 
        correo_jefe_input = st.text_input("Correo del jefe directo", value=correo_jefe, key="pe_correo")
        #Botón para registrar y enviar el permiso
        if st.button("Registrar y enviar permiso"):
            if not nombre or not fecha or not area_pe or tipo_permiso == "Seleccione un tipo" or not correo_jefe:
                # Mostrar mensaje de error si falta información
                st.error("Completa todos los campos para registrar el permiso.")
            else:
                registro = {"nombre": nombre, "fecha": fecha, "area": area_pe, "tipo": tipo_permiso, "correo":correo_em, "correo_jefe": correo_jefe}
                #generar pdf registo del permiso
                pdf = generar_pdf_permiso(registro)
                st.download_button(
                    "Descargar PDF Permiso",
                    pdf,
                    file_name="permiso_.pdf",
                    mime="application/pdf"
                ) 
                #enviar correo con el registro del permiso
                enviar_correo_permiso(registro)
                # Mostrar mensaje de éxito
                st.success("Permiso registrado y notificacion enviada correctamente.")
#Incapacidades
    with tabs[2]:
        st.markdown("<h3 style='color: #19277F;'>Registrar Incapacidad 🏥</h3>", unsafe_allow_html=True)       
        nombre= st.text_input("Nombre empleado", key="in_nombre")
        fecha = st.date_input("Fecha de registro de la incapacidad", key="in_fecha")          
        area_pe = st.selectbox("Área de trabajo", ["Logistica","Compras","Ventas","Marketing","Mensajeria","Juridica","Gestion Humana","SST","TI"], key="in_area")             
        st.subheader("Adjuntar documento")
        archivo = st.file_uploader("Selecciona un archivo", type=["pdf", "jpg", "jpeg", "png", "docx", "xlsx"])        
        # Definir el correo del destinatario
        destinatario = "sebastianvibr@gmail.com"          
        if archivo is not None:
            # Muestra el nombre del archivo cargado
            st.write(f"Archivo cargado: {archivo.name}")            
            # Botón para enviar el correo
            if st.button("Enviar por correo"):
                # Enviar el archivo por correo
                if not nombre or not fecha or not area_pe:
                    st.error("Completa todos los campos antes de enviar la incapacidad.")
                else:
                    registro = {
                        "nombre": nombre,
                        "fecha": fecha,
                        "area": area_pe,
                        "archivo": archivo.name
                    }
                    # Llamar a la función para enviar el correo con el archivo adjunto
                    enviar_correo_incapacidad(archivo, destinatario, nombre, fecha, area_pe)
                    st.success("Incapacidad enviada correctamente.")
# Vacaciones
    with tabs[3]:
        st.markdown("<h3 style='color: #19277F;'>Solicitar Vacaciones ☀️🌴</h3>", unsafe_allow_html=True)
        # Calculo de vacaciones
        st.markdown("<hr style='border: none; height: 4px; background-color: #fab70e;'>", unsafe_allow_html=True)
        st.markdown("""
        <p style='color: #19277F;'>
        Para calcular las vacaciones, se considera que cada empleado tiene derecho a 15 días hábiles de vacaciones al año,
        lo que equivale a 3 semanas laborales. Si el empleado ha trabajado menos de un año, se calcula proporcionalmente.
        </p>
        """, unsafe_allow_html=True)

        # Entrada de fecha de ingreso a la empresa
        fecha_ingreso = st.date_input("Fecha de ingreso a la empresa", key="vac_ingreso")
        
        # Calcular el tiempo trabajado solo si se ha seleccionado una fecha
        if fecha_ingreso:
            tiempo_trabajado = (datetime.now().date() - fecha_ingreso).days
            semanas_trabajadas = tiempo_trabajado // 7
            vacaciones_proporcionales = (tiempo_trabajado / 365) * 15  # Calcular vacaciones proporcionales
            # Mostrar el tiempo trabajado y los días de vacaciones disponibles
            st.write(f"Tiempo trabajado: {tiempo_trabajado} días ({semanas_trabajadas} semanas)")
            st.write(f"Días de vacaciones disponibles: {vacaciones_proporcionales:.2f} días hábiles")
            # Si el trabajador ha trabajado un año completo, se asegura de no pasar los 15 días de vacaciones
            dias_vacaciones = min(vacaciones_proporcionales, 15)
            st.write(f"Días de vacaciones (ajustados a máximo anual): {dias_vacaciones:.2f} días hábiles")

        st.markdown("<hr style='border: none; height: 4px; background-color: #fab70e;'>", unsafe_allow_html=True)
        
        # Nombre del empleado
        nombre = st.text_input("Nombre empleado", key="vac_nombre")
        # Área de trabajo
        area_vac = st.selectbox(
            "Área de trabajo",
            ["Seleccione un área"] + list(CORREOS_JEFES.keys()),  # Mostrar las áreas disponibles
            key="area_vac"
        )
        # Al seleccionar un área, el campo de correo del jefe se actualiza automáticamente
        if area_vac != "Seleccione un área":
            correo_jefe = CORREOS_JEFES[area_vac]
        else:
            correo_jefe = ""

        # Correo del empleado
        correo_em = st.text_input("Correo del empleado", key="vac_correo")  

        # Fecha de inicio de las vacaciones
        fecha_inicio = st.date_input("Fecha de inicio de las vacaciones", key="vac_inicio")

        # Fecha de fin de las vacaciones
        fecha_fin = st.date_input("Fecha de fin de las vacaciones", key="vac_fin")

        # Correo del jefe directo
        correo_jefe_input = st.text_input("Correo del jefe directo", value=correo_jefe, key="vac_jefe")

        # Firma del empleado
        firma = st.file_uploader("Adjuntar firma del empleado", type=["png", "jpg", "jpeg"], key="vac_firma")

        if st.button("Solicitar Vacaciones"):
            if not nombre or not fecha_inicio or not fecha_fin or not area_vac or not correo_jefe_input:
                st.error("Completa todos los campos antes de registrar las vacaciones.")
            else:
                # Verificar si se ha seleccionado un área válida y asignar el correo del jefe
                correo_jefe_input = CORREOS_JEFES.get(area_vac, '')  # Utiliza el correo del jefe de acuerdo al área

                if not correo_jefe_input:
                    st.error("No se pudo encontrar el correo del jefe para el área seleccionada.")
                else:
                    # Construir el registro con la información del empleado
                    registro = {
                        "nombre": nombre,
                        "fecha_inicio": fecha_inicio,
                        "fecha_fin": fecha_fin,
                        "area": area_vac,
                        "correo_jefe": correo_jefe_input,  # Asegúrate de pasar el correo del jefe
                        "correo_em": correo_em,  # Correo del empleado
                    }

                    # Llamar a la función para enviar el correo
                    enviar_correo_vacaciones(archivo, correo_jefe, nombre, fecha_inicio, fecha_fin, area_pe)
                
                    # Mostrar mensaje de éxito
                    st.success(f"Vacaciones solicitadas para {nombre} desde {fecha_inicio} hasta {fecha_fin}.")


if __name__ == "__main__":
    main()
# Línea decorativa
    st.markdown("<hr style='border: none; height: 4px; background-color: #fab70e;'>", unsafe_allow_html=True)
    st.markdown("""
        <div style="text-align: center; margin-top: 20px; color: #19277f;">
            <p>© 2025 Muelles y Frenos Simón Bolívar. Todos los derechos reservados.</p>
        </div>
     """, unsafe_allow_html=True)
    


                      






