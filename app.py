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
from email_utils import enviar_correo_incapacidad
from correos import CORREOS_JEFES
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
            <h1 style='color:#19277F; margin-bottom: 10px;'>MUELLES Y FRENOS SIMON BOLIVAR<br>Sistema de Turnos y Registros</h1>
        </div>""", unsafe_allow_html=True)

    st.markdown("<hr style='border: none; height: 4px; background-color: #fab70e;'>", unsafe_allow_html=True)
# Crear pestañas para las diferentes funcionalidades
    tabs = st.tabs(["Turnos", "Tiempo Extra", "Día de la Familia", "Permisos", "Incapacidades", "Vacaciones"])
# Asignar turnos
    with tabs[0]:
        st.markdown("<h3 style='color: #19277F;'>Asignar Turnos ⏰</h3>", unsafe_allow_html=True)
# Selección de empleados
        area = st.selectbox("Área de trabajo", ["Seleccione un área"] + list(EMPLEADOS_POR_AREA.keys()))
        empleados_predefinidos = "\n".join(EMPLEADOS_POR_AREA.get(area, [])) if area != "Seleccione un área" else ""
        empleados_input = st.text_area("Lista de empleados (uno por línea), Puedes agregar o borrar empleados.", value=empleados_predefinidos)
        empleados = [e.strip() for e in empleados_input.split("\n") if e.strip()]
# Selección de año y mes
        col1, col2 = st.columns(2)
        with col1:
            year = st.number_input("Año", min_value=2023, max_value=2100, value=datetime.now().year)
        with col2:
            month = st.number_input("Mes", min_value=1, max_value=12, value=datetime.now().month)
# Selección de horarios
        horarios_predefinidos = [
            {"nombre": "7:00 AM - 16:00 PM", "horas": 9.0},
            {"nombre": "7:30 AM - 16:15 PM", "horas": 8.75},
            {"nombre": "7:30 AM - 17:00 PM", "horas": 9.5},
            {"nombre": "8:00 AM - 12:00 PM", "horas": 4.0},
            {"nombre": "7:30 AM - 17:15 PM", "horas": 9.75},
            {"nombre": "8:00 AM - 11:30 AM", "horas": 3.5},
            {"nombre": "8:00 AM - 13:00 PM", "horas": 5.0},
            {"nombre": "8:00 AM - 14:00 PM", "horas": 6.0},
            {"nombre": "8:00 AM - 15:00 PM", "horas": 7.0},
            {"nombre": "8:00 AM - 16:00 PM", "horas": 8.0},
            {"nombre": "8:00 AM - 16:45 PM", "horas": 8.75},
            {"nombre": "8:00 AM - 16:30 PM", "horas": 8.5},
            {"nombre": "8:00 AM - 17:00 PM", "horas": 9.0},
            {"nombre": "8:00 AM - 17:30 PM", "horas": 9.5},
            {"nombre": "8:00 AM - 18:00 PM", "horas": 10.0},
            {"nombre": "9:00 AM - 12:30 PM", "horas": 3.5},
            {"nombre": "9:00 AM - 14:00 PM", "horas": 5.0},
            {"nombre": "9:00 AM - 18:00 PM", "horas": 9.0},
            {"nombre": "9:30 AM - 18:00 PM", "horas": 8.5},
            {"nombre": "10:00 AM - 18:00 PM", "horas": 8.0}
        ]

        horarios_opciones_display = [h["nombre"] for h in horarios_predefinidos]
        horarios_mapping = {h["nombre"]: h for h in horarios_predefinidos}
# Selección de horarios de lunes a jueves
        horarios_seleccionados_nombres = st.multiselect("Selecciona los horarios de trabajo de Lunes a Jueves", horarios_opciones_display)
        horarios_lun_jue = [horarios_mapping[n] for n in horarios_seleccionados_nombres]
# Selección de horarios de viernes
        horarios_viernes_nombres = st.multiselect("Selecciona los horarios de trabajo del Viernes (pueden rotar)", horarios_opciones_display)
        horarios_viernes = [horarios_mapping[n] for n in horarios_viernes_nombres]
# Selección de si trabajan los sábados
        trabajan_sabado = st.checkbox("¿Estos empleados trabajan los sábados?")
        horarios_seleccionadossabado = []
        if trabajan_sabado:
            horarios_seleccionadossabado_nombres = st.multiselect(
                "Selecciona los horarios de trabajo para el Sábado (rotarán cada semana)",
                horarios_opciones_display,
            )
            horarios_seleccionadossabado = [horarios_mapping[nombre] for nombre in horarios_seleccionadossabado_nombres]
# Selecciona si algún empleado tiene el Día de la Familia con su fecha
        dia_familia = st.checkbox("Algún empleado tiene el Día de la Familia?")
        empleados_dia_familia_dict = {}
        if dia_familia:
            empleados_dia_familia = st.multiselect("Selecciona los empleados que tienen el Día de la Familia", empleados)
            for empleado in empleados_dia_familia:
                fecha = st.date_input(f"Fecha del Día de la Familia para {empleado}", datetime.now(), key=f"fam_{empleado}")
                empleados_dia_familia_dict[empleado] = fecha
# Selecciona si algún empleado está de vacaciones con su fecha de inicio y fin
        vacaciones = st.checkbox("¿Algún empleado está de vacaciones?")
        empleados_vacaciones_dict = {}
        if vacaciones:
            empleados_vacaciones = st.multiselect("Selecciona los empleados que están de vacaciones", empleados)
            for empleado in empleados_vacaciones:
                inicio = st.date_input(f"Inicio vacaciones de {empleado}", datetime.now(), key=f"vac_ini_{empleado}")
                fin = st.date_input(f"Fin vacaciones de {empleado}", datetime.now(), key=f"vac_fin_{empleado}")
                empleados_vacaciones_dict[empleado] = (inicio, fin)
# Selecciona si asignar días de descanso por empleado
        descansos = st.checkbox("¿Asignar uno o varios días de descanso manual por empleado?")
        empleados_descanso_dict = {}
        if descansos:
            empleados_descanso = st.multiselect("Selecciona los empleados que tendrán días de descanso específicos", empleados)
            for empleado in empleados_descanso:
                fechas_descanso = st.date_input(f"Selecciona la(s) fecha(s) de descanso para {empleado}", [], key=f"descanso_{empleado}")
                if isinstance(fechas_descanso, datetime):
                    fechas_descanso = [fechas_descanso]
                empleados_descanso_dict[empleado] = [f.strftime("%Y-%m-%d") for f in fechas_descanso]
# Botón para generar los turnos
        turnos = None
        if st.button("Generar Turnos"):
            if not empleados:
                st.error("Por favor, ingresa al menos un empleado antes de generar los turnos.")
            elif not horarios_lun_jue:
                st.error("Por favor, selecciona al menos un horario de lunes a jueves.")
            else:
                try:
                    turnos = asignar_turnos(
                        empleados,
                        year,
                        month,
                        horarios_lun_jue,
                        trabajan_sabado,
                        horarios_seleccionadossabado,
                        horarios_viernes
                    )
                except Exception as e:
                    st.error(f"Error al asignar turnos: {e}")
                    turnos = {}

                all_turnos = []
                for empleado, lista in turnos.items():
                    for t in lista:
                        fecha_str = t["fecha"]
                        fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d").date()
                        turno = t["turno"]
                        horas = t["horas"]

                        if dia_familia and empleado in empleados_dia_familia_dict:
                            if fecha_obj == empleados_dia_familia_dict[empleado]:
                                turno = "Día de la Familia"
                                horas = 0

                        if vacaciones and empleado in empleados_vacaciones_dict:
                            inicio, fin = empleados_vacaciones_dict[empleado]
                            if inicio <= fecha_obj <= fin:
                                turno = "Vacaciones"
                                horas = 0

                        if descansos and empleado in empleados_descanso_dict:
                            if fecha_str in empleados_descanso_dict[empleado]:
                                turno = "Descanso"
                                horas = 0

                        horas_ajustadas = max(horas - 0.75, 0)

                        all_turnos.append({
                            "Empleado": empleado,
                            "Fecha": fecha_str,
                            "Turno": turno,
                            "Horas Laboradas": horas_ajustadas,
                            "Almuerzo": "30 minutos",
                            "Desayuno": "15 minutos"
                        })

                df = pd.DataFrame(all_turnos)
                df["Día"] = df["Fecha"].apply(obtener_dia)
                df["Semana"] = pd.to_datetime(df["Fecha"]).dt.isocalendar().week

                resumen_semanal = df.groupby(["Empleado", "Semana"])["Horas Laboradas"].sum().reset_index()
                resumen_semanal.rename(columns={"Horas Laboradas": "Horas Semana"}, inplace=True)

                df = df.merge(resumen_semanal, on=["Empleado", "Semana"], how="left")
                st.session_state["df_turnos"] = df

        if "df_turnos" in st.session_state:
            df = st.session_state["df_turnos"]

# Crear columna de horas totales si no existe
            if "Horas Totales" not in df.columns:
                df["Horas Totales"] = df["Horas Laboradas"] - 0.75

            st.subheader("Turnos Generados")
            st.dataframe(df[[
                "Empleado", "Fecha", "Día", "Turno", "Almuerzo", "Desayuno", "Horas Laboradas", "Horas Totales"
            ]])
# Descargar turnos en Excel
            st.download_button(
                "Descargar Turnos en Excel",
                generar_excel_descarga(
                    df[[
                        "Empleado", "Fecha", "Día", "Turno", "Almuerzo", "Desayuno", "Horas Laboradas", "Horas Totales"
                    ]],
                    "Turnos"
                ),
                file_name=f"Turnos_{year}_{month}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# Horas Extra
    with tabs[1]:
        st.markdown("<h3 style='color: #19277F;'>Registrar Tiempo Extra laborado ⏱️</h3>", unsafe_allow_html=True)      

        num = st.number_input("¿Cuántos empleados trabajaron tiempo extra?", 1, 20, 1)
        campos = []

        for i in range(num):
            st.markdown(f"**Empleado #{i+1}**")
            cols = st.columns(4)

            with cols[0]:
                nombre = st.text_input("Nombre empleado", key=f"he_nombre_{i}")
            with cols[1]:
                fecha = st.date_input("Fecha", key=f"he_fecha_{i}")
            with cols[2]:
                col_h, col_m = st.columns(2)
                with col_h:
                    minutos_di = st.number_input("Minutos Diurnos", 0, 59, key=f"he_diurnas_minutos_{i}")
                with col_m:
                    horas_di = st.number_input("Horas Diurnas", 0, 12, key=f"he_diurnas_horas_{i}")
            with cols[3]:
                col_h, col_m = st.columns(2)
                with col_h:
                    minutos_no = st.number_input("Minutos Nocturnos", 0, 59, key=f"he_nocturnas_minutos_{i}")                   
                with col_m:
                    horas_no = st.number_input("Horas Nocturnas", 0, 12, key=f"he_nocturnas_horas_{i}")

            area_he = st.selectbox("Área de trabajo", 
                ["Logistica","Compras","Cartera","Marketing","Mensajeria","Juridica","Gestion Humana","SST","TI"], 
                key=f"he_area_{i}"
            )

            pago = st.selectbox(
                "Medio de pago",
                ["Seleccione un medio de pago", "Nomina", "Tiempo"],
                key=f"he_pago_{i}"
            )

            campos.append((nombre, fecha, horas_no, horas_di, minutos_di, minutos_no, area_he, pago))

        if st.button("Registrar y enviar"):
            registros = []
            for nombre, fecha, horas_no, horas_di, minutos_di, minutos_no, area_he, pago in campos:
                if not nombre or (horas_di == 0 and minutos_di == 0 and horas_no == 0 and minutos_no == 0):
                    st.error("Completa el nombre y al menos una hora o minuto extra.")
                    break

                registro = registrar_horas_extra(
                    empleado=nombre,
                    fecha=fecha,
                    horas_nocturnas=horas_no,
                    horas_diurnas=horas_di,
                    minutos_di=minutos_di,
                    minutos_no=minutos_no,
                    area=area_he,
                    pago=pago
                )
                registros.extend(registro)

            else:  # Se ejecuta solo si no hubo break
                if registros:
                    pdf = generar_pdf_horas_extra(registros)
                    st.download_button(
                        "Descargar PDF Horas Extra",
                        pdf,
                        file_name="horas_extra_.pdf",
                        mime="application/pdf"
                    )
                    enviar_correo_horas_extra_agrupado(registros)
                    st.success("Horas extra registradas y correo enviado.")                  
#Día de la Familia
    with tabs[2]:
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
    with tabs[3]:
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
    with tabs[4]:
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
    with tabs[5]:
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
                    enviar_correo_vacaciones(registro)
                    
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
    

                      