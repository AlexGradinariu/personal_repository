/*
 * ============================================================
 *  Statie meteo + calitate aer + miscare — NodeMCU ESP8266
 * ============================================================
 *  Senzori:
 *    - AHT20 + BMP280   → Temperatura, Umiditate, Presiune (I2C)
 *    - BH1750 (GY-302)  → Intensitate lumina (I2C)
 *    - ADS1115           → ADC 16-bit (I2C, 0x48)
 *        A0 = MQ-135     → Calitate aer
 *        A1 = MQ-9       → CO / GPL
 *    - OLED 0.96" I2C   → Afisaj (I2C, 0x3C)
 *    - SR602             → Senzor miscare PIR (digital, D3)
 *
 *  Pinout I2C:
 *    SDA = D2 (GPIO 4)
 *    SCL = D1 (GPIO 5)
 *
 *  Alimentare:
 *    VBUS (5V) → MQ-9, MQ-135 (VCC senzor)
 *    3.3V      → AHT20, BMP280, BH1750, OLED, ADS1115, SR602
 *    GND       → toate, comune
 *
 *  Divizor tensiune (AO senzori MQ → ADS1115):
 *    AO_MQ ─── R1(10kΩ) ─┬─── AINx (ADS1115)
 *                          │
 *                        R2(20kΩ)
 *                          │
 *                         GND
 *    Vout = Vin * 20/30 = Vin * 0.666
 *    5V * 0.666 = 3.33V (sigur pentru ADS1115 la 3.3V)
 *
 *  Biblioteci necesare:
 *    - Adafruit AHTX0
 *    - Adafruit BMP280
 *    - BH1750 by Christopher Laws
 *    - Adafruit ADS1X15
 *    - Adafruit SSD1306
 *    - Adafruit GFX Library
 * ============================================================
 */

#include <Wire.h>
#include <Adafruit_AHTX0.h>
#include <Adafruit_BMP280.h>
#include <BH1750.h>
#include <Adafruit_ADS1X15.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_GFX.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// ── Pini ──────────────────────────────────────────────────
#define PIR_PIN D3   // SR602 OUT

// ── WiFi & MQTT ───────────────────────────────────────────
const char* ssid            = "Lita_Edi_Parter";
const char* password        = "Ilinca20";
const char* mqtt_server     = "192.168.20.189";
const char* mqtt_pub_topic  = "read/sensor_outside";
const char* mqtt_sub_topic  = "home/sensor_outside/cmd";

WiFiClient   espClient;
PubSubClient mqtt(espClient);

// ── OLED ──────────────────────────────────────────────────
#define SCREEN_WIDTH  128
#define SCREEN_HEIGHT  64
#define OLED_RESET     -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// ── Senzori ───────────────────────────────────────────────
Adafruit_AHTX0   aht;
Adafruit_BMP280  bmp;
BH1750           lightMeter;
Adafruit_ADS1115 ads;

// ── Calibrare MQ ─────────────────────────────────────────
// R0 = rezistenta in aer curat (masoara si actualizeaza!)
// RL = rezistenta de sarcina de pe placa senzorului
// Divizor tensiune: 10k + 10k => v_real = v_citit * 2.0
// Formula Rs: ((Vcc - Vreal) * RL) / Vreal

float       R0_MQ135  = 49;   // kOhm — actualizeaza dupa calibrare!
const float RL_MQ135  = 1.0;    // kOhm

float       R0_MQ9    = 18.3;    // kOhm — actualizeaza dupa calibrare!
const float RL_MQ9    = 1.0;    // kOhm

// ── Smoothing buffers MQ (medie pe 10 esantioane) ────────
float mq135Buffer[10];
float mq9Buffer[10];
int   idxBuf135 = 0;
int   idxBufMQ9 = 0;

// Ratio curent (Rs/R0) — folosit si la OLED si la Serial
float g_ratio135 = 0;
float g_ratio9   = 0;

// ── Timing ───────────────────────────────────────────────
const unsigned long INTERVAL  = 3000;  // citire senzori (ms)
const unsigned long PAGE_TIME = 2500;  // schimbare pagina OLED (ms)
// Miscare: afiseaza pe OLED minim 5s dupa ultima detectie
const unsigned long PIR_SHOW  = 5000;

unsigned long lastRead    = 0;
unsigned long lastPage    = 0;
unsigned long lastMotion  = 0;
int           oledPage    = 0;

// ── Date globale ─────────────────────────────────────────
float g_temp     = 0;
float g_hum      = 0;
float g_pres     = 0;
float g_lux      = 0;
bool  g_motion   = false;

bool  ahtOK     = false;
bool  bmpOK     = false;
bool  bh1750OK  = false;
bool  adsOK     = false;

