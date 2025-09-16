#!/usr/bin/env python3
import os, time, subprocess, serial, requests, sys

SERVER_URL = os.environ.get("SERVER_URL", "http://192.168.0.33:5000/add_batch")
MAC        = os.environ.get("ESP32_MAC", "C0:49:EF:08:D6:FE")
RFCOMM_DEV = os.environ.get("RFCOMM_DEV", "0")
BAUD       = int(os.environ.get("BAUD", "115200"))

BATCH_N    = int(os.environ.get("BATCH_N", "25"))   # ~0.5s a 50 Hz
BATCH_MS   = int(os.environ.get("BATCH_MS", "250")) # o cada 250 ms
TIMEOUT    = (0.5, 0.5)  # connect, read
MAX_BACKLOG = int(os.environ.get("MAX_BACKLOG", "1000"))  # máx líneas en cola

def sh(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT>

def ensure_rfcomm():
    if not os.path.exists(f"/dev/rfcomm{RFCOMM_DEV}"):
        sh(["rfcomm", "release", RFCOMM_DEV])
        sh(["rfcomm", "bind", RFCOMM_DEV, MAC, "1"])

def open_serial():
    return serial.Serial(f"/dev/rfcomm{RFCOMM_DEV}", BAUD, timeout=0.2)

print(f"🌉 Reenviando a: {SERVER_URL}")
ser = None
sess = requests.Session()
buf, last_send = [], time.monotonic()

while True:
    try:
        ensure_rfcomm()
        if ser is None or not ser.is_open:
            print(f"📶 Abriendo /dev/rfcomm{RFCOMM_DEV}...")
            ser = open_serial()
            print("✅ Conectado")

        line = ser.readline().decode("utf-8", errors="ignore").strip()
        if not line or line.startswith("Tiempo"):
            continue

        buf.append(line)
        now = time.monotonic()
        # Enviar por tamaño de lote o por tiempo
        if len(buf) >= BATCH_N or (now - last_send) * 1000 >= BATCH_MS:
            try:
                payload = "\n".join(buf)
                r = sess.post(SERVER_URL, data=payload,
                              headers={"Content-Type": "text/plain"},
                              timeout=TIMEOUT)
                r.raise_for_status()
                buf.clear()
                last_send = now
            except Exception as e:
                print(f"⚠️  HTTP: {e}", file=sys.stderr)
                # Evita colas de minutos: conserva solo las últimas MAX_BACKLOG
                if len(buf) > MAX_BACKLOG:
                    buf[:] = buf[-MAX_BACKLOG:]
                time.sleep(0.2)

    except (serial.SerialException, OSError) as e:
        print(f"⚠️  BT caído: {e}. Reintentando...")
        try:
            if ser: ser.close()
        except: pass
        ser = None
        time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n👋 Saliendo...")
        break
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        time.sleep(0.5)

try:
    if ser and ser.is_open: ser.close()
except: pass

