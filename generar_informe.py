"""Genera Practica7_CSP_Informe.pdf a partir de los datos medidos (CSV, salida_demo.txt, figuras)."""
import csv
import json
import os
import platform
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Flowable
from pygments import lex
from pygments.lexers import PythonLexer
from pygments.token import Token
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, Preformatted,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

pdfmetrics.registerFont(TTFont('DejaVuSansMono', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'))
NOMBRE, CODIGO = "Gonzalez Martinez Alondra Goretti", "218534681"
AZUL, AZUL2, NARANJA, ZEBRA = colors.HexColor("#1f3a5f"), colors.HexColor("#2f6fd6"), colors.HexColor("#e0902c"), colors.HexColor("#e6ecf7")
SALIDA = "Practica7_CSP_Informe.pdf"

# ---------------------------------------------------------------- datos medidos
demo = open("salida_demo.txt", encoding="utf-8").read()
num = lambda p: float(re.search(p, demo).group(1))
t_sec = num(r"Tiempo secuencial: ([\d.]+) s")
t_pip = num(r"Tiempo pipeline CSP: ([\d.]+) s")
t_arr = num(r"crear los procesos: ([\d.]+) s")
b_prod = num(r"Bloqueo del Productor.*?([\d.]+) ms")
b_calc = num(r"Bloqueo del Calculador.*?([\d.]+) ms")
e_calc = num(r"Espera del Calculador.*?([\d.]+) ms")
e_acum = num(r"Espera del Acumulador.*?([\d.]+) ms")
eventos = json.load(open("eventos_demo.json", encoding="utf-8"))
primer_bloqueo = next(e for e in eventos if e["tipo"] == "ENVIA" and e["bloqueo"] > 1e-3)
cap = list(csv.DictReader(open("capacidad.csv", encoding="utf-8")))
cue = list(csv.DictReader(open("cuellos.csv", encoding="utf-8")))
RET = {"Balanceado (10/10/10 ms)": (10, 10, 10), "Cuello medio (5/15/5 ms)": (5, 15, 5), "Cuello fuerte (5/30/5 ms)": (5, 30, 5)}
f1 = lambda x, d=2: f"{float(x):.{d}f}"

# ---------------------------------------------------------------- figura 1 (arquitectura)
def fig_arquitectura():
    fig, ax = plt.subplots(figsize=(9, 3.2)); ax.set_xlim(0, 100); ax.set_ylim(0, 36); ax.axis("off")
    def caja(x, y, w, h, txt, fc, ec):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.2", fc=fc, ec=ec, lw=1))
        ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center", fontsize=8)
    def flecha(x1, y1, x2, y2, txt="", dy=1.8):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", lw=1.1, color="#333"))
        if txt: ax.text((x1 + x2) / 2, (y1 + y2) / 2 + dy, txt, ha="center", fontsize=7)
    for x, nom, d in ((2, "Productor", "genera 1..n\n(5 ms)"), (38, "Calculador", "eleva al cuadrado\n(15 ms)"), (74, "Acumulador", "suma los cuadrados\n(5 ms)")):
        caja(x, 18, 24, 12, f"{nom}\n{d}", "#e1f0ea", "#1a9a78")
    flecha(26.5, 24, 37.5, 24, "canal A\nQueue(2)", 2.2)
    flecha(62.5, 24, 73.5, 24, "canal B\nQueue(2)", 2.2)
    caja(38, 2, 24, 8, "Logger\n(imprime y recopila eventos)", "#fbeadb", "#e0680c")
    for x in (14, 50, 86):
        flecha(x, 17.5, 50 if x != 50 else 50, 10.8, "", 0)
    ax.text(14, 13.2, "canal de eventos", fontsize=7, ha="center")
    caja(74, 2, 24, 8, "Proceso principal\n(Pipe: resultado final)", "#e6ecf7", "#1f3a5f")
    flecha(86, 17.5, 86, 10.8, "", 0)
    fig.tight_layout(); fig.savefig("fig_arquitectura.png", dpi=170); plt.close(fig)

fig_arquitectura()

# ---------------------------------------------------------------- estilos
cuerpo = ParagraphStyle("cuerpo", fontName="Times-Roman", fontSize=10.2, leading=13.4, alignment=TA_JUSTIFY, spaceAfter=5)
pie = ParagraphStyle("pie", fontName="Helvetica", fontSize=8, leading=10, alignment=TA_CENTER, textColor=colors.HexColor("#666"), spaceAfter=8)
h2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11.5, textColor=AZUL2, spaceBefore=8, spaceAfter=4, keepWithNext=1)
h1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=15, textColor=colors.white, leading=18)
viñeta = ParagraphStyle("vineta", parent=cuerpo, leftIndent=14, bulletIndent=3, spaceAfter=2)
celda = ParagraphStyle("celda", fontName="Helvetica", fontSize=8.4, leading=10.5)
celda_h = ParagraphStyle("celda_h", parent=celda, fontName="Helvetica-Bold", textColor=colors.white)
codigo = ParagraphStyle("codigo", fontName="Courier", fontSize=6.5, leading=7.7, backColor=colors.HexColor("#f4f6fa"), borderPadding=4)
captura = ParagraphStyle("captura", fontName="Courier", fontSize=5.0, leading=6.05, backColor=colors.HexColor("#151b28"),
                         textColor=colors.HexColor("#d7e3f4"))


