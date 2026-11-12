"""AMYS - Paso 5: ventana visual en el navegador."""

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
  body { margin:0; background:#0B0C10; color:#e8e8e8;
         font-family:Arial, sans-serif; display:flex;
         flex-direction:column; height:100vh; }
  header { padding:16px 24px; border-bottom:1px solid #D4AF37; }
  h1 { margin:0; color:#D4AF37; letter-spacing:6px; font-size:24px; }
  #estado { color:#45A29E; font-size:13px; margin-top:4px; }
  #chat { flex:1; overflow-y:auto; padding:20px 24px; }
  .msg { max-width:75%; padding:10px 14px; margin:8px 0;
         border-radius:10px; line-height:1.4; white-space:pre-wrap; }
  .yo { background:#1f2833; margin-left:auto; border:1px solid #45A29E; }
  .amys { background:#14161c; border:1px solid #D4AF37; }
  footer { display:flex; gap:10px; padding:16px 24px;
           border-top:1px solid #D4AF37; }
  input { flex:1; padding:12px; background:#14161c; color:#fff;
          border:1px solid #45A29E; border-radius:8px; font-size:16px; }
  button { padding:12px 22px; background:#D4AF37; color:#0B0C10;
           border:none; border-radius:8px; font-weight:bold;
           font-size:16px; cursor:pointer; }
</style>
</head>
<body>
<header>
  <h1>AMYS</h1>
  <div id="estado">Cerebro: en espera</div>
</header>
<div id="chat"></div>
<footer>
  <input id="texto" placeholder="Escribe aqui, Samuel..." autofocus>
  <button onclick="enviar()">Enviar</button>
</footer>
<script>
const historial = [];
const chat = document.getElementById('chat');
const caja = document.getElementById('texto');
const estado = document.getElementById('estado');

function agregar(clase, texto) {
  const d = document.createElement('div');
  d.className = 'msg ' + clase;
  d.textContent = texto;
  chat.appendChild(d);
  chat.scrollTop = chat.scrollHeight;
  return d;
}

function hablar(t) { const v = new SpeechSynthesisUtterance(t); v.lang = 'es-ES'; speechSynthesis.cancel(); speechSynthesis.speak(v); }
async function enviar() {
  const t = caja.value.trim();
  if (!t) return;
  caja.value = '';
  agregar('yo', t);
  historial.push({role: 'user', content: t});
  const espera = agregar('amys', 'Pensando...');
  try {
    const r = await fetch('/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({historial: historial})
    });
    const d = await r.json();
    espera.textContent = d.respuesta; hablar(d.respuesta);
    historial.push({role: 'assistant', content: d.respuesta});
    estado.textContent = 'Cerebro: ' + d.modo;
  } catch (e) {
    espera.textContent = 'Error de conexion';
    historial.pop();
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