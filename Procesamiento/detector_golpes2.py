import time
import requests
import subprocess
import os

FLASK_URL = "http://localhost:5000/data"
EXPORTAR_URL = "http://localhost:5000/exportar"

UMBRAL_MAGNITUD = 17.0
VENTANA_ESPERA = 2.5
INTERVALO_CONSULTA = 0.2

def calcular_magnitud(x, y, z):
    return (x**2 + y**2 + z**2) ** 0.5

print("🟢 Iniciando detector de golpes...")

golpe_detectado = False
ultimo_tiempo_golpe = 0

while True:
    try:
        response = requests.get(FLASK_URL, timeout=2)
        datos = response.json()

        if not datos:
            time.sleep(INTERVALO_CONSULTA)
            continue

        tiempo, x, y, z = datos[-1]
        magnitud = calcular_magnitud(x, y, z)
        print(f"📈 {tiempo} ms | X: {x:.2f}, Y: {y:.2f}, Z: {z:.2f} | M: {magnitud:.2f}")

        if magnitud > UMBRAL_MAGNITUD and not golpe_detectado:
            golpe_detectado = True
            ultimo_tiempo_golpe = time.time()
            print("💥 Golpe detectado. Esperando para exportar...")

        if golpe_detectado and time.time() - ultimo_tiempo_golpe > VENTANA_ESPERA:
            print("💾 Exportando CSV automáticamente...")
            r = requests.get(EXPORTAR_URL)
            if r.status_code == 200:
                ruta_completa = r.json().get("archivo")
                if ruta_completa:
                    print(f"✅ Exportado: {ruta_completa}")
                    
                    # Ejecutar filtrar_golpe.py con la ruta
                    subprocess.run(["python3", "/home/adri/flask/filtrar_golpe.py", ruta_completa])
                else:
                    print("❌ No se recibió ruta de archivo")
            else:
                print("❌ Error exportando CSV")

            golpe_detectado = False

        time.sleep(INTERVALO_CONSULTA)

    except Exception as e:
        print("⚠️ Error:", e)
        time.sleep(1)