def seccion(titulo):
    t = Table([[Paragraph(titulo, h1)]], colWidths=[ANCHO])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), AZUL), ("LEFTPADDING", (0, 0), (-1, -1), 14),
                           ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9)]))
    return [t, Spacer(1, 8)]


def tabla(encabezado, filas, anchos, negrita_ultima=False):
    datos = [[Paragraph(c, celda_h) for c in encabezado]] + [[Paragraph(str(c), celda) for c in f] for f in filas]
    t = Table(datos, colWidths=[a * inch for a in anchos], repeatRows=1)
    est = [("BACKGROUND", (0, 0), (-1, 0), AZUL), ("LINEBELOW", (0, 0), (-1, 0), 1.6, NARANJA),
           ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
    for i in range(2, len(datos), 2):
        est.append(("BACKGROUND", (0, i), (-1, i), ZEBRA))
    t.setStyle(TableStyle(est))
    return t


def figura(archivo, ancho, texto):
    from PIL import Image as PI
    w, h = PI.open(archivo).size
    return KeepTogether([Image(archivo, width=ancho * inch, height=ancho * inch * h / w), pie_fig(texto)])


def P(t): return Paragraph(t, cuerpo)
def V(t): return Paragraph(t, viñeta, bulletText="\u2022")


def portada_fondo(canvas, doc):
    canvas.saveState()
    p = canvas.beginPath(); p.rect(0, 0, 0.37 * inch, 11 * inch); canvas.clipPath(p, stroke=0, fill=0)
    canvas.linearGradient(0, 11 * inch, 0, 0, [colors.Color(194 / 255, 38 / 255, 217 / 255), colors.Color(105 / 255, 112 / 255, 191 / 255),
                                              colors.Color(18 / 255, 184 / 255, 166 / 255)], extend=False)
    canvas.restoreState()


def encabezado_pie(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.8); canvas.setFillColor(colors.HexColor("#555"))
    canvas.drawString(0.72 * inch, 10.45 * inch, "Práctica 7 · Modelos de concurrencia (CSP)")
    canvas.drawRightString(7.78 * inch, 10.45 * inch, "Programación paralela y concurrente")
    canvas.setStrokeColor(AZUL); canvas.setLineWidth(0.8); canvas.line(0.72 * inch, 10.38 * inch, 7.78 * inch, 10.38 * inch)
    canvas.setStrokeColor(colors.HexColor("#c9d0dc")); canvas.setLineWidth(0.6); canvas.line(0.72 * inch, 0.72 * inch, 7.78 * inch, 0.72 * inch)
    canvas.setFillColor(colors.HexColor("#555")); canvas.drawString(0.72 * inch, 0.5 * inch, f"{NOMBRE} · {CODIGO}")
    canvas.setFillColor(AZUL); canvas.roundRect(7.38 * inch, 0.42 * inch, 0.4 * inch, 0.24 * inch, 5, fill=1, stroke=0)
    canvas.setFillColor(colors.white); canvas.setFont("Helvetica-Bold", 8); canvas.drawCentredString(7.58 * inch, 0.49 * inch, str(doc.page))
    canvas.restoreState()


VENTANA_BG, VENTANA_BAR = colors.HexColor("#171a26"), colors.HexColor("#2b2f40")
ANCHO = 7.07 * inch
PALETA = {Token.Keyword: "#b4a6ff", Token.Name.Builtin: "#7aa2f7", Token.Name.Function: "#7aa2f7", Token.Literal.String: "#a5d66a",
          Token.Literal.Number: "#f0a05c", Token.Comment: "#6b7089", Token.Operator.Word: "#b4a6ff"}


def color_token(tipo):
    while tipo is not Token:
        if tipo in PALETA:
            return PALETA[tipo]
        tipo = tipo.parent
    return "#d7dae6"


def lineas_resaltadas(codigo_fuente):
    """Lista de líneas; cada línea es una lista de (color, texto)."""
    lineas, actual = [], []
    for tipo, txt in lex(codigo_fuente, PythonLexer()):
        partes = txt.split("\n")
        for k, parte in enumerate(partes):
            if k > 0:
                lineas.append(actual); actual = []
            if parte:
                actual.append((color_token(tipo), parte))
    if actual:
        lineas.append(actual)
    return lineas


class Ventana(Flowable):
    """Ventana oscura estilo terminal/editor: barra con tres puntos y líneas coloreadas."""
    def __init__(self, lineas, titulo=None, tam=6.4, interlineado=7.8, numerar=0, ancho=ANCHO):
        super().__init__()
        self.lineas, self.titulo, self.tam, self.il, self.numerar, self.ancho = lineas, titulo, tam, interlineado, numerar, ancho
        self.barra = 20 if titulo else 0
        self.alto = self.barra + len(lineas) * interlineado + 14

    def wrap(self, aw, ah):
        return self.ancho, self.alto

    def draw(self):
        c = self.canv
        c.setFillColor(VENTANA_BG); c.roundRect(0, 0, self.ancho, self.alto, 7, fill=1, stroke=0)
        if self.titulo:
            c.saveState(); p = c.beginPath(); p.roundRect(0, 0, self.ancho, self.alto, 7); c.clipPath(p, stroke=0, fill=0)
            c.setFillColor(VENTANA_BAR); c.rect(0, self.alto - self.barra, self.ancho, self.barra, fill=1, stroke=0); c.restoreState()
            for i, col in enumerate(("#ff5f57", "#febc2e", "#28c840")):
                c.setFillColor(colors.HexColor(col)); c.circle(12 + i * 12, self.alto - self.barra / 2, 2.8, fill=1, stroke=0)
            c.setFillColor(colors.HexColor("#9aa0b8")); c.setFont("Helvetica", 7); c.drawString(52, self.alto - self.barra / 2 - 2.4, self.titulo)
        y = self.alto - self.barra - 11
        ancho_car = pdfmetrics.stringWidth("0", "DejaVuSansMono", self.tam)
        x0 = 12 + (self.numerar and (len(str(self.numerar + len(self.lineas))) + 1.8) * ancho_car)
        for i, linea in enumerate(self.lineas):
            if self.numerar:
                c.setFillColor(colors.HexColor("#6b7089")); c.setFont("DejaVuSansMono", self.tam)
                c.drawRightString(x0 - 1.8 * ancho_car, y, str(self.numerar + i))
            x = x0
            for col, txt in linea:
                c.setFillColor(colors.HexColor(col)); c.setFont("DejaVuSansMono", self.tam); c.drawString(x, y, txt)
                x += pdfmetrics.stringWidth(txt, "DejaVuSansMono", self.tam)
            y -= self.il


def pie_fig(texto):
    """Pie de figura: «Figura N.» en azul y negrita, texto gris, fuente en cursiva."""
    texto = re.sub(r"<b>(Figura \d+\.)</b>", r"<font color='#2f6fd6'><b>\1</b></font>", texto)
    return Paragraph(texto, pie)



S = []
# ---------------------------------------------------------------- portada (mismo diseño que la Práctica 5)
sans_b = ParagraphStyle("sb", fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=colors.white, alignment=TA_CENTER)
S += [Spacer(1, 0.05 * inch), Paragraph("<b>UNIVERSIDAD DE GUADALAJARA</b>", ParagraphStyle("u", fontName="Times-Bold", fontSize=29, leading=34, alignment=TA_CENTER)),
      Table([[""]], colWidths=[ANCHO], rowHeights=[4], style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.black)])), Spacer(1, 6),
      Paragraph("<b>CENTRO UNIVERSITARIO DE CIENCIAS EXACTAS E INGENIERÍAS</b>", ParagraphStyle("c1", fontName="Times-Roman", fontSize=9.5, leading=12.5, alignment=TA_CENTER)),
      Paragraph("Departamento de Innovación Basada en la Información y el Conocimiento", ParagraphStyle("c2", fontName="Times-Roman", fontSize=11, leading=14, alignment=TA_CENTER)),
      Spacer(1, 0.3 * inch), Image("escudo_udg.png", width=1.55 * inch, height=1.55 * inch * 460 / 360), Spacer(1, 0.12 * inch),
      Paragraph("Ingeniería En Computación", ParagraphStyle("c3", fontName="Times-Roman", fontSize=11.5, leading=15, alignment=TA_CENTER)), Spacer(1, 0.1 * inch)]
