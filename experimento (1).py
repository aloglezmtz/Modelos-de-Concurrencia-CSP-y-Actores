"""Experimentos de la Práctica 7 (análisis entre procesos).

A) Capacidad del canal (1, 2, 5, 10, 20): cuánto se bloquea cada proceso.
B) Desbalance entre etapas: el proceso más lento fija el ritmo de todo el pipeline.
Genera capacidad.csv, cuellos.csv, fig_capacidad.png, fig_cuellos.png y fig_linea_tiempo.png.
"""
import csv
import json
import statistics as st

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from csp_pipeline import ejecutar

N = 40
REPS = 5
CAPACIDADES = [1, 2, 5, 10, 20]
ESCENARIOS = {"Balanceado (10/10/10 ms)": (0.010, 0.010, 0.010),
              "Cuello medio (5/15/5 ms)": (0.005, 0.015, 0.005),
              "Cuello fuerte (5/30/5 ms)": (0.005, 0.030, 0.005)}
AZUL, NARANJA, VERDE, ROJO, GRIS = "#1f3a5f", "#e0680c", "#1a9a78", "#c0392b", "#9aa5b1"


def med(v):
    return st.median(v)


def correr(cap, ret):
    rs = [ejecutar(N, cap, ret) for _ in range(REPS)]
    sec = N * sum(ret)
    d = med([r["duracion"] for r in rs])
    return {"secuencial_ms": sec * 1000, "pipeline_ms": d * 1000, "acel": sec / d,
            "bloq_prod_ms": med([r["bloqueo_prod"] for r in rs]) * 1000,
            "bloq_calc_ms": med([r["bloqueo_calc"] for r in rs]) * 1000,
            "espera_calc_ms": med([r["espera_calc"] for r in rs]) * 1000,
            "espera_acum_ms": med([r["espera_acum"] for r in rs]) * 1000,
            "arranque_ms": med([r["arranque"] for r in rs]) * 1000}


def main():
    filas_a = []
    for c in CAPACIDADES:
        r = correr(c, (0.005, 0.015, 0.005))
        filas_a.append({"capacidad": c, **r})
        print("A", c, {k: round(v, 1) for k, v in r.items()}, flush=True)
    filas_b = []
    for nombre, ret in ESCENARIOS.items():
        r = correr(2, ret)
        filas_b.append({"escenario": nombre, **r})
        print("B", nombre, {k: round(v, 1) for k, v in r.items()}, flush=True)

    for nombre, filas in (("capacidad.csv", filas_a), ("cuellos.csv", filas_b)):
        with open(nombre, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
            w.writeheader()
            w.writerows([{k: (round(v, 3) if isinstance(v, float) else v) for k, v in fila.items()} for fila in filas])

    # --- Fig: capacidad del canal -------------------------------------------------
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
    x = [f["capacidad"] for f in filas_a]
    ax[0].plot(x, [f["pipeline_ms"] for f in filas_a], "s-", color=VERDE, label="Pipeline CSP")
    ax[0].axhline(filas_a[0]["secuencial_ms"], color=NARANJA, ls="--", label="Secuencial")
    ax[0].set(xlabel="Capacidad del canal", ylabel="Tiempo (ms)", title="Tiempo total (40 mensajes)")
    ax[0].legend(); ax[0].grid(alpha=.3); ax[0].set_xscale("log"); ax[0].set_xticks(x); ax[0].set_xticklabels(x)
    ax[1].plot(x, [f["bloq_prod_ms"] for f in filas_a], "o-", color=ROJO, label="Productor bloqueado (canal A lleno)")
    ax[1].plot(x, [f["espera_acum_ms"] for f in filas_a], "^-", color=GRIS, label="Acumulador esperando (canal B vacío)")
    ax[1].set(xlabel="Capacidad del canal", ylabel="Tiempo acumulado (ms)", title="Sincronización por proceso")
    ax[1].legend(fontsize=7); ax[1].grid(alpha=.3); ax[1].set_xscale("log"); ax[1].set_xticks(x); ax[1].set_xticklabels(x)
    fig.tight_layout(); fig.savefig("fig_capacidad.png", dpi=170); plt.close(fig)

    # --- Fig: cuellos de botella ---------------------------------------------------
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    nombres = [f["escenario"] for f in filas_b]
    xs = range(len(nombres))
    ax.bar([i - .2 for i in xs], [f["secuencial_ms"] for f in filas_b], .4, color=NARANJA, label="Secuencial")
    ax.bar([i + .2 for i in xs], [f["pipeline_ms"] for f in filas_b], .4, color=VERDE, label="Pipeline CSP")
    for i, f in enumerate(filas_b):
        ax.text(i + .2, f["pipeline_ms"] + 8, f"{f['acel']:.2f}x", ha="center", fontsize=8)
    ax.set_xticks(list(xs)); ax.set_xticklabels(nombres, fontsize=8)
    ax.set(ylabel="Tiempo (ms)", title="El proceso más lento fija el ritmo (40 mensajes, capacidad 2)")
    ax.legend(); ax.grid(axis="y", alpha=.3)
    fig.tight_layout(); fig.savefig("fig_cuellos.png", dpi=170); plt.close(fig)

    # --- Fig: línea de tiempo de la demostración (8 mensajes, capacidad 2) ---------
    with open("eventos_demo.json", encoding="utf-8") as f:   # misma corrida que salida_demo.txt
        ev = json.load(f)
    procs = ["Productor", "Calculador", "Acumulador"]
    fig, ax = plt.subplots(figsize=(9, 2.9))
    for y, p in enumerate(reversed(procs)):
        for e in (e for e in ev if e["proceso"] == p):
            t = e["t"] * 1000
            if e["tipo"] in ("PRODUCE", "CALCULA", "ACUMULA"):
                ax.barh(y, e["dur"] * 1000, left=t - e["dur"] * 1000, color=VERDE, height=.5)
            if e["tipo"] == "ENVIA" and e["bloqueo"] > 1e-3:
                ax.barh(y, e["bloqueo"] * 1000, left=t - e["bloqueo"] * 1000, color=ROJO, height=.5)
            if e["tipo"] in ("RECIBE", "FIN") and e["espera"] > 1e-3:
                ax.barh(y, e["espera"] * 1000, left=t - e["espera"] * 1000, color=GRIS, height=.5)
    ax.set_yticks(range(3)); ax.set_yticklabels(list(reversed(procs)))
    ax.set(xlabel="Tiempo (ms)", title="Línea de tiempo de los 3 procesos (8 mensajes, capacidad 2)")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=VERDE, label="Trabajando"), Patch(color=ROJO, label="Bloqueado (canal lleno)"),
                       Patch(color=GRIS, label="Esperando (canal vacío)")], ncol=3, fontsize=8, loc="upper center",
              bbox_to_anchor=(.5, -.42))
    ax.grid(axis="x", alpha=.3)
    fig.tight_layout(); fig.savefig("fig_linea_tiempo.png", dpi=170); plt.close(fig)


if __name__ == "__main__":
    main()
