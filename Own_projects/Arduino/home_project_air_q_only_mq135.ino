#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <Adafruit_AHTX0.h>
#include <Adafruit_BMP280.h>
#include <MQ135.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

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
MQ135 mq135(A0);
WiFiClient espClient;
PubSubClient mqtt(espClient);

// ── Variabile ──────────────────────
String mesajPi     = "";      // Buffer pentru mesajul brut primit prin MQTT
String mesajAfisare = "";     // Mesajul procesat care va fi afișat pe LCD
int    screen      = 0;       // Controlul ecranului (0, 1, 2)
int    scrollPg    = 0;       // Pagina curentă a mesajului MQTT
int    totalPages  = 0;       // Total pagini calculate pentru mesaj
unsigned long lastMs = 0;     // Timer pentru schimbarea ecranelor

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

// ── Setup ─────────────────────────
void setup() {
  Serial.begin(115200);
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
  float ppm = mq135.getCorrectedPPM(temp.temperature, humidity.relative_humidity);

  // ── 2. Publicare date prin MQTT (la 10 secunde) ──
  static unsigned long lastMqttPublish = 0;
  if (millis() - lastMqttPublish >= 10000) {
    char payload[128];
    snprintf(payload, sizeof(payload),
      "{\"temp\":%.1f,\"hum\":%.0f,\"pres\":%.1f,\"ppm\":%.0f}",
      temp.temperature, humidity.relative_humidity, presiune, ppm);
    mqtt.publish(mqtt_pub_topic, payload);
    lastMqttPublish = millis();
  }

  // ── 3. Procesare mesaj nou primit ──
  if (mesajPi.length() > 0) {
    mesajAfisare = mesajPi;
    mesajPi = ""; // Eliberăm bufferul
    
    // Calculăm câte pagini (perechi de 2 linii) are mesajul
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
      // ECRAN 1: Temperatură, Umiditate, Presiune
      lcd.setCursor(0, 0);
      lcd.print("T:"); lcd.print(temp.temperature, 1);
      lcd.print("C H:"); lcd.print(humidity.relative_humidity, 0); lcd.print("%");
      lcd.setCursor(0, 1);
      lcd.print("Pres:"); lcd.print(presiune, 1); lcd.print("mb");
      
      screen = 1;
    } 
    else if (screen == 1) {
      // ECRAN 2: Calitatea Aerului
      lcd.setCursor(0, 0);
      lcd.print("Aer: "); lcd.print(ppm, 0); lcd.print("ppm");
      lcd.setCursor(0, 1);
      if (ppm < 400)      lcd.print("Excelent");
      else if (ppm < 700) lcd.print("Calitate Buna");
      else if (ppm < 1000)lcd.print("Aer Mediu");
      else                lcd.print("Poluat/Slab");
      
      // Dacă există un mesaj MQTT, mergem la ecranul 2, altfel reluăm de la 0
      if (mesajAfisare.length() > 0) screen = 2;
      else screen = 0;
    } 
    else if (screen == 2) {
      // ECRAN 3: Afișare Mesaj MQTT (paginat)
      lcd.setCursor(0, 0);
      lcd.print(buildPage(mesajAfisare, scrollPg * 2, 16));
      lcd.setCursor(0, 1);
      lcd.print(buildPage(mesajAfisare, scrollPg * 2 + 1, 16));

      scrollPg++;
      
      // Dacă am terminat toate paginile mesajului, revenim la Ecranul 1
      if (scrollPg >= totalPages) {
        screen = 0; 
        scrollPg = 0;
        // mesajAfisare = ""; // Opțional: șterge mesajul după ce a fost afișat complet o dată
      }
    }
  }
}