bloque = Table([[Paragraph("PRÁCTICA 7", sans_b)],
                [Paragraph("Modelos de Concurrencia: CSP", ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=22, leading=27, textColor=colors.white, alignment=TA_CENTER))],
                [Paragraph("Pipeline de procesos con canales: multiprocessing.Queue y Pipe", ParagraphStyle("st", fontName="Helvetica", fontSize=9, leading=12, textColor=colors.HexColor("#c9d6ea"), alignment=TA_CENTER))]],
               colWidths=[ANCHO])
bloque.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), AZUL), ("TOPPADDING", (0, 0), (0, 0), 20), ("BOTTOMPADDING", (0, -1), (-1, -1), 22),
                            ("TOPPADDING", (0, 1), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, 0), 4)]))
cel = ParagraphStyle("cel", fontName="Times-Roman", fontSize=9.5, leading=12)
info = Table([[Paragraph(f"<b>Nombre</b>: {NOMBRE.upper()}", cel), Paragraph(f"<b>Código</b>: {CODIGO}", cel)],
              [Paragraph("<b>Materia</b>: Programación paralela y concurrente", cel), Paragraph("<b>Grupo</b>: ____________", cel)],
              [Paragraph("<b>Nombre del profesor</b>: Mtro. Zeus Cobián", cel), Paragraph("<b>Actividad</b>: Práctica 7 (100 puntos)", cel)],
              [Paragraph("<b>Fecha de entrega</b>: 20 de noviembre del 2026", cel), Paragraph("<b>Lenguaje</b>: Python 3.12 · multiprocessing", cel)]],
             colWidths=[0.58 * ANCHO, 0.42 * ANCHO])
