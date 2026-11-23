#include <WiFi.h>
#include <WebServer.h>

// ─── UPDATE THESE ────────────────────────────────────────────
const char* WIFI_SSID     = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
// ─────────────────────────────────────────────────────────────

#define VALVE_LED 2          // Built-in LED on most ESP32 boards

WebServer server(80);
bool valveOpen = false;

// ── Helpers ──────────────────────────────────────────────────

void setValve(bool open) {
  valveOpen = open;
  digitalWrite(VALVE_LED, open ? HIGH : LOW);
  Serial.println(open ? "[VALVE] >>> OPEN <<<" : "[VALVE] --- CLOSED ---");
}

void sendJSON(String body) {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send(200, "application/json", body);
}

// ── Routes ───────────────────────────────────────────────────

void handleOpen() {
  setValve(true);
  sendJSON("{\"valve\":\"open\",\"message\":\"Blockchain delivery confirmed — valve opened\"}");
}

void handleClose() {
  setValve(false);
  sendJSON("{\"valve\":\"closed\",\"message\":\"Valve closed\"}");
}

void handleStatus() {
  String body = "{\"valve\":\"" + String(valveOpen ? "open" : "closed") + "\"}";
  sendJSON(body);
}

// ── Setup ────────────────────────────────────────────────────

void setup() {
  Serial.begin(115200);
  Serial.println("\n=== ESP32 Smart Solenoid Valve ===");

  pinMode(VALVE_LED, OUTPUT);
  setValve(false);   // Start closed

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("[WiFi] Connecting");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); Serial.print(".");
  }

  Serial.println("\n[WiFi] Connected!");
  Serial.print("[WiFi] IP Address: ");
  Serial.println(WiFi.localIP());   // <- Copy this into valve.py

  server.on("/open",   HTTP_GET, handleOpen);
  server.on("/close",  HTTP_GET, handleClose);
  server.on("/status", HTTP_GET, handleStatus);
  server.begin();

  Serial.println("[HTTP] Server ready");
  Serial.println("==================================");
}

// ── Loop ─────────────────────────────────────────────────────

void loop() {
  server.handleClient();
}
