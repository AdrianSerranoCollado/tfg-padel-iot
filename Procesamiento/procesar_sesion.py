import os
import sys
import argparse
import numpy as np
import pandas as pd
import subprocess
import glob
import shutil
from pathlib import Path

CARPETA_FILTRADOS = "/home/adri/flask/datos/filtrados/"
CARPETA_COMPLETOS = "/home/adri/flask/datos/completos/"
CARPETA_PNGS      = "/home/adri/flask/capturas/completos/"
os.makedirs(CARPETA_FILTRADOS, exist_ok=True)
os.makedirs(CARPETA_COMPLETOS, exist_ok=True)
os.makedirs(CARPETA_PNGS, exist_ok=True)

def load_session_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(
        path, delimiter=';', skiprows=1,
        names=['t','x','y','z'], dtype=str, encoding='utf-8', engine='python'
    )
    for c in ['t','x','y','z']:
        df[c] = pd.to_numeric(df[c].str.replace(',','.', regex=False), errors='coerce')
    return df.dropna().sort_values('t').reset_index(drop=True)

def sma(arr: np.ndarray, w: int = 5) -> np.ndarray:
    n = len(arr)
    if w <= 1 or n == 0:
        return arr.astype(float, copy=True)
    out = np.empty(n, dtype=float)
    csum = np.cumsum(np.insert(arr.astype(float), 0, 0.0))
    half = w // 2
    for i in range(n):
        a = max(0, i - half)
        b = min(n, i + (w - half))
        out[i] = (csum[b] - csum[a]) / (b - a)
    return out