info.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ZEBRA), ("GRID", (0, 0), (-1, -1), 0.8, colors.black),
                          ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7), ("LEFTPADDING", (0, 0), (-1, -1), 9)]))
bs = ParagraphStyle("bib", fontName="Times-Roman", fontSize=6.9, leading=8.6)
biblio = Table([[[Paragraph("<b>Bibliografía:</b>", bs),
                  Paragraph("Hoare, C. A. R. (1978). Communicating sequential processes. <i>Communications of the ACM, 21</i>(8), 666–677.", bs),
                  Paragraph("Python Software Foundation. (s. f.). multiprocessing — Process-based parallelism. <i>Python 3 Documentation</i>.", bs),
                  Paragraph("Gutiérrez Cobián, Z. E. (2026). <i>Semana 10 – Guía de práctica: Modelos de concurrencia (CSP y Actores)</i>. CUCEI, Universidad de Guadalajara.", bs),
                  Paragraph("Recursos didácticos de la asignatura (Semana 10 – Modelos de concurrencia).", bs)]]], colWidths=[ANCHO])
biblio.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fde8c8")), ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
                            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 8), ("LEFTPADDING", (0, 0), (-1, -1), 9)]))
S += [bloque, info, biblio, PageBreak()]

# ---------------------------------------------------------------- 1. objetivo
S += seccion("1. Objetivo de la práctica")
S += [P("Implementar un ejemplo del modelo de concurrencia <b>CSP</b>: tres procesos secuenciales independientes (Productor, Calculador y Acumulador) "
        "que no comparten memoria y se coordinan únicamente enviándose mensajes por <b>canales</b> (<font face='DejaVuSansMono' size='8.6'>multiprocessing.Queue</font> y "
        "<font face='DejaVuSansMono' size='8.6'>Pipe</font>). El programa imprime cada intercambio de mensajes y cada bloqueo para visualizar la sincronización, y el informe "
        "analiza qué ocurre entre los procesos: quién espera a quién, dónde se forma el cuello de botella y cómo termina el flujo.")]

