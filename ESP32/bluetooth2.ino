#include <BluetoothSerial.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_ADXL345_U.h>

BluetoothSerial SerialBT;
Adafruit_ADXL345_Unified accel = Adafruit_ADXL345_Unified(12345);

unsigned long tiempoInicio = 0;

void setup() {
  Serial.begin(115200);
  SerialBT.begin("PalaPadelESP32"); // Nombre Bluetooth

  if (!accel.begin()) {
    SerialBT.println("Error: no se encontró el ADXL345");
    while (1);
  }
  accel.setRange(ADXL345_RANGE_16_G);
  tiempoInicio = millis();

  // Cabecera CSV
  SerialBT.println("Tiempo(ms);X(m/s²);Y(m/s²);Z(m/s²)");
}

void loop() {
  sensors_event_t event;
  accel.getEvent(&event);

  unsigned long tiempoActual = millis() - tiempoInicio;

  // Convertimos puntos a comas (Excel en español suele usar , como decimal)
  String x = String(event.acceleration.x, 2); x.replace('.', ',');
  String y = String(event.acceleration.y, 2); y.replace('.', ',');
  String z = String(event.acceleration.z, 2); z.replace('.', ',');

  String filaCSV = String(tiempoActual) + ";" + x + ";" + y + ";" + z;

  SerialBT.println(filaCSV);
  delay(200);
  //delay(50); 

}
