"""Práctica 7 · Modelos de concurrencia: CSP (Communicating Sequential Processes).

Pipeline de procesos secuenciales que SOLO se comunican por canales:

    Productor --canal A--> Calculador --canal B--> Acumulador
        \\___________ canal de eventos ___________/ --> Logger

* Cada proceso es secuencial y no comparte memoria con los demás.
* Los canales son multiprocessing.Queue(maxsize=capacidad): put() se BLOQUEA
  si el canal está lleno y get() se BLOQUEA si está vacío (sincronización).
* El fin del flujo se avisa con un mensaje centinela (None) por el mismo canal.
* El resultado final viaja por un multiprocessing.Pipe hacia el proceso principal.

Uso: python csp_pipeline.py            (8 mensajes, capacidad 2)
     python csp_pipeline.py -n 12 -c 1
"""
import argparse
import json
import multiprocessing as mp
import os
import time

N_MENSAJES = 8
CAPACIDAD = 2
# Tiempo de "trabajo" simulado por etapa (s): productor, calculador, acumulador
RETARDOS = (0.005, 0.015, 0.005)
FIN = None  # mensaje centinela: "no habrá más datos"


# --------------------------------------------------------------------------
# Utilidades de registro: cada proceso manda sus eventos al canal de eventos
# --------------------------------------------------------------------------
def evento(canal_ev, proceso, tipo, detalle="", dur=0.0, bloqueo=0.0, espera=0.0):
    canal_ev.put({"t": time.time(), "proceso": proceso, "pid": os.getpid(),
                  "tipo": tipo, "detalle": detalle, "dur": dur,
                  "bloqueo": bloqueo, "espera": espera})


def trabajar(segundos):
    """Simula el cálculo de una etapa; devuelve lo que realmente tardó."""
    t = time.perf_counter()
    time.sleep(segundos)
    return time.perf_counter() - t


# --------------------------------------------------------------------------
# Procesos secuenciales (cada uno solo conoce sus canales)
# --------------------------------------------------------------------------
def productor(canal_a, canal_ev, barrera, n, retardo):
    barrera.wait()                              # arrancan todos a la vez
    for i in range(1, n + 1):
        d = trabajar(retardo)
        evento(canal_ev, "Productor", "PRODUCE", f"dato {i}", dur=d)
        t = time.perf_counter()
        canal_a.put(i)                          # se bloquea si el canal A está lleno
        b = time.perf_counter() - t
        evento(canal_ev, "Productor", "ENVIA", f"{i} -> canal A", bloqueo=b)
    canal_a.put(FIN)
    evento(canal_ev, "Productor", "FIN", "centinela -> canal A")


def calculador(canal_a, canal_b, canal_ev, barrera, retardo):
    barrera.wait()
    while True:
        t = time.perf_counter()
        x = canal_a.get()                       # se bloquea si el canal A está vacío
        w = time.perf_counter() - t
        if x is FIN:
            evento(canal_ev, "Calculador", "FIN", "centinela <- canal A", espera=w)
            canal_b.put(FIN)
            return
        evento(canal_ev, "Calculador", "RECIBE", f"{x} <- canal A", espera=w)
        d = trabajar(retardo)
        y = x * x
        evento(canal_ev, "Calculador", "CALCULA", f"{x}^2 = {y}", dur=d)
        t = time.perf_counter()
        canal_b.put(y)                          # se bloquea si el canal B está lleno
        b = time.perf_counter() - t
        evento(canal_ev, "Calculador", "ENVIA", f"{y} -> canal B", bloqueo=b)


def acumulador(canal_b, canal_ev, barrera, retardo, conexion):
    barrera.wait()
    total = 0
    while True:
        t = time.perf_counter()
        y = canal_b.get()
        w = time.perf_counter() - t
        if y is FIN:
            evento(canal_ev, "Acumulador", "FIN", f"centinela <- canal B | total = {total}", espera=w)
            conexion.send(total)                # resultado por un Pipe hacia main
            return
        evento(canal_ev, "Acumulador", "RECIBE", f"{y} <- canal B", espera=w)
        d = trabajar(retardo)
        total += y
        evento(canal_ev, "Acumulador", "ACUMULA", f"total = {total}", dur=d)


def logger(canal_ev, conexion, mostrar, t0):
    """Proceso que serializa la salida: único dueño de la pantalla."""
    eventos = []
    while True:
        e = canal_ev.get()
        if e is FIN:
            break
        eventos.append(e)
        if mostrar:
            extra = ""
            if e["tipo"] == "ENVIA" and e["bloqueo"] > 1e-3:
                extra = f"  [bloqueado {e['bloqueo'] * 1000:.1f} ms: canal lleno]"
            if e["tipo"] in ("RECIBE", "FIN") and e["espera"] > 1e-3:
                extra = f"  [esperó {e['espera'] * 1000:.1f} ms: canal vacío]"
            print(f"[{e['t'] - t0.value:7.3f} s] {e['proceso']:<10} (pid {e['pid']}) "
                  f"{e['tipo']:<8} {e['detalle']}{extra}", flush=True)
    conexion.send(eventos)