# ---------------------------------------------------------------- 2. fundamento
S += seccion("2. Elección del modelo y fundamento")
S += [P("<b>Elegí CSP en lugar de Actores</b> porque la guía pide visualizar la coordinación, y en CSP la sincronización queda explícita en el canal: "
        "<font face='DejaVuSansMono' size='8.6'>put()</font> se bloquea cuando el canal está lleno y <font face='DejaVuSansMono' size='8.6'>get()</font> se bloquea cuando está vacío, "
        "así que se puede <i>ver</i> cuándo un proceso espera a otro. Además, <font face='DejaVuSansMono' size='8.6'>multiprocessing</font> crea procesos reales con memoria "
        "separada, que es justo la premisa de CSP (Hoare, 1978): procesos secuenciales que solo interactúan por comunicación."),
      P("En CSP los procesos son anónimos y lo que se nombra es el canal; en el modelo de Actores cada actor tiene una dirección y un buzón propio y el envío "
        "es asíncrono. Un detalle de fidelidad: en la formulación original de Hoare la comunicación es síncrona (encuentro entre emisor y receptor), mientras que "
        "<font face='DejaVuSansMono' size='8.6'>Queue(maxsize=n)</font> es un canal con <b>búfer acotado</b> de capacidad n, una variante habitual de CSP. "
        "Por eso la capacidad del canal es uno de los parámetros que se analizan en la sección 4."),
      figura("fig_arquitectura.png", 6.4, "<b>Figura 1.</b> Arquitectura del programa: tres procesos de trabajo conectados por canales, un proceso logger y el proceso principal. <i>Fuente: elaboración propia.</i>")]
S += [Paragraph("Metodología de medición", h2),
      V("Cada etapa simula su trabajo con <font face='DejaVuSansMono' size='8.6'>time.sleep</font> (Productor 5 ms, Calculador 15 ms, Acumulador 5 ms por mensaje). "
        "El <i>sleep</i> libera la CPU, por lo que el solapamiento entre procesos se observa aunque el equipo tenga un solo núcleo; es una simulación de trabajo, no cálculo real."),
      V("Los tres procesos de trabajo y el principal esperan en una <font face='DejaVuSansMono' size='8.6'>Barrier</font>; el tiempo se mide desde que se libera, de modo que "
        "el costo de crear los procesos (spawn) se reporta aparte."),
      V("Corrida de demostración: 8 mensajes y canales de capacidad 2. Experimentos: 40 mensajes, mediana de 5 repeticiones. "
        "En los experimentos el tiempo secuencial es el valor calculado (n × suma de los retardos); en la demostración se midió."),
      V(f"Entorno de prueba: Python {platform.python_version()}, {platform.system()} {platform.release()}, <b>{os.cpu_count()} núcleo(s) lógico(s)</b>.")]

# ---------------------------------------------------------------- 3. código
S += [PageBreak()] + seccion("3. Código de la práctica") + [Paragraph("3.1 Programa completo (csp_pipeline.py)", h2)]
fuente = open("csp_pipeline.py", encoding="utf-8").read()
todas = lineas_resaltadas(fuente)
POR_VENTANA = 66
for k in range(0, len(todas), POR_VENTANA):
    S.append(Ventana(todas[k:k + POR_VENTANA], titulo="csp_pipeline.py · Python 3" if k == 0 else None, numerar=k + 1))
    S.append(Spacer(1, 8))