// ─────────────────────────────────────────────────────────
// Citire tensiune bruta ADS1115 (V)
// ─────────────────────────────────────────────────────────
float readVoltage(uint8_t channel) {
  int16_t raw = ads.readADC_SingleEnded(channel);
  return raw * 0.1875 / 1000.0;  // GAIN_ONE: 0.1875 mV/bit
}

// ─────────────────────────────────────────────────────────
// Calcul Rs din tensiunea citita
// Divizor 10k+10k => v_real = v_citit * 2.0
// Rs = ((Vcc - Vreal) * RL) / Vreal
// ─────────────────────────────────────────────────────────
float getRsMQ135(float volt) {
  float v_real = volt * 2.0;
  if (v_real < 0.1) v_real = 0.1;
  if (v_real > 4.9) v_real = 4.9;
  return ((5.0 - v_real) * RL_MQ135) / v_real;
}

float getRsMQ9(float volt) {
  float v_real = volt * 2.0;
  if (v_real < 0.1) v_real = 0.1;
  if (v_real > 4.9) v_real = 4.9;
  return ((5.0 - v_real) * RL_MQ9) / v_real;
}

// ─────────────────────────────────────────────────────────
// Smoothing — medie mobila pe 10 esantioane
// ─────────────────────────────────────────────────────────
float smooth(float* buf, float newVal, int& idx) {
  buf[idx] = newVal;
  idx = (idx + 1) % 10;
  float sum = 0;
  for (int i = 0; i < 10; i++) sum += buf[i];
  return sum / 10.0;
}

// ─────────────────────────────────────────────────────────
// MQTT callback — nu avem comenzi in aceasta versiune,
// dar functia e necesara pentru PubSubClient
// ─────────────────────────────────────────────────────────
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  // rezervat pentru comenzi viitoare
}

// ─────────────────────────────────────────────────────────
void connectMQTT() {
  while (!mqtt.connected()) {
    display.clearDisplay();
    display.setCursor(0, 0);
    display.println("MQTT...");
    display.display();
    Serial.print("Conectare MQTT...");
    if (mqtt.connect("NodeMCU_Senzori")) {
      mqtt.subscribe(mqtt_sub_topic);
      Serial.println(" OK");
      display.clearDisplay();
      display.setCursor(0, 0);
      display.println("MQTT OK");
      display.display();
      delay(1000);
    } else {
      Serial.print(" eroare, rc=");
      Serial.println(mqtt.state());
      delay(2000);
    }
  }
}

// ─────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);

  // Initializeaza bufferele de smoothing MQ cu primele citiri
  ads.setGain(GAIN_ONE);
  ads.begin();
  for (int i = 0; i < 10; i++) {
    mq135Buffer[i] = readVoltage(0) * 1000;
    mq9Buffer[i]   = readVoltage(1) * 1000;
    delay(20);
  }

  Wire.begin();  // SDA=D2, SCL=D1

  pinMode(PIR_PIN, INPUT);

  Serial.println("\n== Initializare ==");

  // OLED
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("[EROARE] OLED negasit!");
  } else {
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(0, 0);
    display.println("Initializare...");
    display.display();
    Serial.println("[OK] OLED");
  }

  // AHT20
  if (aht.begin()) {
    ahtOK = true;
    Serial.println("[OK] AHT20");
  } else {
    Serial.println("[EROARE] AHT20 negasit!");
  }

  // BMP280
  if (bmp.begin(0x76) || bmp.begin(0x77)) {
    bmpOK = true;
    bmp.setSampling(Adafruit_BMP280::MODE_NORMAL,
                    Adafruit_BMP280::SAMPLING_X2,
                    Adafruit_BMP280::SAMPLING_X16,
                    Adafruit_BMP280::FILTER_X16,
                    Adafruit_BMP280::STANDBY_MS_500);
    Serial.println("[OK] BMP280");
  } else {
    Serial.println("[EROARE] BMP280 negasit!");
  }

  // BH1750
  if (lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE)) {
    bh1750OK = true;
    Serial.println("[OK] BH1750");
  } else {
    Serial.println("[EROARE] BH1750 negasit!");
  }

  // ADS1115
  if (ads.begin()) {
    adsOK = true;
    Serial.println("[OK] ADS1115");
  } else {
    Serial.println("[EROARE] ADS1115 negasit!");
  }

  // WiFi
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println("WiFi...");
  display.display();
  WiFi.begin(ssid, password);
  Serial.print("Conectare WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" OK");
  Serial.print("IP: "); Serial.println(WiFi.localIP());
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println("WiFi OK");
  display.display();
  delay(800);

  // MQTT
  mqtt.setServer(mqtt_server, 1883);
  mqtt.setCallback(mqttCallback);
  connectMQTT();

  // Preincalzire MQ
  Serial.println("Preincalzire MQ... 20s");
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println("Preincalzire MQ");
  display.println("Asteapta 20s...");
  display.println("(60s = precizie max)");
  display.display();
  delay(20000);

  Serial.println("== Gata! ==\n");
}

