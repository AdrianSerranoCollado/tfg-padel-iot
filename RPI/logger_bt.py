!/usr/bin/env python3
import os, time, subprocess, serial
from datetime import datetime

MAC = os.environ.get("ESP32_MAC", "C0:49:EF:08:D6:FE")   # CAMBIA si hace falta
RFCOMM_DEV = os.environ.get("RFCOMM_DEV", "0")
BAUD = int(os.environ.get("BAUD", "115200"))
OUTDIR = os.environ.get("OUTDIR", "/home/pi/padel/sesiones")
ROTATE_MIN = int(os.environ.get("ROTATE_MIN", "30"))

os.makedirs(OUTDIR, exist_ok=True)

def sh(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT>

def ensure_rfcomm():
    # Intenta tener /dev/rfcommN disponible
    if not os.path.exists(f"/dev/rfcomm{RFCOMM_DEV}"):
        sh(["rfcomm", "release", RFCOMM_DEV])
        sh(["rfcomm", "bind", RFCOMM_DEV, MAC, "1"])

def open_serial():
    return serial.Serial(f"/dev/rfcomm{RFCOMM_DEV}", BAUD, timeout=1)

def new_file():
    ts = datetime.now().strftime("sesion_%Y-%m-%d_%H-%M-%S.csv")
    path = os.path.join(OUTDIR, ts)
    f = open(path, "w", buffering=1)
    f.write("Tiempo(ms);X(m/s²);Y(m/s²);Z(m/s²)\n")
    return f, path

print(f"📥 Guardando en: {OUTDIR}")
ser, f, path = None, None, None
t_start = 0

while True:
    try:
        ensure_rfcomm()
        if ser is None or not ser.is_open:
            print("📶 Abriendo /dev/rfcomm%s..." % RFCOMM_DEV)
            ser = open_serial()
            print("✅ Conectado")

        if f is None:
            f, path = new_file()
            t_start = time.time()
            print(f"📝 Registrando en: {path}")

        if (time.time() - t_start) > ROTATE_MIN*60:
            f.close()
            f, path = new_file()
            t_start = time.time()
            print(f"🔄 Rotación de fichero. Nuevo: {path}")

        line = ser.readline().decode("utf-8", errors="ignore").strip()
        if not line:
            continue
        if "Tiempo" in line:
            continue
        f.write(line + "\n")

    except (serial.SerialException, OSError) as e:
        print(f"⚠️ BT caído: {e}. Reintentando...")
        try:
            if ser: ser.close()
        except: pass
        ser = None
        time.sleep(2)
    except KeyboardInterrupt:
        print("\n👋 Saliendo...")
        break
    except Exception as e:
        print(f"❌ Error: {e}")
        time.sleep(1)

try:
    if f: f.close()
    if ser and ser.is_open: ser.close()
except: pass