S += [P("Los scripts <font face='DejaVuSansMono' size='8.6'>experimento.py</font> y <font face='DejaVuSansMono' size='8.6'>generar_informe.py</font> (incluidos en la entrega) repiten las mediciones y generan "
        "las tablas, las gráficas y este PDF. Todo se ejecuta con <font face='DejaVuSansMono' size='8.6'>python csp_pipeline.py</font>, <font face='DejaVuSansMono' size='8.6'>python experimento.py</font> y "
        "<font face='DejaVuSansMono' size='8.6'>python generar_informe.py</font>.")]

# ---------------------------------------------------------------- 4. resultados
S += [PageBreak()] + seccion("4. Resultados") + [Paragraph("4.1 Captura de la ejecución", h2),
      P("Salida real del programa (8 mensajes, canales de capacidad 2). Las líneas aparecen en el orden en que llegan al canal de eventos; "
        "entre procesos distintos pueden diferir en cerca de 1 ms respecto a su marca de tiempo.")]
def colorear_salida(texto):
    out = []
    for l in ("$ python csp_pipeline.py\n\n" + texto.rstrip("\n")).split("\n"):
        col = "#a5d66a" if l.startswith(("$", "-->")) else "#7aa2f7" if l.startswith("===") else "#d7dae6"
        out.append([(col, l)] if l else [])
    return out

S.append(pie_fig("<b>Figura 2.</b> Ejecución del pipeline CSP con impresión de cada mensaje, espera y bloqueo. <i>Fuente: elaboración propia.</i>"))
S.append(Ventana(colorear_salida(demo), titulo="terminal — csp_pipeline.py", tam=4.9, interlineado=5.75))
S += [PageBreak(), Paragraph("4.2 Comparación y línea de tiempo", h2),
      KeepTogether([P("<b>Tabla 1.</b> Corrida de referencia (8 mensajes, capacidad 2)."),
      tabla(["Versión", "Tiempo (ms)", "Aceleración"],
            [["Secuencial (una sola tarea)", f1(t_sec * 1000), "1.00×"], ["Pipeline CSP (3 procesos)", f1(t_pip * 1000), f"{t_sec / t_pip:.2f}×"],
             ["Crear los procesos (aparte)", f1(t_arr * 1000), "—"]], [3.0, 2.0, 2.0])]),
      Spacer(1, 6),
      tabla(["Sincronización en la corrida", "Tiempo acumulado (ms)"],
            [["Productor bloqueado (canal A lleno)", f1(b_prod, 1)], ["Calculador bloqueado (canal B lleno)", f1(b_calc, 1)],
             ["Calculador esperando (canal A vacío)", f1(e_calc, 1)], ["Acumulador esperando (canal B vacío)", f1(e_acum, 1)]], [4.0, 3.0]),
      Spacer(1, 8),
      figura("fig_linea_tiempo.png", 6.6, "<b>Figura 3.</b> Línea de tiempo de la corrida de la captura: verde = trabajando, rojo = bloqueado por canal lleno, gris = esperando por canal vacío. <i>Fuente: elaboración propia.</i>")]

S += [Paragraph("4.3 Efecto de la capacidad del canal", h2),
      P("<b>Tabla 2.</b> Mediana de 5 repeticiones, 40 mensajes, retardos 5/15/5 ms."),
      tabla(["Capacidad", "Secuencial (ms)", "Pipeline (ms)", "Aceleración", "Productor bloqueado (ms)", "Acumulador esperando (ms)"],
            [[c["capacidad"], f1(c["secuencial_ms"], 0), f1(c["pipeline_ms"], 1), f"{float(c['acel']):.2f}×", f1(c["bloq_prod_ms"], 1), f1(c["espera_acum_ms"], 1)] for c in cap],
            [0.8, 1.1, 1.1, 1.0, 1.55, 1.55]),
      Spacer(1, 8),
      figura("fig_capacidad.png", 6.6, "<b>Figura 4.</b> Con más capacidad el tiempo total no cambia, pero el bloqueo del productor baja. <i>Fuente: elaboración propia.</i>")]

filas_c = []
for c in cue:
    r = RET[c["escenario"]]
    filas_c.append([c["escenario"], f1(c["secuencial_ms"], 0), f1(c["pipeline_ms"], 1), f"{float(c['acel']):.2f}×", f"{sum(r) / max(r):.2f}×"])
