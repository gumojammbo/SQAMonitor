from apps.actividades.models import DIMENSIONES, Actividad, Defecto

REVISION = [("revisados", "Artefactos revisados", 90), ("defectos", "Defectos corregidos", 100),
            ("plan", "Cumplimiento del plan", 75)]
# metricas de cada dimension: (clave, nombre, umbral); flake8 no usa umbral
METRICAS = {
    "especificacion": REVISION,
    "diseno": REVISION,
    "construccion": [("cobertura", "Cobertura de pruebas", 80),
                     ("pruebas", "Pruebas aprobadas", 100),
                     ("pasan", "Artefactos revisados que pasan", 85),
                     ("flake8", "Errores de flake8", None),
                     ("plan", "Cumplimiento del plan", 75)],
    "conformidad": [("pasan", "Artefactos revisados que pasan", 85),
                    ("plan", "Cumplimiento del plan", 75)],
}
# semaforo: etiqueta, clase de bootstrap y color de fondo para el pdf
SEMAFOROS = {
    "verde": ("Aprobado", "success", (198, 239, 206)),
    "amarillo": ("En riesgo", "warning", (255, 235, 156)),
    "rojo": ("Bloqueado", "danger", (255, 199, 206)),
    "gris": ("Sin dato", "secondary", (220, 220, 220)),
}


def porcentaje(parte, total):
    return parte * 100 / total if total else None


# puntaje 0-100 de una metrica; sin valor no hay puntaje
def puntaje_metrica(clave, valor, umbral):
    if valor is None:
        return None
    if clave == "flake8":
        return max(0, 100 - 20 * valor)
    return min(100, valor * 100 / umbral)


# promedio de los valores que tienen dato
def promedio(valores):
    validos = [v for v in valores if v is not None]
    return sum(validos) / len(validos) if validos else None


# verde desde 80, amarillo desde 60, rojo debajo; sin puntaje es gris
def semaforo(puntaje):
    if puntaje is None:
        clave = "gris"
    else:
        clave = "verde" if puntaje >= 80 else "amarillo" if puntaje >= 60 else "rojo"
    etiqueta, bs, rgb = SEMAFOROS[clave]
    return {"etiqueta": etiqueta, "bs": bs, "rgb": rgb}


def texto(puntaje):
    return "-" if puntaje is None else f"{puntaje:.0f}"


# calcula puntajes y semaforos a partir de valores {dimension: {metrica: valor}}
def evaluar(valores):
    dimensiones = []
    for clave, nombre in DIMENSIONES:
        metricas = []
        for m, etiqueta, umbral in METRICAS[clave]:
            valor = valores.get(clave, {}).get(m)
            puntaje = puntaje_metrica(m, valor, umbral)
            if m == "flake8":
                dato, meta = ("Sin dato" if valor is None else f"{valor} errores"), "0 errores"
            else:
                dato, meta = ("Sin dato" if valor is None else f"{valor:.1f}%"), f"{umbral}%"
            metricas.append({"nombre": etiqueta, "valor": dato, "umbral": meta,
                             "puntaje": puntaje, "texto": texto(puntaje)})
        puntaje = promedio(m["puntaje"] for m in metricas)
        dimensiones.append({"nombre": nombre, "puntaje": puntaje, "texto": texto(puntaje),
                            "semaforo": semaforo(puntaje), "metricas": metricas})
    puntaje = promedio(d["puntaje"] for d in dimensiones)
    return {"dimensiones": dimensiones, "puntaje": puntaje, "texto": texto(puntaje),
            "semaforo": semaforo(puntaje)}


# reune de la base los valores de un sprint por dimension
def valores_de(sprint):
    metrica = getattr(sprint, "metrica", None)
    valores = {}
    for clave, _ in DIMENSIONES:
        actividades = Actividad.objects.filter(sprint=sprint, dimension=clave)
        con_revisor = actividades.filter(revisor__isnull=False)
        defectos = Defecto.objects.filter(actividad__in=actividades)
        encontrados = defectos.count()
        valores[clave] = {
            "plan": porcentaje(actividades.filter(hecha=True).count(), actividades.count()),
            "revisados": porcentaje(
                con_revisor.filter(estado_revision__in=["aprobada", "rechazada"]).count(),
                con_revisor.count()),
            "pasan": porcentaje(con_revisor.filter(estado_revision="aprobada").count(),
                                con_revisor.count()),
            # sin defectos vale 100, pero solo si la dimension tiene actividades
            "defectos": None if not actividades.exists() else 100 if not encontrados
            else porcentaje(defectos.filter(estado="corregido").count(), encontrados),
        }
    if metrica:
        valores["construccion"].update(cobertura=metrica.cobertura,
                                       pruebas=metrica.pct_aprobadas(), flake8=metrica.flake8)
    return valores


# reporte del proyecto: puntaje global (promedio de sprints) y detalle por sprint
def reporte(proyecto):
    sprints = [{"sprint": s, **evaluar(valores_de(s))} for s in proyecto.sprints.all()]
    puntaje = promedio(s["puntaje"] for s in sprints)
    return {"proyecto": proyecto, "puntaje": puntaje, "texto": texto(puntaje),
            "semaforo": semaforo(puntaje), "sprints": sprints}
