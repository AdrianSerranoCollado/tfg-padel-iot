import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import pearsonr
from scipy.spatial.distance import euclidean
from scipy.interpolate import interp1d
from dtaidistance import dtw
import sys

BASE_DATOS_DIR = "/home/adri/flask/base_datos/"
GOLPE_DIR = "/home/adri/flask/datos/completos/"

def cargar_normalizado(path):
    df = pd.read_csv(path, sep=';')
    if 'normalizado' not in df.columns:
        raise ValueError(f"⚠️ El archivo '{path}' no contiene columna 'normalizado'")
    return df['normalizado'].values

def igualar_longitudes(sig1, sig2, target_len=200):
    def interpolar(s, n):
        x_old = np.linspace(0, 1, len(s))
        f = interp1d(x_old, s, kind='linear')
        x_new = np.linspace(0, 1, n)
        return f(x_new)
    return interpolar(sig1, target_len), interpolar(sig2, target_len)

def comparar(s1, s2):
    correlacion, _ = pearsonr(s1, s2)
    dist_euclid = euclidean(s1, s2)
    dist_dtw = dtw.distance(s1, s2)
    return correlacion, dist_euclid, dist_dtw

def identificar_golpe(golpe_nuevo_nombre):
    ruta_golpe_nuevo = os.path.join(GOLPE_DIR, golpe_nuevo_nombre)
    golpe_nuevo = cargar_normalizado(ruta_golpe_nuevo)

    mejor_categoria = None
    mejor_archivo = None
    mejor_dtw = float("inf")
    mejor_correlacion = -1
    golpe_nuevo_interp = None

    for categoria in os.listdir(BASE_DATOS_DIR):
        carpeta_categoria = os.path.join(BASE_DATOS_DIR, categoria)
        if not os.path.isdir(carpeta_categoria):
            continue

        for archivo in os.listdir(carpeta_categoria):
            if not archivo.endswith(".csv"):
                continue
            path_archivo = os.path.join(carpeta_categoria, archivo)
            try:
                golpe_bd = cargar_normalizado(path_archivo)
                golpe_nuevo_eq, golpe_bd_eq = igualar_longitudes(golpe_nuevo, golpe_bd)
                corr, dist_euc, dist_dtw = comparar(golpe_nuevo_eq, golpe_bd_eq)

                print(f"🆚 {archivo} ({categoria}) → Pearson: {corr:.3f}, Euclidea: {dist_euc:.2f}, DTW: {dist_dtw:.2f}")

                if dist_dtw < mejor_dtw:
                    mejor_dtw = dist_dtw
                    mejor_correlacion = corr
                    mejor_categoria = categoria
                    mejor_archivo = archivo
                    golpe_nuevo_interp = golpe_nuevo_eq
                    golpe_bd_mejor = golpe_bd_eq

            except Exception as e:
                print(f"❌ Error comparando con {archivo}: {e}")

    if mejor_categoria:
        print(f"\n✅ El golpe es más similar a la categoría: **{mejor_categoria}**")
        print(f"🏷️ Archivo más similar: {mejor_archivo}")
        print(f"🔄 DTW: {mejor_dtw:.2f} | 🔗 Pearson: {mejor_correlacion:.3f}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python identificar_golpe.py golpe_nuevo.csv")
    else:
        identificar_golpe(sys.argv[1])
