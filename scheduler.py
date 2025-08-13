import math
from datetime import datetime, timedelta
from collections import defaultdict


def get_dias_laborales(year, month):
    """Genera todos los días laborales del mes, excluyendo domingos."""
    start_date = datetime(year, month, 1)
    end_date = datetime(year + (month // 12), (month % 12) + 1, 1)
    dias = []
    while start_date < end_date:
        if start_date.weekday() != 6:  # Excluir domingos
            dias.append(start_date)
        start_date += timedelta(days=1)
    return dias


def seleccionar_turno_rotativo(lista_turnos, semana_idx):
    """Devuelve el turno correspondiente para la semana, de forma rotativa."""
    if isinstance(lista_turnos, list) and lista_turnos:
        return lista_turnos[semana_idx % len(lista_turnos)]
    return {"nombre": "SIN HORARIO", "horas": 0}


def agrupar_dias_por_semana(dias, trabajan_sabado):
    """Agrupa los días laborales por semana ISO."""
    dias_por_semana = defaultdict(list)
    for dia in dias:
        if dia.weekday() == 5 and not trabajan_sabado:
            continue  # Excluir sábados si no se trabaja
        semana = dia.isocalendar()[1]
        dias_por_semana[semana].append(dia)
    return dias_por_semana


def asignar_turnos_base(empleados, dias_por_semana, horarios_lun_jue, trabajan_sabado, horarios_sabado, horarios_viernes):
    """Asigna turnos rotativos por semana a cada grupo de empleados."""
    turnos = {empleado: [] for empleado in empleados}
    grupo_a = empleados[:math.ceil(len(empleados) / 2)]
    grupo_b = empleados[math.ceil(len(empleados) / 2):]
    total_horarios = len(horarios_lun_jue)
    semana_idx = 0

    for semana in sorted(dias_por_semana.keys()):
        idx_a = semana_idx % total_horarios
        idx_b = (semana_idx + 1) % total_horarios if total_horarios > 1 else idx_a

        turno_a = horarios_lun_jue[idx_a]
        turno_b = horarios_lun_jue[idx_b]

        for grupo, turno_base in [(grupo_a, turno_a), (grupo_b, turno_b)]:
            for empleado in grupo:
                for dia in dias_por_semana[semana]:
                    # Día específico de la semana
                    if dia.weekday() == 4:  # Viernes
                        turno_final = seleccionar_turno_rotativo(horarios_viernes, semana_idx)
                    elif dia.weekday() == 5:  # Sábado
                        if trabajan_sabado:
                            turno_final = seleccionar_turno_rotativo(horarios_sabado, semana_idx)
                        else:
                            continue
                    else:  # Lunes a Jueves
                        turno_final = turno_base

                    turnos[empleado].append({
                        "fecha": dia.strftime("%Y-%m-%d"),
                        "turno": turno_final["nombre"],
                        "horas": turno_final["horas"],
                        "fecha_obj": dia
                    })

        semana_idx += 1

    return turnos


def asignar_turnos_con_descanso(
    empleados,
    year,
    month,
    horarios_lun_jue,
    trabajan_sabado=False,
    horarios_sabado=None,
    horarios_viernes=None
):
    """
    Asigna turnos rotativos semanales para empleados.
    No asigna descansos automáticos.
    """
    dias_laborales = get_dias_laborales(year, month)
    dias_por_semana = agrupar_dias_por_semana(dias_laborales, trabajan_sabado)
    turnos = asignar_turnos_base(
        empleados,
        dias_por_semana,
        horarios_lun_jue,
        trabajan_sabado,
        horarios_sabado,
        horarios_viernes
    )
    return turnos
