#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN D4
#define RST_PIN D3
#define RELAY_PIN D1
#define LED_PIN D2

const char* ssid = "SSID";
const char* password = "PASSWD";

const char* serverUrl ="http://IPADDR:5000/check_card";

MFRC522 mfrc522(SS_PIN, RST_PIN);
WiFiClient client;

void setup() {
  Serial.begin(115200);
  SPI.begin();
  mfrc522.PCD_Init();

  pinMode(RELAY_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, HIGH);
  digitalWrite(LED_PIN, LOW);

  WiFi.begin(ssid, password);
  Serial.println("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");
}

void loop() {
  digitalWrite(LED_PIN,HIGH); //device is ready to read data
  if (!mfrc522.PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) {
    return;
  }

  String cardUID = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    cardUID += String(mfrc522.uid.uidByte[i], HEX);
  }

  cardUID.toUpperCase();
  Serial.println("Card UID: " + cardUID);

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(client, serverUrl);
    http.addHeader("Content-Type", "application/json");

    String postData = "{\"card_uid\":\"" + cardUID + "\"}";
    Serial.println(postData);
    int httpResponseCode = http.POST(postData);
    Serial.println(httpResponseCode);

    if (httpResponseCode > 0) {
      String payload = http.getString();
      Serial.println("Response: " + payload);

      if (payload.indexOf("true") >= 0) {
        openLock();
      } else {
        denyAccess();
      }
    } else {
      Serial.println("Error in HTTP request");
    }

    http.end();
  } else {
    Serial.println("WiFi not connected");
  }

  mfrc522.PICC_HaltA();
  delay(1000);
}

void openLock() {
  digitalWrite(RELAY_PIN, LOW);
  notifyDoorState("open");
  blinkLED(1, 100);
  delay(3000);  // 3 seconds
  digitalWrite(RELAY_PIN, HIGH);
  notifyDoorState("closed");
}

void denyAccess() {
  blinkLED(10, 100);
}

void notifyDoorState(const String& state) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(client, "http://IPADDR:5000/door_state");
    http.addHeader("Content-Type", "application/json");
    String body = "{\"state\": \"" + state + "\"}";
    int code = http.POST(body);
    Serial.println(code);
    http.end();
  }
}

void blinkLED(int times, int duration) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(duration);
    digitalWrite(LED_PIN, LOW);
    delay(duration);
  }
}