// ─────────────────────────────────────────────────────────
void readSensors() {

  // AHT20
  if (ahtOK) {
    sensors_event_t humidity, temp;
    aht.getEvent(&humidity, &temp);
    g_temp = temp.temperature;
    g_hum  = humidity.relative_humidity;
  }

  // BMP280
  if (bmpOK) {
    g_pres = bmp.readPressure() / 100.0F;  // hPa
    if (!ahtOK) g_temp = bmp.readTemperature();
  }

  // BH1750
  if (bh1750OK) {
    g_lux = lightMeter.readLightLevel();
  }

  // ADS1115 — MQ senzori
  if (adsOK) {
    // A0 = MQ-135 (calitate aer)
    float v135      = readVoltage(0);
    float rs135     = getRsMQ135(v135);
    g_ratio135      = rs135 / R0_MQ135;
    smooth(mq135Buffer, v135 * 1000, idxBuf135);  // smoothing pentru stabilitate

    // A1 = MQ-9 (CO)
    float v9        = readVoltage(1);
    float rs9       = getRsMQ9(v9);
    g_ratio9        = rs9 / R0_MQ9;
    smooth(mq9Buffer, v9 * 1000, idxBufMQ9);
  }

  // SR602 — miscare
  g_motion = digitalRead(PIR_PIN);
  if (g_motion) lastMotion = millis();
}

// ─────────────────────────────────────────────────────────
void printSerial() {
  Serial.println("──────────────────────────────");
  if (ahtOK) {
    Serial.printf("Temperatura  : %.1f °C\n", g_temp);
    Serial.printf("Umiditate    : %.1f %%\n",  g_hum);
  }
  if (bmpOK) {
    Serial.printf("Presiune     : %.1f hPa\n", g_pres);
  }
  if (bh1750OK) {
    Serial.printf("Lumina       : %.0f lux\n", g_lux);
  }
  if (adsOK) {
    Serial.print("MQ135 Ratio: "); Serial.print(g_ratio135);
    Serial.print(" | MQ9 Ratio: "); Serial.println(g_ratio9);

    // Calitate aer bazata pe ratio MQ-135
    // Ratio mare = aer curat, ratio mic = aer poluat
    if      (g_ratio135 > 0.8) Serial.println("Calitate aer : EXCELENTA");
    else if (g_ratio135 > 0.5) Serial.println("Calitate aer : MODERATA");
    else                        Serial.println("Calitate aer : SLABA !");

    // CO bazat pe ratio MQ-9
    if      (g_ratio9 > 0.9)  Serial.println("CO           : Normal");
    else if (g_ratio9 > 0.5)  Serial.println("CO           : Atentie!");
    else if (g_ratio9 > 0.2)  Serial.println("CO           : MODERAT");
    else                       Serial.println("CO           : PERICOL!");

    // Decommenteaza pentru calibrare initiala (ruleaza in aer curat):
    // Serial.print("SCRIE IN R0_MQ135: "); Serial.println(getRsMQ135(readVoltage(0)));
    // Serial.print("SCRIE IN R0_MQ9:   "); Serial.println(getRsMQ9(readVoltage(1)));
  }

  Serial.printf("Miscare      : %s\n", g_motion ? "DA" : "nu");
  Serial.println("──────────────────────────────");
}

// ─────────────────────────────────────────────────────────
// Calitate aer — text scurt pentru OLED
// ─────────────────────────────────────────────────────────
const char* airQualityStr() {
  if      (g_ratio135 > 0.8) return "EXCELENTA";
  else if (g_ratio135 > 0.5) return "MODERATA";
  else                        return "SLABA!";
}

