from flask import Flask, render_template, request, jsonify
from collections import deque
import os, time
from datetime import datetime

app = Flask(__name__)

# Buffer en memoria (últimas 1000 muestras): cada item = [t_ms, x, y, z]
datos = deque(maxlen=1000)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data")
def data():
    """Devuelve el buffer para la GUI (lista de listas)."""
    return jsonify(list(datos))

def append_line(ln: str):
    """Parsea línea 't;x;y;z' (admite coma decimal) y la añade al buffer."""
    ln = ln.strip()
    if not ln or ln.startswith("Tiempo"):
        return
    partes = ln.split(";")
    if len(partes) != 4:
        return
    t_ms = int(partes[0])
    # Normaliza coma decimal a punto para float() en Python
    x = float(partes[1].replace(",", "."))
    y = float(partes[2].replace(",", "."))
    z = float(partes[3].replace(",", "."))
    datos.append([t_ms, round(x, 2), round(y, 2), round(z, 2)])

@app.route("/add_batch", methods=["POST"])
def add_batch():
    """Ingesta por lotes: body text/plain con varias líneas separadas por \\n."""
    raw = request.get_data(as_text=True) or ""
    for ln in raw.splitlines():
        try:
            append_line(ln)
        except Exception:
            # Ignorar líneas defectuosas en lote
            continue
    return "ok", 200

@app.route("/exportar")
def exportar_csv():
    """Exporta el buffer actual a CSV (separador ';')."""
    carpeta_salida = "/home/adri/flask/datos/originales/"
    os.makedirs(carpeta_salida, exist_ok=True)
    timestamp = datetime.now().strftime("golpe_%Y-%m-%d_%H-%M-%S.csv")
    ruta_completa = os.path.join(carpeta_salida, timestamp)

    with open(ruta_completa, "w", encoding="utf-8") as f:
        f.write("Tiempo(ms);X(m/s²);Y(m/s²);Z(m/s²)\n")
        for t, x, y, z in list(datos):
            f.write(f"{t};{x:.2f};{y:.2f};{z:.2f}\n")

    return jsonify({"status": "exportado", "archivo": ruta_completa})

if __name__ == "__main__":
    # Sin reloader/debug para evitar doble proceso y colas
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False, threaded=True)
