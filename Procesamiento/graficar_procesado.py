import pandas as pd
import matplotlib.pyplot as plt
import sys
import os

BASE_PATH_DATOS = "/home/adri/flask/datos/completos/"
BASE_PATH_SALIDA = "/home/adri/flask/capturas/completos"

def main():
    if len(sys.argv) < 2:
        print("Uso: python graficar_procesado.py archivo.csv [nombre_salida.png]")
        sys.exit(1)

    nombre_archivo = sys.argv[1]
    nombre_salida = sys.argv[2] if len(sys.argv) == 3 else None

    # Ruta completa al CSV
    ruta_archivo = os.path.join(BASE_PATH_DATOS, nombre_archivo)
    if not os.path.exists(ruta_archivo):
        print(f"❌ El archivo '{ruta_archivo}' no existe.")
        sys.exit(1)

    # Cargar CSV
    df = pd.read_csv(ruta_archivo, sep=';')

    # Verificar columna de tiempo
    if 'Tiempo(ms)' not in df.columns:
        print("❌ El archivo no contiene la columna 'Tiempo(ms)'")
        sys.exit(1)

    # Convertir tiempo a segundos
    df['Tiempo(s)'] = df['Tiempo(ms)'] / 1000.0

    # Crear la gráfica
    plt.figure(figsize=(12, 6))
    for columna in ['X(m/s²)', 'Y(m/s²)', 'Z(m/s²)', 'magnitud', 'suavizado', 'normalizado']:
        if columna in df.columns:
            plt.plot(df['Tiempo(s)'], df[columna], label=columna)
        else:
            print(f"⚠️ Columna '{columna}' no encontrada en el archivo.")

    plt.title(f"Señales procesadas: {nombre_archivo}")
    plt.xlabel("Tiempo (s)")
    plt.ylabel("Aceleración / Magnitud / Normalizado")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    # Nombre y ruta de salida
    if not nombre_salida:
        base_name = os.path.splitext(nombre_archivo)[0]
        nombre_salida = os.path.join(BASE_PATH_SALIDA, base_name + "_grafica.png")
    else:
        nombre_salida = os.path.join(BASE_PATH_SALIDA, nombre_salida)

    # Guardar imagen
    plt.savefig(nombre_salida)
    print(f"✅ Gráfica guardada como '{nombre_salida}'")


if __name__ == "__main__":
    main()
