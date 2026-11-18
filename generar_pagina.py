"""Genera index.html (laboratorio interactivo para GitHub Pages) con los datos medidos de la práctica."""
import csv
import html

cap = list(csv.DictReader(open("capacidad.csv", encoding="utf-8")))
cue = list(csv.DictReader(open("cuellos.csv", encoding="utf-8")))
demo = html.escape(open("salida_demo.txt", encoding="utf-8").read())

filas_cap = "".join(
    f"<tr><td>{c['capacidad']}</td><td>{float(c['secuencial_ms']):.0f}</td><td>{float(c['pipeline_ms']):.1f}</td>"
    f"<td>{float(c['acel']):.2f}×</td><td>{float(c['bloq_prod_ms']):.1f}</td><td>{float(c['espera_acum_ms']):.1f}</td></tr>" for c in cap)
LIM = {"Balanceado (10/10/10 ms)": 3.0, "Cuello medio (5/15/5 ms)": 25 / 15, "Cuello fuerte (5/30/5 ms)": 40 / 30}
filas_cue = "".join(
    f"<tr><td>{c['escenario']}</td><td>{float(c['secuencial_ms']):.0f}</td><td>{float(c['pipeline_ms']):.1f}</td>"
    f"<td>{float(c['acel']):.2f}×</td><td>{LIM[c['escenario']]:.2f}×</td></tr>" for c in cue)

