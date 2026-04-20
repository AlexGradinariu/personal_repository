#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <Adafruit_AHTX0.h>
#include <Adafruit_BMP280.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <Adafruit_ADS1X15.h>


// ── Config ─────────────────────────
const char* ssid = "Gradinariu_wifi24";
const char* password = "Gradinariu@net";
const char* mqtt_server = "192.168.50.64";
const char* mqtt_pub_topic = "read/sensor";
const char* mqtt_sub_topic = "home/sensor/cmd";

// ── Obiecte ────────────────────────
LiquidCrystal_I2C lcd(0x27, 16, 2);
Adafruit_AHTX0 aht;
Adafruit_BMP280 bmp;
WiFiClient espClient;
PubSubClient mqtt(espClient);
Adafruit_ADS1115 ads;


// ── Variabile ──────────────────────
String mesajPi     = "";      
String mesajAfisare = "";     
int    screen      = 0;       
int    scrollPg    = 0;       
int    totalPages  = 0;       
unsigned long lastMs = 0;     

float R0_MQ9 = 2.5; 
const float RL_MQ9 = 1.0; 
float R0_MQ135 = 2.06 ;
const float RL_MQ135 = 1.0; 
;

// ── MQTT callback ─────────────────
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  mesajPi = "";
  for (int i = 0; i < length; i++) {
    mesajPi += (char)payload[i];
  }
}

// ── MQTT connect ──────────────────
void connectMQTT() {
  while (!mqtt.connected()) {
    lcd.clear();
    lcd.print("MQTT...");
    if (mqtt.connect("NodeMCU_Display")) {
      mqtt.subscribe(mqtt_sub_topic);
      lcd.clear();
      lcd.print("MQTT OK");
      delay(1000);
      lcd.clear();
    } else {
      delay(2000);
    }
  }
}

// ── Build page pentru scroll ──────
String buildPage(String text, int page, int width) {
  int len = text.length();
  int index = 0;
  int currentPage = 0;

  while (index < len) {
    int end = index + width;
    if (end >= len) end = len;
    if (end < len && text[end] != ' ') {
      int back = end;
      while (back > index && text[back] != ' ') back--;
      if (back > index) end = back;
    }
    if (currentPage == page) {
      String result = text.substring(index, end);
      while ((int)result.length() < width) result += " ";
      return result;
    }
    index = end + 1;
    currentPage++;
  }
  return "                ";
}

// ── ADS helper ──
float readVoltage(uint8_t channel) {
  int16_t raw = ads.readADC_SingleEnded(channel);
  return raw * 0.1875 / 1000.0;
}

// ── simple smoothing buffers ──
float mq135Buffer[10];
float mq9Buffer[10];
int idxBuf135 = 0;
int idxBufMQ9 = 0;

float smooth(float *buf, float newVal, int &idx) {
  buf[idx] = newVal;
  idx = (idx + 1) % 10;
  float sum = 0;
  for (int i = 0; i < 10; i++) sum += buf[i];
  return sum / 10.0;
}

float getRsMQ9(float voltaj) {
  // Deoarece ai 10k + 10k, tensiunea reala este voltajul citit de ADS inmultit cu 2
  float v_real = voltaj * 2.0; 
  
  // Limitam valorile pentru a evita erori de calcul (infinit sau negativ)
  if (v_real < 0.1) v_real = 0.1;
  if (v_real > 4.9) v_real = 4.9; 
  
  // Formula: Rs = ((Vcc - Vreal) * RL) / Vreal
  return ((5.0 - v_real) * RL_MQ9) / v_real;
}

float getRsMQ135(float voltaj) {
  float v_real = voltaj * 2.0; 
  
  if (v_real < 0.1) v_real = 0.1;
  if (v_real > 4.9) v_real = 4.9;
  
  return ((5.0 - v_real) * RL_MQ135) / v_real;
}

// ── Setup ─────────────────────────
void setup() {
  Serial.begin(115200);
  ads.begin(); 
  ads.setGain(GAIN_ONE);  
  for (int i = 0; i < 10; i++) {
    float v = readVoltage(0);
    mq135Buffer[i] = v * 1000;
    v = readVoltage(1);
    mq9Buffer[i] = v * 1000;
    delay(20);
  }
  Wire.begin(4, 5);
  lcd.init();
  lcd.backlight();
  aht.begin();
  if (!bmp.begin(0x76) && !bmp.begin(0x77)) {
    Serial.println("BMP280 negasit!");
    while (1);
  }
  WiFi.begin(ssid, password);
  lcd.print("WiFi...");
  while (WiFi.status() != WL_CONNECTED) delay(500);
  lcd.clear();
  lcd.print("WiFi OK");
  delay(1000);
  mqtt.setServer(mqtt_server, 1883);
  mqtt.setCallback(mqttCallback);
  connectMQTT();
}