S += [Paragraph("4.4 Efecto del desbalance entre etapas", h2),
      P("<b>Tabla 3.</b> Capacidad 2, 40 mensajes. «Límite» es la aceleración máxima de un pipeline: suma de los retardos entre el retardo de la etapa más lenta."),
      tabla(["Escenario (productor/calculador/acumulador)", "Secuencial (ms)", "Pipeline (ms)", "Aceleración medida", "Límite (suma/máx)"], filas_c, [2.6, 1.0, 1.0, 1.2, 1.2]),
      Spacer(1, 8),
      figura("fig_cuellos.png", 5.6, "<b>Figura 5.</b> El proceso más lento fija el ritmo de todo el pipeline. <i>Fuente: elaboración propia.</i>")]

# ---------------------------------------------------------------- 5. análisis entre procesos
c1, c20 = cap[0], cap[-1]
S += [PageBreak()] + seccion("5. Análisis entre procesos")
S += [Paragraph("Coordinación sin memoria compartida", h2),
      P("Cada proceso tiene su propio PID (en la captura aparecen tres distintos más el del logger) y solo conoce sus canales: el Productor no sabe quién consume y el "
        "Acumulador no sabe quién produce. Todo lo que intercambian son mensajes (enteros y el centinela <font face='DejaVuSansMono' size='8.6'>None</font>); incluso el resultado final "
        "viaja por un <font face='DejaVuSansMono' size='8.6'>Pipe</font> hacia el proceso principal. La impresión la hace un único proceso, el Logger, para que las líneas no se mezclen."),
      Paragraph("Sincronización implícita por el canal", h2),
      P(f"No hay <i>locks</i> ni variables compartidas: la sincronización ocurre dentro de <font face='DejaVuSansMono' size='8.6'>put()</font> y <font face='DejaVuSansMono' size='8.6'>get()</font>. "
        f"En la captura, el Calculador tarda 15 ms por mensaje y el Productor solo 5 ms, así que el canal A se llena. El primer bloqueo aparece al enviar el "
        f"dato {primer_bloqueo['detalle'].split(' ')[0]}: dos datos esperan en el canal, uno está en manos del Calculador y el siguiente ya no cabe, de modo que el "
        f"Productor debe esperar. Desde ahí el Productor queda bloqueado unos 10 ms por mensaje (suma de {b_prod:.1f} ms). Es <b>contrapresión</b> (<i>backpressure</i>): "
        f"el proceso más lento frena al más rápido sin que nadie lo programe explícitamente. En sentido contrario, el Acumulador pasa {e_acum:.1f} ms esperando "
        f"en canal B vacío, porque depende del Calculador."),
      Paragraph("El cuello de botella fija el ritmo", h2),
      P(f"El pipeline entrega un resultado cada 15 ms, el ritmo de su etapa más lenta; con 40 mensajes eso son unos 600 ms más el llenado y vaciado del flujo "
        f"(medido: {float(cap[1]['pipeline_ms']):.0f} ms). La aceleración máxima es suma/máx = 25/15 = 1.67× y se midió {float(cap[1]['acel']):.2f}×. La Tabla 3 lo confirma: "
        f"con etapas balanceadas el límite sube a 3.00× (medido {float(cue[0]['acel']):.2f}×) y con un cuello fuerte baja a 1.33× (medido {float(cue[2]['acel']):.2f}×). "
        f"Acelerar una etapa que no es el cuello no mejora el total; la mejora real está en balancear o repartir la etapa lenta."),
      Paragraph("Capacidad del canal: desacopla, no acelera", h2),
      P(f"Pasar la capacidad de 1 a 20 dejó el tiempo total prácticamente igual ({float(c1['pipeline_ms']):.0f} ms contra {float(c20['pipeline_ms']):.0f} ms), pero el bloqueo "
        f"del Productor bajó de {float(c1['bloq_prod_ms']):.0f} ms a {float(c20['bloq_prod_ms']):.0f} ms: con un canal grande el Productor entrega sus 40 mensajes más pronto y se bloquea menos. "
        f"Es decir, el búfer cambia <i>dónde</i> se acumula la espera, no el ritmo. Como costo, un canal grande guarda más datos en vuelo y pierde la contrapresión, "
        f"lo que en un sistema real puede agotar memoria si el productor es mucho más rápido que el consumidor."),
      Paragraph("Interbloqueo y terminación", h2),
      P("El grafo de canales es una cadena sin ciclos (canal A, canal B) y cada canal tiene un único emisor y un único receptor, por eso no hay espera circular. Si hubiera un ciclo con "
        "canales llenos (por ejemplo, dos procesos que se envían mensajes entre sí con <font face='DejaVuSansMono' size='8.6'>put()</font> antes de hacer <font face='DejaVuSansMono' size='8.6'>get()</font>) "
        "podría producirse un interbloqueo. El canal de eventos no tiene límite de capacidad, así que registrar nunca bloquea a un proceso de trabajo. "
        "La terminación es ordenada: el Productor envía el centinela <font face='DejaVuSansMono' size='8.6'>None</font>, el Calculador lo reenvía al canal B y el Acumulador responde con el "
        "total, con lo que todos los procesos terminan sin <i>kill</i> ni tiempos de espera."),
      Paragraph("Diferencia con la Práctica 6", h2),
      P("En la Práctica 6 se repartían <i>datos independientes</i> (data parallelism) entre procesos de un <i>pool</i> y, con un solo núcleo, no hubo mejora porque el trabajo "
        "era cálculo de CPU. Aquí las tareas son dependientes y forman un flujo (task parallelism, en cadena); la mejora aparece incluso con un núcleo porque el trabajo simulado "
        "es espera (<font face='DejaVuSansMono' size='8.6'>sleep</font>) y no consume CPU. Con trabajo de CPU real en un equipo de un solo núcleo, el pipeline no sería más rápido que la versión secuencial.")]

