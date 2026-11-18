# Práctica 7 · Modelos de concurrencia (CSP)

Pipeline de tres procesos secuenciales (Productor, Calculador, Acumulador) que se comunican solo por canales
(`multiprocessing.Queue` y `Pipe`), más un proceso Logger que imprime cada intercambio de mensajes.

## Ejecutarlo
```bash
python csp_pipeline.py            # demostración: 8 mensajes, canales de capacidad 2
python csp_pipeline.py -n 12 -c 1 # otros parámetros
python experimento.py             # capacidad del canal y cuellos de botella (CSV + gráficas)
python generar_informe.py         # Practica7_CSP_Informe.pdf  (requiere reportlab, matplotlib, pillow)
python generar_pagina.py          # index.html (laboratorio interactivo)
```
Requisitos: Python 3.12; para las gráficas y el PDF, `pip install matplotlib reportlab pillow`.

## Publicar en GitHub Pages
1. Sube el contenido de esta carpeta a un repositorio (raíz o carpeta `/docs`).
2. En *Settings → Pages* elige la rama y la carpeta; `index.html` será la página principal.

## Archivos
- `csp_pipeline.py`: programa principal (CSP con canales).
- `experimento.py`: experimentos A (capacidad) y B (desbalance entre etapas).
- `generar_informe.py`, `generar_pagina.py`: generan el PDF y la página web con los datos medidos.
- `capacidad.csv`, `cuellos.csv`, `salida_demo.txt`, `eventos_demo.json`: resultados.
- `Practica7_CSP_Informe.pdf`: informe de la práctica.
- `escudo_udg.png`: escudo usado en la portada del informe.

Nota: el trabajo de cada etapa se simula con `time.sleep`; los tiempos dependen del equipo.
