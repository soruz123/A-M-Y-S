"""AMYS - interfaz visual estilo Jarvis, con voz y micrófono."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from amys import responder

PAGINA = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AMYS</title>
<style>
  :root { --c:#b57bff; --c2:#7a3fd1; --g:#ffd23f; --bg:#0B0C10; }
  body[data-modo="escuchando"] { --c:#ffd23f; --c2:#d9a800; }
  * { box-sizing:border-box; }
  body { margin:0; height:100vh; overflow:hidden; color:#e6dcff;
         font-family:'Courier New', monospace;
         background:radial-gradient(circle at 30% 50%, #1a1030, #0B0C10 70%); }
  #app { display:grid; grid-template-columns:1fr 430px;
         grid-template-rows:60px 1fr; height:100vh; }
  header { grid-column:1 / 3; display:flex; align-items:center;
           justify-content:space-between; padding:0 24px;
           border-bottom:1px solid var(--c2); }
  h1 { margin:0; color:var(--c); letter-spacing:10px; font-size:22px;
       text-shadow:0 0 12px var(--c); }
  #estado { color:var(--c2); font-size:12px; letter-spacing:2px; }
  #reloj { color:var(--g); font-size:14px; letter-spacing:2px; }
  #hud { display:flex; flex-direction:column; align-items:center;
         justify-content:center; position:relative; }
  #hud svg { width:min(80%, 70vh); height:auto;
             filter:drop-shadow(0 0 14px var(--c2)); }
  #leyenda { margin-top:6px; color:var(--c); letter-spacing:6px;
             font-size:13px; text-transform:uppercase; }
  .gira { transform-box:fill-box; transform-origin:center; }
  .r1 { animation:gira 24s linear infinite; }
  .r2 { animation:gira 14s linear infinite reverse; }
  .r3 { animation:gira 18s linear infinite; }
  body[data-modo="pensando"] .r1 { animation-duration:3s; }
  body[data-modo="pensando"] .r2 { animation-duration:2s; }
  body[data-modo="pensando"] .r3 { animation-duration:4s; }
  body[data-modo="escuchando"] .r1 { animation-duration:8s; }
  #nucleo { transform-box:fill-box; transform-origin:center;
            animation:pulso 3.2s ease-in-out infinite; }
  body[data-modo="hablando"] #nucleo { animation:pulso 0.55s ease-in-out infinite; }
  body[data-modo="escuchando"] #nucleo { animation:pulso 1.1s ease-in-out infinite; }
  @keyframes gira { to { transform:rotate(360deg); } }
  @keyframes pulso { 0%,100% { transform:scale(1); opacity:0.75; }
                     50% { transform:scale(1.18); opacity:1; } }
  #panel { display:flex; flex-direction:column; min-height:0;
           border-left:1px solid var(--c2); background:rgba(18,10,32,0.75); }
  #chat { flex:1; overflow-y:auto; padding:18px; }
  .msg { padding:10px 12px; margin:10px 0; line-height:1.45;
         white-space:pre-wrap; font-size:14px;
         border-left:3px solid var(--c2); background:rgba(35,20,60,0.7); }
  .yo { border-left-color:var(--g); color:#f1e3b0; }
  .amys { border-left-color:var(--c); }
  footer { display:flex; gap:8px; padding:14px; border-top:1px solid var(--c2); }
  input { flex:1; min-width:0; padding:11px; background:#140c24; color:#fff;
          border:1px solid var(--c2); font-family:inherit; font-size:14px; }
  button { padding:11px 14px; background:transparent; color:var(--c);
           border:1px solid var(--c); font-family:inherit; font-size:13px;
           letter-spacing:1px; cursor:pointer; }
  button:hover { background:var(--c); color:#0B0C10; }
  #mic.activo { border-color:var(--g); color:var(--g); }
  @media (max-width:820px) {
    #app { grid-template-columns:1fr; grid-template-rows:56px 230px 1fr; }
    header { grid-column:1; }
    #hud svg { width:auto; height:190px; }
    #panel { border-left:none; border-top:1px solid var(--c2); }
  }
</style>
</head>
<body data-modo="reposo">
<div id="app">
  <header>
    <h1>AMYS</h1>
    <div id="estado">CEREBRO: EN ESPERA</div>
    <div id="reloj"></div>
  </header>
  <section id="hud">
    <svg viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <radialGradient id="brillo">
          <stop offset="0%" stop-color="#ffffff"/>
          <stop offset="35%" stop-color="var(--c)"/>
          <stop offset="100%" stop-color="var(--c)" stop-opacity="0"/>
        </radialGradient>
      </defs>
      <g class="gira r1" id="marcas"></g>
      <g class="gira r2">
        <circle cx="200" cy="200" r="150" fill="none" stroke="var(--c)"
                stroke-width="3" stroke-dasharray="90 40 30 40"/>
      </g>
      <g class="gira r3">
        <circle cx="200" cy="200" r="120" fill="none" stroke="var(--g)"
                stroke-width="2" stroke-dasharray="4 10"/>
        <circle cx="200" cy="200" r="100" fill="none" stroke="var(--c2)"
                stroke-width="5" stroke-dasharray="150 60"/>
      </g>
      <circle cx="200" cy="200" r="72" fill="none" stroke="var(--c)"
              stroke-width="1.5"/>
      <circle id="nucleo" cx="200" cy="200" r="58" fill="url(#brillo)"/>
      <circle cx="200" cy="200" r="22" fill="#ffffff" opacity="0.9"/>
    </svg>
    <div id="leyenda">Sistema en reposo</div>
  </section>
  <section id="panel">
    <div id="chat"></div>
    <footer>
      <button id="mic" onclick="escuchar()">MIC</button>
      <input id="texto" placeholder="Habla o escribe, Samuel...">
      <button onclick="enviar()">ENVIAR</button>
    </footer>
  </section>
</div>
<script>
const historial = [];
const chat = document.getElementById('chat');
const caja = document.getElementById('texto');
const estado = document.getElementById('estado');
const leyenda = document.getElementById('leyenda');
const botonMic = document.getElementById('mic');

const TEXTOS = {
  reposo: 'Sistema en reposo',
  pensando: 'Procesando',
  hablando: 'Respondiendo',
  escuchando: 'Te escucho'
};

function modo(m) {
  document.body.setAttribute('data-modo', m);
  leyenda.textContent = TEXTOS[m];
}

// Marcas del anillo exterior
(function() {
  const g = document.getElementById('marcas');
  const NS = 'http://www.w3.org/2000/svg';
  for (let i = 0; i < 72; i++) {
    const a = (i / 72) * Math.PI * 2;
    const largo = i % 6 === 0 ? 16 : 7;
    const l = document.createElementNS(NS, 'line');
    l.setAttribute('x1', 200 + Math.cos(a) * 185);
    l.setAttribute('y1', 200 + Math.sin(a) * 185);
    l.setAttribute('x2', 200 + Math.cos(a) * (185 - largo));
    l.setAttribute('y2', 200 + Math.sin(a) * (185 - largo));
    l.setAttribute('stroke', 'var(--c2)');
    l.setAttribute('stroke-width', i % 6 === 0 ? 2.5 : 1);
    g.appendChild(l);
  }
})();

// Reloj
function reloj() {
  document.getElementById('reloj').textContent =
    new Date().toLocaleTimeString('es-CO');
}
reloj();
setInterval(reloj, 1000);

function agregar(clase, texto) {
  const d = document.createElement('div');
  d.className = 'msg ' + clase;
  d.textContent = texto;
  chat.appendChild(d);
  chat.scrollTop = chat.scrollHeight;
  return d;
}

function hablar(t) {
  const v = new SpeechSynthesisUtterance(t);
  v.lang = 'es-ES';
  v.onstart = function() { modo('hablando'); };
  v.onend = function() { modo('reposo'); };
  v.onerror = function() { modo('reposo'); };
  speechSynthesis.cancel();
  speechSynthesis.speak(v);
}

function escuchar() {
  const Reco = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Reco) {
    agregar('amys', 'Este navegador no soporta el microfono. Usa Chrome o Edge.');
    return;
  }
  const r = new Reco();
  r.lang = 'es-ES';
  r.onstart = function() {
    botonMic.classList.add('activo');
    botonMic.textContent = 'ESCUCHANDO';
    modo('escuchando');
  };
  r.onend = function() {
    botonMic.classList.remove('activo');
    botonMic.textContent = 'MIC';
    if (document.body.getAttribute('data-modo') === 'escuchando') modo('reposo');
  };
  r.onerror = function(e) { agregar('amys', 'No pude escucharte (' + e.error + ').'); };
  r.onresult = function(e) {
    caja.value = e.results[0][0].transcript;
    enviar();
  };
  r.start();
}

async function enviar() {
  const t = caja.value.trim();
  if (!t) return;
  caja.value = '';
  agregar('yo', t);
  historial.push({role: 'user', content: t});
  const espera = agregar('amys', 'Procesando...');
  modo('pensando');
  try {
    const r = await fetch('/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({historial: historial})
    });
    const d = await r.json();
    espera.textContent = d.respuesta;
    historial.push({role: 'assistant', content: d.respuesta});
    estado.textContent = 'CEREBRO: ' + d.modo.toUpperCase();
    hablar(d.respuesta);
  } catch (e) {
    espera.textContent = 'Error de conexion';
    historial.pop();
    modo('reposo');
  }
}

caja.addEventListener('keydown', function(e) {
  if (e.key === 'Enter') enviar();
});
</script>
</body>
</html>"""


class Manejador(BaseHTTPRequestHandler):
    def do_GET(self):
        datos = PAGINA.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def do_POST(self):
        largo = int(self.headers.get("Content-Length", 0))
        cuerpo = json.loads(self.rfile.read(largo).decode("utf-8"))
        respuesta, modo = responder(cuerpo["historial"])
        datos = json.dumps(
            {"respuesta": respuesta, "modo": modo}
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print("AMYS visual encendida en el puerto 8000")
    ThreadingHTTPServer(("0.0.0.0", 8000), Manejador).serve_forever()