// ─────────────────────────────────────────────────────────
// OLED — 4 pagini rotative
//   0: Temperatura / Umiditate / Presiune
//   1: Lumina / CO (MQ-9)
//   2: Calitate aer (MQ-135)
//   3: Miscare + uptime
// Daca e detectata miscare, afiseaza pagina 3 prioritar
// ─────────────────────────────────────────────────────────
void updateOLED() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);

  bool motionRecent = (millis() - lastMotion < PIR_SHOW);

  // Daca e miscare recenta, sari direct la pagina de miscare
  int page = motionRecent ? 3 : oledPage;

  switch (page) {
    case 0:
      display.println("-- Clima --");
      if (ahtOK) {
        display.printf("Temp: %.1f C\n", g_temp);
        display.printf("Hum:  %.0f %%\n", g_hum);
      } else {
        display.println("AHT20 lipsa");
      }
      if (bmpOK) {
        display.printf("Pres: %.1f hPa\n", g_pres);
      } else {
        display.println("BMP280 lipsa");
      }
      break;

    case 1:
      display.println("-- Lumina & CO --");
      if (bh1750OK) {
        display.printf("Lux:  %.0f\n", g_lux);
      } else {
        display.println("BH1750 lipsa");
      }
      if (adsOK) {
        display.printf("CO r: %.2f\n", g_ratio9);
        if (g_ratio9 < 0.2) display.println("!! PERICOL CO !!");
        else if (g_ratio9 < 0.5) display.println("! Atentie CO");
      } else {
        display.println("ADS lipsa");
      }
      break;

    case 2:
      display.println("-- Calitate Aer --");
      if (adsOK) {
        display.printf("Ratio: %.2f\n", g_ratio135);
        display.println(airQualityStr());
        if (g_ratio135 < 0.5) display.println("!! VENTILEAZA !!");
      } else {
        display.println("MQ-135 lipsa");
      }
      break;

    case 3:
      display.println("-- Miscare --");
      if (motionRecent) {
        display.println("** DETECTATA **");
        unsigned long secAgo = (millis() - lastMotion) / 1000;
        if (secAgo == 0) display.println("Acum!");
        else display.printf("Acum %lus\n", secAgo);
      } else {
        display.println("Nicio miscare");
      }
      display.printf("\nUptime: %lus\n", millis() / 1000);
      break;
  }

  display.display();
}

// ─────────────────────────────────────────────────────────
void loop() {
  // Mentine conexiunea MQTT
  if (!mqtt.connected()) connectMQTT();
  mqtt.loop();

  unsigned long now = millis();

  // Citire senzori la interval
  if (now - lastRead >= INTERVAL) {
    lastRead = now;
    readSensors();
    printSerial();
    updateOLED();
  }

  // Publicare MQTT la 5 secunde
  static unsigned long lastMqttPublish = 0;
  if (now - lastMqttPublish >= 5000) {
    lastMqttPublish = now;
    char payload[200];
    snprintf(payload, sizeof(payload),
      "{\"temp\":%.1f,\"hum\":%.0f,\"pres\":%.1f,\"lux\":%.0f,\"mq135_r\":%.2f,\"mq9_r\":%.2f,\"motion\":%d}",
      g_temp, g_hum, g_pres, g_lux, g_ratio135, g_ratio9, g_motion ? 1 : 0);
    mqtt.publish(mqtt_pub_topic, payload);
    Serial.print("MQTT publicat: "); Serial.println(payload);
  }

  // Schimbare pagina OLED (doar daca nu e miscare recenta)
  if (now - lastPage >= PAGE_TIME) {
    lastPage = now;
    if (millis() - lastMotion >= PIR_SHOW) {
      oledPage = (oledPage + 1) % 4;
    }
    updateOLED();
  }
}

/*
 * ============================================================
 *  CALIBRARE MQ — pasi:
 * ============================================================
 *  1. Lasa senzorii sa se incalzeasca 24-48h la prima pornire.
 *  2. Porneste in aer curat (afara sau camera ventilata).
 *  3. Decommenteaza liniile de calibrare din printSerial():
 *       // Serial.print("SCRIE IN R0_MQ135: "); ...
 *       // Serial.print("SCRIE IN R0_MQ9:   "); ...
 *  4. Citeste valorile din Serial Monitor si actualizeaza:
 *       float R0_MQ135 = <valoarea citita>;
 *       float R0_MQ9   = <valoarea citita>;
 *  5. Recommenteaza liniile de calibrare.
 *
 *  INTERPRETARE RATIO (Rs/R0):
 *    Ratio aproape de 1.0 = aer curat (Rs ≈ R0)
 *    Ratio < 1.0 = concentratie crescuta de gaz
 *
 *  MQ-135 ratio:  > 0.8 Excelent | 0.5-0.8 Moderat | < 0.5 Slab
 *  MQ-9 ratio:    > 0.9 Normal   | 0.5-0.9 Atentie  | < 0.2 Pericol
 *
 * ============================================================
 *  REZUMAT CONEXIUNI:
 * ============================================================
 *  NodeMCU D1 (SCL) → SCL: OLED, AHT20, BMP280, BH1750, ADS1115
 *  NodeMCU D2 (SDA) → SDA: OLED, AHT20, BMP280, BH1750, ADS1115
 *  NodeMCU D3       → OUT: SR602
 *  NodeMCU 3.3V     → VCC: OLED, AHT20, BMP280, BH1750, ADS1115, SR602
 *  NodeMCU VBUS(5V) → VCC: MQ-9, MQ-135
 *  NodeMCU GND      → GND: toate
 *  ADS1115 A0       ← AO MQ-135 (prin divizor 10k+20k)
 *  ADS1115 A1       ← AO MQ-9   (prin divizor 10k+20k)
 *  ADS1115 ADDR     → GND (adresa I2C = 0x48)
 * ============================================================
 */
