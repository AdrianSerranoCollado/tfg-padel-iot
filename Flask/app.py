from flask import Flask, render_template, request, jsonify
from collections import deque
import os, time
from datetime import datetime

app = Flask(__name__)

# BUFFER en memoria (últimos 200)
datos = deque(maxlen=1000)  # cada item: [t_ms, x, y, z]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def data():
    # Mantenemos el formato que espera tu front-end: lista de listas
    return jsonify(list(datos))

def append_line(ln: str):
    """Parsea línea CSV 't;x;y;z' (coma decimal admitida) y la añade al buffer."""
    ln = ln.strip()
    if not ln or ln.startswith("Tiempo"):
        return
    partes = ln.split(';')
    if len(partes) != 4:
        return
    t_ms = int(partes[0])
    x = float(partes[1].replace(',', '.'))
    y = float(partes[2].replace(',', '.'))
    z = float(partes[3].replace(',', '.'))
    datos.append([t_ms, round(x, 2), round(y, 2), round(z, 2)])

# @app.route('/add', methods=['POST'])
# def add_data():
#     contenido = request.json
#     if not contenido or 'line' not in contenido:
#         return jsonify({"status": "missing data"}), 400
#     try:
#         append_line(contenido['line'])
#         return jsonify({"status": "ok"}), 200
#     except Exception:
#         return jsonify({"status": "bad format"}), 400

@app.route('/add_batch', methods=['POST'])
def add_batch():
    """Ingesta por lotes: body de texto con varias líneas separadas por \n."""
    raw = request.get_data(as_text=True) or ""
    for ln in raw.splitlines():
        try:
            append_line(ln)
        except Exception:
            # ignoramos líneas defectuosas en lote
            continue
    return "ok", 200

@app.route('/exportar')
def exportar_csv():
    carpeta_salida = "/home/adri/flask/datos/originales/"
    os.makedirs(carpeta_salida, exist_ok=True)
    timestamp = datetime.now().strftime("golpe_%Y-%m-%d_%H-%M-%S.csv")
    ruta_completa = os.path.join(carpeta_salida, timestamp)

    with open(ruta_completa, 'w', encoding='utf-8') as f:
        f.write("Tiempo(ms);X(m/s²);Y(m/s²);Z(m/s²)\n")
        for t, x, y, z in list(datos):
            f.write(f"{t};{x:.2f};{y:.2f};{z:.2f}\n")

    return jsonify({"status": "exportado", "archivo": ruta_completa})

if __name__ == '__main__':
    # IMPORTANTE: sin reloader/debug para evitar doble proceso y colas
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, threaded=True)