# --------------------------------------------------------------------------
# Orquestación (proceso principal)
# --------------------------------------------------------------------------
def ejecutar(n=N_MENSAJES, capacidad=CAPACIDAD, retardos=RETARDOS, mostrar=False):
    ctx = mp.get_context("spawn")               # procesos independientes, sin memoria compartida
    canal_a = ctx.Queue(maxsize=capacidad)
    canal_b = ctx.Queue(maxsize=capacidad)
    canal_ev = ctx.Queue()
    res_rx, res_tx = ctx.Pipe(duplex=False)     # resultado del acumulador
    log_rx, log_tx = ctx.Pipe(duplex=False)     # eventos recopilados por el logger
    barrera = ctx.Barrier(4)                    # 3 procesos de trabajo + main
    t0 = ctx.Value("d", 0.0)                    # instante en que se libera la barrera
    r_prod, r_calc, r_acum = retardos

    procs = [
        ctx.Process(target=logger, args=(canal_ev, log_tx, mostrar, t0), name="Logger"),
        ctx.Process(target=acumulador, args=(canal_b, canal_ev, barrera, r_acum, res_tx), name="Acumulador"),
        ctx.Process(target=calculador, args=(canal_a, canal_b, canal_ev, barrera, r_calc), name="Calculador"),
        ctx.Process(target=productor, args=(canal_a, canal_ev, barrera, n, r_prod), name="Productor"),
    ]
    a0 = time.perf_counter()
    for p in procs:
        p.start()
    barrera.wait()                              # todos listos: empieza el trabajo real
    inicio = time.perf_counter()
    t0.value = time.time()
    arranque = inicio - a0                      # costo de crear los procesos (no es parte del flujo)
    total = res_rx.recv()                       # espera el resultado final
    duracion = time.perf_counter() - inicio
    for p in procs[1:]:
        p.join()
    canal_ev.put(FIN)                           # cierra el logger
    eventos = log_rx.recv()
    procs[0].join()
    for e in eventos:
        e["t"] -= t0.value

    def suma(proceso, campo):
        return sum(e[campo] for e in eventos if e["proceso"] == proceso)

    return {"total": total, "duracion": duracion, "arranque": arranque, "eventos": eventos,
            "bloqueo_prod": suma("Productor", "bloqueo"),
            "bloqueo_calc": suma("Calculador", "bloqueo"),
            "espera_calc": suma("Calculador", "espera"),
            "espera_acum": suma("Acumulador", "espera")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=N_MENSAJES, help="número de mensajes")
    ap.add_argument("-c", type=int, default=CAPACIDAD, help="capacidad de cada canal")
    args = ap.parse_args()

    print(f"Mensajes: {args.n} | Capacidad de canal: {args.c} | Núcleos: {os.cpu_count()} | "
          f"Procesos: 4 (Productor, Calculador, Acumulador, Logger)\n")
    print("=== BLOQUE 1: ejecución SECUENCIAL (referencia) ===")
    t = time.perf_counter()
    esperado = 0
    for i in range(1, args.n + 1):
        trabajar(RETARDOS[0]); trabajar(RETARDOS[1]); esperado += i * i; trabajar(RETARDOS[2])
    t_sec = time.perf_counter() - t
    print(f"Suma de cuadrados: {esperado:,}")
    print(f"--> Tiempo secuencial: {t_sec:.6f} s\n")

    print("=== BLOQUE 2: pipeline CSP (intercambio de mensajes) ===")
    r = ejecutar(args.n, args.c, mostrar=True)
    with open("eventos_demo.json", "w", encoding="utf-8") as f:
        json.dump(r["eventos"], f)              # lo usa experimento.py para la línea de tiempo
    print(f"\nSuma de cuadrados (por Pipe): {r['total']:,}")
    print(f"--> Tiempo pipeline CSP: {r['duracion']:.6f} s  (crear los procesos: {r['arranque']:.3f} s, aparte)\n")

    assert r["total"] == esperado == sum(i * i for i in range(1, args.n + 1)), "las sumas no coinciden"
    print("Verificación: el resultado del pipeline coincide con la versión secuencial.\n")

    print("=== TABLA COMPARATIVA ===")
    print(f"{'Versión':<24}{'Tiempo (s)':>14}")
    print(f"{'Secuencial':<24}{t_sec:>14.6f}")
    print(f"{'Pipeline CSP':<24}{r['duracion']:>14.6f}")
    print(f"{'Aceleración':<24}{t_sec / r['duracion']:>13.2f}x")
    print(f"\nBloqueo del Productor (canal A lleno):   {r['bloqueo_prod'] * 1000:8.1f} ms")
    print(f"Bloqueo del Calculador (canal B lleno):  {r['bloqueo_calc'] * 1000:8.1f} ms")
    print(f"Espera del Calculador (canal A vacío):   {r['espera_calc'] * 1000:8.1f} ms")
    print(f"Espera del Acumulador (canal B vacío):   {r['espera_acum'] * 1000:8.1f} ms")


if __name__ == "__main__":
    main()
