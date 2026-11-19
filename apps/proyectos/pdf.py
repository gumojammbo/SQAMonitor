from fpdf import FPDF


# las fuentes base del pdf solo admiten latin-1
def limpio(texto):
    return texto.encode("latin-1", "replace").decode("latin-1")


# titulo con el puntaje y el color del semaforo a la derecha
def encabezado(pdf, titulo, texto, semaforo, tam):
    pdf.set_font("Helvetica", "B", tam)
    pdf.cell(130, 8, limpio(titulo))
    pdf.set_fill_color(*semaforo["rgb"])
    pdf.cell(50, 8, f"{texto}  {semaforo['etiqueta']}", align="C", fill=True,
             new_x="LMARGIN", new_y="NEXT")


# genera el pdf del reporte de salud y lo devuelve como bytes
def generar(r):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, limpio(f"Reporte de salud: {r['proyecto'].nombre}"),
             new_x="LMARGIN", new_y="NEXT")
    encabezado(pdf, "Puntaje del proyecto", r["texto"], r["semaforo"], 13)
    for s in r["sprints"]:
        pdf.ln(4)
        encabezado(pdf, f"{s['sprint'].nombre} ({s['sprint'].inicio:%d/%m/%Y} a "
                        f"{s['sprint'].fin:%d/%m/%Y})", s["texto"], s["semaforo"], 12)
        for d in s["dimensiones"]:
            encabezado(pdf, d["nombre"], d["texto"], d["semaforo"], 10)
            pdf.set_font("Helvetica", "", 9)
            for m in d["metricas"]:
                pdf.cell(80, 6, "   " + limpio(m["nombre"]))
                pdf.cell(35, 6, m["valor"])
                pdf.cell(35, 6, f"meta {m['umbral']}")
                pdf.cell(30, 6, f"puntaje {m['texto']}", new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
