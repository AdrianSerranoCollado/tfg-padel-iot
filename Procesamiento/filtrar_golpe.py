import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import os
import subprocess

CARPETA_FILTRADOS = "/home/adri/flask/datos/filtrados/"
CARPETA_COMPLETOS = "/home/adri/flask/datos/completos/"

# Crear carpetas si no existen
os.makedirs(CARPETA_FILTRADOS, exist_ok=True)
os.makedirs(CARPETA_COMPLETOS, exist_ok=True)

def cargar_y_recortar_golpe(path, ventana=5, muestras_antes=30, muestras_despues=30):  #15
    df = pd.read_csv(path, delimiter=';', names=['Tiempo(ms)', 'X(m/s²)', 'Y(m/s²)', 'Z(m/s²)'], skiprows=1)
    df = df.apply(pd.to_numeric, errors='coerce').dropna()

    df['magnitud'] = np.sqrt(df['X(m/s²)']**2 + df['Y(m/s²)']**2 + df['Z(m/s²)']**2)
    df['suavizado'] = df['magnitud'].rolling(window=ventana, center=True).mean()
    df = df.dropna().reset_index(drop=True)

    idx_pico = df['suavizado'].idxmax()
    inicio = max(0, idx_pico - muestras_antes)
    fin = min(len(df), idx_pico + muestras_despues)

    if fin - inicio < (muestras_antes + muestras_despues):
        print("⚠️ Aviso: no se han podido extraer todas las muestras esperadas.")

    df_recorte = df.iloc[inicio:fin].copy()

    df_recorte['normalizado'] = (df_recorte['suavizado'] - df_recorte['suavizado'].mean()) / df_recorte['suavizado'].std()

    return df_recorte



def main(path):
    df_golpe = cargar_y_recortar_golpe(path)

    print(f"\n📄 Muestras extraídas: {len(df_golpe)}")
    print(f"🕒 Tiempo del primer sample: {df_golpe['Tiempo(ms)'].iloc[0]} ms")


    # Nombre base del archivo (sin path y sin extensión)
    base = os.path.splitext(os.path.basename(path))[0]

    # Guardar filtrado simple
    ruta_simple = os.path.join(CARPETA_FILTRADOS, base + "_golpe_filtrado.csv")
    df_simple = df_golpe[['Tiempo(ms)', 'X(m/s²)', 'Y(m/s²)', 'Z(m/s²)']]
    df_simple.to_csv(ruta_simple, sep=';', index=False)

    # Guardar completo
    ruta_completo = os.path.join(CARPETA_COMPLETOS, base + "_procesado_completo.csv")
    df_golpe.to_csv(ruta_completo, sep=';', index=False)

    print(f"✅ Guardado limpio en: {ruta_simple}")
    print(f"✅ Guardado completo en: {ruta_completo}")

    # Llamar a graficar_procesado.py
    print("📊 Generando gráfica...")
    subprocess.run(["python3", "/home/adri/flask/graficar_procesado.py", os.path.basename(ruta_completo)])


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python filtrar_golpe.py archivo.csv")
    else:
        main(sys.argv[1])