PLANTILLA = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Modelos de concurrencia (CSP) · laboratorio interactivo</title>
<style>
:root{--bg:#f7f9fc;--fg:#1c2433;--card:#fff;--bd:#d5ddea;--ac:#1f3a5f;--ok:#1a9a78;--bl:#c0392b;--wt:#9aa5b1;--mut:#5b6678;--code:#f0f3f8}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#10151f;--fg:#e6ecf5;--card:#171e2b;--bd:#2a3447;--ac:#7fb0ff;--mut:#9aa7bb;--code:#0c111a}}
*{box-sizing:border-box}body{margin:0;font:16px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--fg)}
main{max-width:980px;margin:0 auto;padding:24px 16px 56px}
h1{font-size:1.7rem;margin:.2em 0}h2{font-size:1.25rem;margin:1.8em 0 .5em;color:var(--ac)}
a{color:var(--ac)}.mut{color:var(--mut)}.links{display:flex;flex-wrap:wrap;gap:8px 14px;margin:.8em 0}
.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:16px;margin:12px 0}
.ctl{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px 18px}
.ctl label{display:flex;flex-direction:column;font-size:.85rem;color:var(--mut)}.ctl b{color:var(--fg)}
input[type=range]{width:100%}
button{font:inherit;padding:8px 14px;border-radius:8px;border:1px solid var(--bd);background:var(--ac);color:#fff;cursor:pointer}
@media (prefers-color-scheme:dark){button{color:#0c111a}}
button.sec{background:transparent;color:var(--fg)}
.row{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
svg{width:100%;height:auto;display:block}svg text{fill:var(--fg);font-size:13px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-top:12px}
.stat{border:1px solid var(--bd);border-radius:10px;padding:8px 10px}.stat span{display:block;font-size:.78rem;color:var(--mut)}.stat b{font-size:1.15rem}
.leg{display:flex;gap:14px;flex-wrap:wrap;font-size:.85rem;margin-top:8px}.leg i{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:5px;vertical-align:-1px}
table{border-collapse:collapse;width:100%;font-size:.9rem;display:block;overflow-x:auto}th,td{border-bottom:1px solid var(--bd);padding:6px 10px;text-align:left;white-space:nowrap}th{color:var(--ac)}
pre{background:var(--code);border:1px solid var(--bd);border-radius:10px;padding:12px;overflow-x:auto;font-size:.78rem;line-height:1.4}
code{font-family:ui-monospace,Menlo,Consolas,monospace}
</style>
</head>
<body>
<main>
<h1>Modelos de concurrencia (CSP): laboratorio interactivo</h1>
<p>Pipeline de tres procesos secuenciales (<b>Productor → Calculador → Acumulador</b>) que solo se comunican por canales de <code>multiprocessing</code> con capacidad limitada. Mueve la capacidad del canal y el tiempo de cada etapa para ver quién se bloquea, quién espera y qué etapa fija el ritmo.</p>
<div class="links">
<a href="Practica7_CSP_Informe.pdf">📄 Informe (PDF)</a> <a href="csp_pipeline.py">🐍 csp_pipeline.py</a> <a href="experimento.py">🐍 experimento.py</a>
<a href="capacidad.csv">Resultados: capacidad (CSV)</a> <a href="cuellos.csv">Resultados: cuellos (CSV)</a> <a href="README.md">Cómo ejecutarlo</a>
</div>

<div class="card">
<div class="ctl">
<label>Mensajes: <b id="vn">8</b><input id="n" type="range" min="4" max="40" value="8"></label>
<label>Capacidad de cada canal: <b id="vc">2</b><input id="c" type="range" min="1" max="10" value="2"></label>
<label>Productor (ms): <b id="v1">5</b><input id="d1" type="range" min="1" max="40" value="5"></label>
<label>Calculador (ms): <b id="v2">15</b><input id="d2" type="range" min="1" max="40" value="15"></label>
<label>Acumulador (ms): <b id="v3">5</b><input id="d3" type="range" min="1" max="40" value="5"></label>
<label>Velocidad: <b id="vs">×1</b><input id="sp" type="range" min="-2" max="2" value="0"></label>
</div>
<div class="row"><button id="play">▶ Ejecutar</button><button id="rst" class="sec">Reiniciar</button></div>
</div>

<div class="card">
<svg id="lienzo" viewBox="0 0 900 250" role="img" aria-label="Animación del pipeline CSP"></svg>
<div class="leg"><span><i style="background:var(--ok)"></i>trabajando</span><span><i style="background:var(--bl)"></i>bloqueado (canal lleno)</span><span><i style="background:var(--wt)"></i>esperando (canal vacío)</span></div>
<div class="stats">
<div class="stat"><span>tiempo simulado</span><b id="st">0 ms</b></div>
<div class="stat"><span>total del pipeline</span><b id="sp1">–</b></div>
<div class="stat"><span>secuencial (n × suma)</span><b id="ss">–</b></div>
<div class="stat"><span>aceleración</span><b id="sa">–</b></div>
<div class="stat"><span>límite (suma ÷ máx)</span><b id="sl">–</b></div>
<div class="stat"><span>suma de cuadrados</span><b id="sc">–</b></div>
</div>
<p class="mut" style="font-size:.85rem">La animación es un <b>modelo</b> del pipeline (sin sobrecarga del sistema): el bloqueo de <code>put()</code> con canal lleno y de <code>get()</code> con canal vacío se calcula con la misma lógica del programa real. Los datos reales medidos con Python están más abajo.</p>
</div>

<h2>Mediciones reales con Python</h2>
<p class="mut">Mediana de 5 repeticiones, 40 mensajes, retardos 5/15/5 ms, 1 núcleo lógico en el equipo de prueba. El trabajo de cada etapa es <code>time.sleep</code> (espera simulada).</p>
<div class="card"><table>
<tr><th>Capacidad</th><th>Secuencial (ms)</th><th>Pipeline (ms)</th><th>Aceleración</th><th>Productor bloqueado (ms)</th><th>Acumulador esperando (ms)</th></tr>
__FILAS_CAP__
</table></div>
<p class="mut">Más capacidad no acelera: cambia <i>dónde</i> se acumula la espera. El ritmo lo fija la etapa más lenta.</p>
<div class="card"><table>
<tr><th>Escenario (productor/calculador/acumulador)</th><th>Secuencial (ms)</th><th>Pipeline (ms)</th><th>Aceleración medida</th><th>Límite (suma/máx)</th></tr>
__FILAS_CUE__
</table></div>

<h2>Salida real del programa</h2>
<pre>$ python csp_pipeline.py

__DEMO__</pre>

<h2>El corazón del código</h2>
<pre>canal_a = ctx.Queue(maxsize=capacidad)       # canal con búfer acotado
canal_b = ctx.Queue(maxsize=capacidad)

def calculador(canal_a, canal_b, ...):
    while True:
        x = canal_a.get()                    # se bloquea si el canal está vacío
        if x is None:                        # centinela: fin del flujo
            canal_b.put(None); return
        canal_b.put(x * x)                   # se bloquea si el canal está lleno</pre>

<p class="mut" style="margin-top:2em">Práctica 7 · Programación paralela y concurrente · CUCEI. Modelo de la animación: cada mensaje i entra a una etapa cuando la etapa está libre y tiene el dato, y sale hacia el canal cuando hay lugar (capacidad c); por eso un canal lleno bloquea al emisor y uno vacío hace esperar al receptor.</p>
</main>

<script>
const $ = id => document.getElementById(id);
const P = {n:8, c:2, d:[5,15,5]};
let T = [], total = 0, t = 0, run = false, last = 0;
const SVG = 'http://www.w3.org/2000/svg';

function simular(){
  const {n, c} = P, [d1, d2, d3] = P.d;
  const S1=[],E1=[],D1=[],G2=[],E2=[],D2=[],G3=[],E3=[];
  for(let i=0;i<n;i++){
    S1[i] = i ? D1[i-1] : 0;           E1[i] = S1[i] + d1;
    D1[i] = Math.max(E1[i], i>=c ? G2[i-c] : 0);                 // put en canal A: espera lugar
    G2[i] = Math.max(i ? D2[i-1] : 0, D1[i]);  E2[i] = G2[i] + d2;
    D2[i] = Math.max(E2[i], i>=c ? G3[i-c] : 0);                 // put en canal B: espera lugar
    G3[i] = Math.max(i ? E3[i-1] : 0, D2[i]);  E3[i] = G3[i] + d3;
  }
  T = {S1,E1,D1,G2,E2,D2,G3,E3};
  total = E3[n-1];
  const sec = n*(d1+d2+d3), lim = (d1+d2+d3)/Math.max(d1,d2,d3);
  $('sp1').textContent = total.toFixed(0)+' ms'; $('ss').textContent = sec+' ms';
  $('sa').textContent = (sec/total).toFixed(2)+'×'; $('sl').textContent = lim.toFixed(2)+'×';
  let s=0; for(let i=1;i<=n;i++) s+=i*i; $('sc').textContent = s.toLocaleString('es-MX');
}

function estado(t){
  const {n}=P, {S1,E1,D1,G2,E2,D2,G3,E3}=T, r={p:'fin',c:'espera',a:'espera'}, A=[], B=[];
  for(let i=0;i<n;i++){
    if(t>=S1[i]&&t<E1[i]) r.p='trabaja'; else if(t>=E1[i]&&t<D1[i]) r.p='bloq';
    else if(i===0&&t<S1[0]) r.p='trabaja';
    if(t>=G2[i]&&t<E2[i]) r.c='trabaja'; else if(t>=E2[i]&&t<D2[i]) r.c='bloq';
    if(t>=G3[i]&&t<E3[i]) r.a='trabaja';
    if(t>=D1[i]&&t<G2[i]) A.push(i+1);
    if(t>=D2[i]&&t<G3[i]) B.push(i+1);
  }
  if(t>=E3[n-1]) r.a='fin';
  if(t>=D2[n-1]&&t<G3[n-1]&&0) r.c='fin';
  if(t>=E2[n-1]&&t>=D2[n-1]) r.c = (t>=E3[n-1])?'fin':(r.c==='trabaja'?'trabaja':'fin');
  if(t>=D1[n-1]&&r.p!=='trabaja'&&r.p!=='bloq') r.p='fin';
  return {r,A,B};
}

const COL = {trabaja:'var(--ok)', bloq:'var(--bl)', espera:'var(--wt)', fin:'var(--wt)'};
const TXT = {trabaja:'trabajando', bloq:'bloqueado', espera:'esperando', fin:'terminó'};
function el(tag, attrs, txt){const e=document.createElementNS(SVG,tag);for(const k in attrs)e.setAttribute(k,attrs[k]);if(txt!==undefined)e.textContent=txt;return e;}

function dibujar(){
  const {r,A,B} = estado(Math.min(t,total)), L=$('lienzo'); L.replaceChildren();
  const cajas=[[20,'Productor',r.p],[340,'Calculador',r.c],[660,'Acumulador',r.a]];
  for(const [x,nom,e] of cajas){
    L.append(el('rect',{x,y:60,width:220,height:90,rx:12,fill:COL[e],opacity:.9}));
    L.append(el('text',{x:x+110,y:98,'text-anchor':'middle',style:'fill:#fff;font-weight:700;font-size:16px'},nom));
    L.append(el('text',{x:x+110,y:124,'text-anchor':'middle',style:'fill:#fff'},TXT[e]));
  }
  [[240,'canal A',A],[560,'canal B',B]].forEach(([x,nom,items])=>{
    const c=P.c, w=100/c, y0=88;
    L.append(el('text',{x:x+50,y:50,'text-anchor':'middle'},nom+' (capacidad '+c+')'));
    L.append(el('rect',{x,y:y0,width:100,height:34,rx:6,fill:'none',stroke:'var(--bd)','stroke-width':2}));
    for(let k=0;k<c;k++) L.append(el('rect',{x:x+k*w+2,y:y0+3,width:Math.max(w-4,2),height:28,rx:4,fill:k<items.length?'var(--ac)':'none',opacity:k<items.length?.85:1,stroke:'var(--bd)'}));
    items.forEach((m,k)=>{ if(w>=14) L.append(el('text',{x:x+k*w+w/2,y:y0+22,'text-anchor':'middle',style:'fill:#fff;font-size:11px;font-weight:700'},m)); });
    if(items.length===c) L.append(el('text',{x:x+50,y:152,'text-anchor':'middle',style:'fill:var(--bl)'},'lleno'));
    else if(items.length===0) L.append(el('text',{x:x+50,y:152,'text-anchor':'middle',style:'fill:var(--mut)'},'vacío'));
  });
  const tp=Math.min(t,total), W=860;
  L.append(el('rect',{x:20,y:200,width:W,height:8,rx:4,fill:'none',stroke:'var(--bd)'}));
  L.append(el('rect',{x:20,y:200,width:W*tp/total,height:8,rx:4,fill:'var(--ac)'}));
  L.append(el('text',{x:20,y:232},'0 ms')); L.append(el('text',{x:880,y:232,'text-anchor':'end'},total.toFixed(0)+' ms'));
  $('st').textContent = tp.toFixed(0)+' ms';
}

function paso(ts){
  if(!run) return;
  const f = Math.pow(2, +$('sp').value);
  t += (ts-last)/25*f; last = ts;           // 1 ms simulado = 25 ms reales (a ×1)
  if(t>=total){ t=total; run=false; $('play').textContent='▶ Ejecutar'; }
  dibujar(); if(run) requestAnimationFrame(paso);
}
$('play').onclick = () => {
  if(run){ run=false; $('play').textContent='▶ Ejecutar'; return; }
  if(t>=total) t=0;
  run=true; last=performance.now(); $('play').textContent='⏸ Pausar'; requestAnimationFrame(paso);
};
function reiniciar(){ run=false; t=0; $('play').textContent='▶ Ejecutar'; simular(); dibujar(); }
$('rst').onclick = reiniciar;
[['n','vn'],['c','vc'],['d1','v1'],['d2','v2'],['d3','v3']].forEach(([i,v])=>{
  $(i).oninput = () => { $(v).textContent=$(i).value; P.n=+$('n').value; P.c=+$('c').value; P.d=[+$('d1').value,+$('d2').value,+$('d3').value]; reiniciar(); };
});
$('sp').oninput = () => { $('vs').textContent = '×'+Math.pow(2,+$('sp').value); };
simular(); dibujar();
</script>
</body>
</html>
"""

pagina = PLANTILLA.replace("__FILAS_CAP__", filas_cap).replace("__FILAS_CUE__", filas_cue).replace("__DEMO__", demo.rstrip("\n"))
open("index.html", "w", encoding="utf-8").write(pagina)
print("OK index.html", len(pagina), "bytes")