def detectar_golpes(t, x, y, z, umbral, w, pre, post, refract, peak_lookahead):
    mag = np.sqrt(x*x + y*y + z*z)
    mags = sma(mag, w=w)
    dt_med = float(np.median(np.diff(t))) if len(t) >= 5 else 20.0
    fs = 1000.0 / dt_med if dt_med > 0 else float('nan')

    golpes = []
    last_peak_idx = -10**9
    above_prev = False
    n = len(mags)

    for k in range(n):
        above = mags[k] > umbral
        if above and not above_prev:
            k2 = min(n - 1, k + max(1, peak_lookahead))
            k_peak_rel = int(np.argmax(mags[k:k2 + 1]))
            k_peak = k + k_peak_rel
            if (k_peak - last_peak_idx) >= max(1, refract):
                i0 = max(0, k_peak - max(0, pre))
                i1_exclusive = min(n, k_peak + max(0, post))  # exclusivo
                if i1_exclusive - i0 >= max(6, pre + post // 2):
                    golpes.append((len(golpes) + 1, i0, i1_exclusive - 1))  # inclusivo
                    last_peak_idx = k_peak
        above_prev = above

    meta = dict(dt_med_ms=dt_med, fs_hz=fs, total_muestras=n, total_golpes=len(golpes))
    return golpes, mags, mag, meta

def construir_dataframes_segmento(t, x, y, z, i0, i1, w):
    sl = slice(i0, i1 + 1)
    df_simple = pd.DataFrame({
        'Tiempo(ms)': t[sl],
        'X(m/s²)':    x[sl],
        'Y(m/s²)':    y[sl],
        'Z(m/s²)':    z[sl]
    }).reset_index(drop=True)

    mag_seg = np.sqrt(df_simple['X(m/s²)']**2 + df_simple['Y(m/s²)']**2 + df_simple['Z(m/s²)']**2).to_numpy()
    suav_seg = sma(mag_seg, w=max(3, w))
    std = float(np.std(suav_seg))
    norm_seg = (suav_seg - float(np.mean(suav_seg))) / (std if std > 1e-9 else 1.0)

    df_completo = df_simple.copy()
    df_completo['magnitud']    = mag_seg
    df_completo['suavizado']   = suav_seg
    df_completo['normalizado'] = norm_seg
    return df_simple, df_completo

def mover_pngs_generados(ruta_completo: str):
    """
    Mueve cualquier PNG generado por graficar_procesado.py en la misma carpeta
    que 'ruta_completo' hacia CARPETA_PNGS, usando el stem como patrón.
    Evita sobrescribir: si existe, añade sufijo _1, _2, ...
    """
    origen_dir = os.path.dirname(ruta_completo)
    stem = os.path.splitext(os.path.basename(ruta_completo))[0]   # ej: sesion_..._golpe_01_procesado_completo
    patrones = [
        os.path.join(origen_dir, f"{stem}.png"),
        os.path.join(origen_dir, f"{stem}_*.png"),  # por si el script añade sufijos
    ]
    encontrados = []
    for pat in patrones:
        encontrados += glob.glob(pat)

    for src in encontrados:
        base = os.path.basename(src)
        dst = os.path.join(CARPETA_PNGS, base)
        if os.path.abspath(src) == os.path.abspath(dst):
            continue  # ya está en destino
        # Evitar sobrescritura
        if os.path.exists(dst):
            nombre, ext = os.path.splitext(base)
            k = 1
            nuevo = os.path.join(CARPETA_PNGS, f"{nombre}_{k}{ext}")
            while os.path.exists(nuevo):
                k += 1
                nuevo = os.path.join(CARPETA_PNGS, f"{nombre}_{k}{ext}")
            dst = nuevo
        try:
            shutil.move(src, dst)
        except Exception as e:
            print(f"⚠️ No se pudo mover PNG '{src}' → '{dst}': {e}")

def guardar_artifactos(base_name: str, golpes, t, x, y, z, w: int, gen_png: bool):
    out = []
    for idx, i0, i1 in golpes:
        base = f"{base_name}_golpe_{idx:02d}"
        ruta_simple   = os.path.join(CARPETA_FILTRADOS,  base + "_filtrado.csv")
        ruta_completo = os.path.join(CARPETA_COMPLETOS,  base + "_procesado_completo.csv")

        df_simple, df_completo = construir_dataframes_segmento(t, x, y, z, i0, i1, w)
        df_simple.to_csv(ruta_simple, sep=';', index=False)
        df_completo.to_csv(ruta_completo, sep=';', index=False)

        if gen_png:
            try:
                # Genera PNG junto al CSV completo...
                subprocess.run(
                    ["python3", "/home/adri/flask/graficar_procesado.py", ruta_completo],
                    check=False
                )
                # ...y luego muévelo a capturas/completos/
                mover_pngs_generados(ruta_completo)
            except Exception as e:
                print(f"⚠️ Error generando/moviendo PNG: {e}")

        out.append((idx, ruta_simple, ruta_completo, i0, i1))
    return out

def main():
    ap = argparse.ArgumentParser(description="Procesado offline de sesión (ventanas en MUESTRAS).")
    ap.add_argument("csv", help="Ruta al CSV de sesión (Tiempo;X;Y;Z)")
    ap.add_argument("--umbral", type=float, default=15.0, help="Umbral fijo sobre magnitud suavizada (m/s^2)")
    ap.add_argument("--w",      type=int,   default=5,    help="Ventana SMA (muestras)")
    ap.add_argument("--pre",    type=int,   default=30,   help="Muestras PRE al pico (por defecto 30)")
    ap.add_argument("--post",   type=int,   default=30,   help="Muestras POST al pico (por defecto 30)")
    ap.add_argument("--refract", type=int,  default=60,   help="Refractario entre golpes (muestras) ⇒ ~1.2 s a 50 Hz")
    ap.add_argument("--peak-lookahead", type=int, default=15, help="Búsqueda de pico hacia delante (muestras) ⇒ ~0.3 s a 50 Hz")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--png",    dest="gen_png", action="store_true",  help="(Compat.) Forzar generación de PNG (por defecto ya está activado)")
    g.add_argument("--no-png", dest="gen_png", action="store_false", help="NO generar PNG")
    ap.set_defaults(gen_png=True)
    args = ap.parse_args()

    path = Path(args.csv)
    if not path.exists():
        print(f"❌ No existe: {path}")
        sys.exit(1)

    print(f"📂 Sesión: {path}")
    df = load_session_csv(path)
    t = df['t'].to_numpy(); x = df['x'].to_numpy(); y = df['y'].to_numpy(); z = df['z'].to_numpy()

    golpes, mags, mag, meta = detectar_golpes(
        t, x, y, z,
        umbral=args.umbral, w=args.w,
        pre=args.pre, post=args.post,
        refract=args.refract, peak_lookahead=args.peak_lookahead
    )

    base_name = path.stem
    saved = guardar_artifactos(base_name, golpes, t, x, y, z, w=args.w, gen_png=args.gen_png)

    print(f"✅ Detectados {len(saved)} golpes | dt_med≈{meta['dt_med_ms']:.1f} ms (fs≈{meta['fs_hz']:.2f} Hz) | N={meta['total_muestras']}")
    for idx, rs, rc, i0, i1 in saved:
        print(f"  #{idx:02d} [{i0}:{i1}] (N={i1-i0+1:02d}) → {os.path.basename(rs)} | {os.path.basename(rc)}")

if __name__ == "__main__":
    main()