// ── Loop ──────────────────────────
void loop() {
  if (!mqtt.connected()) connectMQTT();
  mqtt.loop();

  // ── 1. Citire senzori ──
  sensors_event_t humidity, temp;
  aht.getEvent(&humidity, &temp);
  float presiune = bmp.readPressure() / 100.0F;

  // MQ135 (A0 ADS)
  float v135 = readVoltage(0);
  float rs135 = getRsMQ135(v135);
  float ratio135 = rs135 / R0_MQ135;
  float ppm = smooth(mq135Buffer, v135 * 1000, idxBuf135);

  // MQ9 (A1 ADS)
  float v9 = readVoltage(1); 
  float raw9 = v9 * 1000;
  float ppmMQ9 = smooth(mq9Buffer, raw9, idxBufMQ9);
  float rsCurrent = getRsMQ9(v9);
  float ratio = rsCurrent / R0_MQ9;

  // Calibrare Serial
  Serial.print("MQ135 Ratio: "); Serial.print(ratio135);
  Serial.print(" | MQ9 Ratio: "); Serial.println(ratio);
  // Adaugă asta sub citirile de senzori pentru 1 minut
  // Serial.print("SCRIE ASTA IN R0_MQ135: "); Serial.println(rs135);
  // Serial.print("SCRIE ASTA IN R0_MQ9: "); Serial.println(rsCurrent);

  // ── 2. Publicare date prin MQTT (la 10 secunde) ──
  static unsigned long lastMqttPublish = 0;
  if (millis() - lastMqttPublish >= 10000) {
      char payload[180]; 
      snprintf(payload, sizeof(payload),
        "{\"temp\":%.1f,\"hum\":%.0f,\"pres\":%.1f,\"mq135_r\":%.2f,\"mq9_r\":%.2f}",
        temp.temperature,
        humidity.relative_humidity,
        presiune,
        ratio135, 
        ratio);   

      mqtt.publish(mqtt_pub_topic, payload);
      lastMqttPublish = millis();
  }

  // ── 3. Procesare mesaj nou primit ──
  if (mesajPi.length() > 0) {
    mesajAfisare = mesajPi;
    mesajPi = ""; 
    
    int totalLinii = 0;
    int idx = 0;
    while (idx < mesajAfisare.length()) {
      int end = idx + 16;
      if (end >= mesajAfisare.length()) end = mesajAfisare.length();
      if (end < mesajAfisare.length() && mesajAfisare[end] != ' ') {
        int back = end;
        while (back > idx && mesajAfisare[back] != ' ') back--;
        if (back > idx) end = back;
      }
      idx = end + 1;
      totalLinii++;
    }
    totalPages = (totalLinii + 1) / 2;
    scrollPg = 0; 
  }

  // ── 4. Schimbare automată ecrane (la fiecare 4 secunde) ──
  if (millis() - lastMs >= 4000) {
    lastMs = millis();
    lcd.clear();

    if (screen == 0) {
      lcd.setCursor(0, 0);
      lcd.print("T:"); lcd.print(temp.temperature, 1);
      lcd.print("C H:"); lcd.print(humidity.relative_humidity, 0); lcd.print("%");
      lcd.setCursor(0, 1);
      lcd.print("Pres:"); lcd.print(presiune, 1); lcd.print("mb");
      screen = 1;
    } 
    else if (screen == 1) {
      lcd.setCursor(0, 0);
      lcd.print("Air: ");
      if (ratio135 > 0.8)      lcd.print("Excelent");
      else if (ratio135 > 0.5) lcd.print("Moderat ");
      else                     lcd.print("Poluat  ");

      lcd.setCursor(0, 1);
      lcd.print("MQ9: ");
      if (ratio > 0.9)         lcd.print("Excelent");
      else if (ratio > 0.5)    lcd.print("Atentie!");
      else if (ratio > 0.2)    lcd.print("MODERAT ");
      else                     lcd.print("PERICOL!");
      
      if (mesajAfisare.length() > 0) screen = 2;
      else screen = 0;
    } 
    else if (screen == 2) {
      lcd.setCursor(0, 0);
      lcd.print(buildPage(mesajAfisare, scrollPg * 2, 16));
      lcd.setCursor(0, 1);
      lcd.print(buildPage(mesajAfisare, scrollPg * 2 + 1, 16));
      scrollPg++;
      if (scrollPg >= totalPages) {
        screen = 0; 
        scrollPg = 0;
      }
    }
  }
} // Aceasta este acolada finală care închide loop-ul