


import json
import os
import socket
import urllib.request

NOMBRE = "AMYS"

CLAUDE_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODELO = "claude-sonnet-5-5"
OLLAMA_MODELO = "llama3.2:1b"

PERSONALIDAD = (
    f"Eres {NOMBRE}, asistente personal de Juan. "
    "Hablas en espanol, de forma directa y concisa."
)


def hay_internet():
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=2).close()
        return True
    except OSError:
        return False


def _enviar(url, datos, cabeceras):
    peticion = urllib.request.Request(
        url, data=json.dumps(datos).encode("utf-8"), headers=cabeceras
    )
    with urllib.request.urlopen(peticion, timeout=60) as respuesta:
        return json.loads(respuesta.read().decode("utf-8"))


def cerebro_nube(historial):
    if not CLAUDE_API_KEY:
        raise RuntimeError("Falta la clave de Claude")
    r = _enviar(
        "https://api.anthropic.com/v1/messages",
        {
            "model": CLAUDE_MODELO,
            "max_tokens": 1024,
            "system": PERSONALIDAD,
            "messages": historial,
        },
        {
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    return r["content"][0]["text"]


def cerebro_local(historial):
    mensajes = [{"role": "system", "content": PERSONALIDAD}] + historial
    r = _enviar(
        "http://localhost:11434/api/chat",
        {"model": OLLAMA_MODELO, "messages": mensajes, "stream": False},
        {"content-type": "application/json"},
    )
    return r["message"]["content"]


def cerebro_basico(texto):
    t = texto.lower()
    if "hola" in t:
        return f"Hola Juan, soy {NOMBRE}."
    if "hora" in t:
        from datetime import datetime
        return "Son las " + datetime.now().strftime("%H:%M")
    return "No tengo un cerebro de IA conectado todavia, pero te escucho."


def responder(historial):
    if hay_internet():
        try:
            return cerebro_nube(historial), "nube"
        except Exception:
            pass
    try:
        return cerebro_local(historial), "local"
    except Exception:
        return cerebro_basico(historial[-1]["content"]), "basico"


def main():
    print(f"{NOMBRE} listo. Escribe 'salir' para terminar.\n")
    historial = []
    while True:
        texto = input("Tu: ").strip()
        if texto.lower() in ("salir", "exit"):
            print(f"{NOMBRE}: Hasta luego, Juan.")
            break
        if not texto:
            continue
        historial.append({"role": "user", "content": texto})
        respuesta, modo = responder(historial)
        historial.append({"role": "assistant", "content": respuesta})
        print(f"{NOMBRE} [{modo}]: {respuesta}\n")


if __name__ == "__main__":
    main()