# ---------------------------------------------------------------- 6. conclusión personal
S += [PageBreak()] + seccion("6. Conclusión personal")
S += [P("Con esta práctica entendí que CSP cambia la forma de pensar la concurrencia: en lugar de proteger datos compartidos con <i>locks</i>, cada proceso es un programa "
        "secuencial simple y la coordinación vive en los canales. Lo que más me sorprendió fue ver la sincronización en la línea de tiempo: nadie le dijo al Productor que "
        "esperara, pero el canal lleno lo detuvo solo, y el Acumulador pasó casi todo el tiempo esperando porque dependía del Calculador. También me quedó claro "
        f"que más procesos no significan más velocidad: el pipeline ganó {t_sec / t_pip:.2f}× en la demostración y {float(cap[1]['acel']):.2f}× con 40 mensajes, "
        "y nunca pudo superar el límite que marca la etapa más lenta. Otra lección fue comparar con la Práctica 6: allí paralelizar no ayudó porque el trabajo era muy corto y "
        "había un solo núcleo; aquí ayudó porque las etapas esperan, así que el tipo de trabajo importa tanto como el modelo. Si repitiera la práctica, probaría balancear "
        "la etapa del Calculador con varios procesos leyendo del mismo canal, y también implementaría la versión con Actores para comparar cómo se escribe la misma coordinación.")]

S += [Paragraph("Referencias", h2),
      Paragraph("Hoare, C. A. R. (1978). Communicating sequential processes. <i>Communications of the ACM, 21</i>(8), 666–677. https://doi.org/10.1145/359576.359585", celda),
      Spacer(1, 3),
      Paragraph("Python Software Foundation. (s. f.). multiprocessing — Process-based parallelism. <i>Python 3 Documentation</i>. https://docs.python.org/3/library/multiprocessing.html", celda),
      Spacer(1, 3),
      Paragraph("Gutiérrez Cobián, Z. E. (2026). <i>Semana 10 – Guía de práctica: Modelos de concurrencia (CSP y Actores)</i> [Guía]. CUCEI, Universidad de Guadalajara.", celda)]

doc = SimpleDocTemplate(SALIDA, pagesize=letter, leftMargin=0.72 * inch, rightMargin=0.72 * inch, topMargin=0.85 * inch, bottomMargin=0.8 * inch,
                        title="Práctica 7 · Modelos de concurrencia (CSP)", author=NOMBRE)
doc.build(S, onFirstPage=portada_fondo, onLaterPages=encabezado_pie)
print("OK", SALIDA)
