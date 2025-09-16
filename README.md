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
