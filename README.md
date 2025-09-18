# tfg-padel-iot
proyecto TFG

## Datos
En la carpeta `Datos/` incluyo **muestras representativas** de golpes:
- `originales/`: CSV **brutos** exportados desde la GUI.
- `filtrados/`: CSV **filtrados** (suavizado y recorte por ventana) de esos mismos golpes.
- `completos/`: CSV **completos** con el procesado final (normalización y magnitud).
- `capturas/`: **imágenes (PNG)** de varios golpes generadas a partir de los datos procesados.

Estas carpetas sirven como **ejemplos de referencia** para reproducir y entender el flujo de trabajo.

## Procesamiento
En `Procesamiento/` están **todos los scripts utilizados en el TFG** para detección, filtrado, graficado y comparación de golpes.

## ESP32
En `ESP32/` — firmware (Arduino/ESP32) que lee ADXL345 @50 Hz y envía por **Bluetooth Clásico (SPP)** líneas `t;x;y;z` con **coma decimal** (`Tiempo(ms);X(m/s²);Y(m/s²);Z(m/s²)`).

## FLASK
En `Flask/` — backend Flask y GUI (`app.py`, `templates/`, `static/`).

## RPI
En `RPI/` — pasarela y registrador: `bridge_bt.py` (RFCOMM → HTTP `/add_batch`), `logger_bt.py` (CSV de sesión) y `services/` (systemd).

## WIRESHARK
En `Wireshark/` — capturas de red (SPP/RFCOMM y `POST /add_batch` periódico) de apoyo a las pruebas.

## BASE_DATOS
En `base_datos/` — plantillas por tipo de golpe (1-bandeja, 2-globo, 3-remate, 4-volea) usadas por `identificar_golpe.py`.
