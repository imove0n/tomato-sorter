/*
 * Tomato Sorter v2.0 — Relay Module Test Sketch
 *
 * Wiring:
 *   Relay VCC -> Arduino 5V
 *   Relay GND -> Arduino GND
 *   Relay IN1 -> Arduino pin 4   (Fan 1 = ripe bin)
 *   Relay IN2 -> Arduino pin 7   (Fan 2 = unripe bin)
 *
 * Most relay modules are ACTIVE LOW:
 *   digitalWrite(pin, LOW)  = relay ON  (click + LED on)
 *   digitalWrite(pin, HIGH) = relay OFF
 *
 * Serial protocol (9600 baud):
 *   R1:ON   R1:OFF      Relay 1 (Fan 1)
 *   R2:ON   R2:OFF      Relay 2 (Fan 2)
 *   ALL:ON  ALL:OFF     Both relays
 *   CYCLE               Auto demo: R1 on/off, R2 on/off, both on/off
 *   STATUS              Report current relay states
 */

const int  RELAY1_PIN = 4;
const int  RELAY2_PIN = 7;
const long BAUD       = 9600;

// Active LOW relays
const int RELAY_ON  = LOW;
const int RELAY_OFF = HIGH;

bool r1State = false;
bool r2State = false;

void setRelay(int pin, bool on, int relayNum) {
  digitalWrite(pin, on ? RELAY_ON : RELAY_OFF);
  if (relayNum == 1) r1State = on;
  else               r2State = on;
  Serial.print("R");
  Serial.print(relayNum);
  Serial.print(":");
  Serial.println(on ? "ON" : "OFF");
}

void setup() {
  pinMode(RELAY1_PIN, OUTPUT);
  pinMode(RELAY2_PIN, OUTPUT);
  // Start with both relays OFF
  digitalWrite(RELAY1_PIN, RELAY_OFF);
  digitalWrite(RELAY2_PIN, RELAY_OFF);
  Serial.begin(BAUD);
  delay(200);
  Serial.println("BOOT: Relay test ready (R1=pin4, R2=pin7)");
  Serial.println("CMD: R1:ON R1:OFF R2:ON R2:OFF ALL:ON ALL:OFF CYCLE STATUS");
}

void cycle() {
  Serial.println("CYCLE: starting demo");
  setRelay(RELAY1_PIN, true,  1); delay(800);
  setRelay(RELAY1_PIN, false, 1); delay(400);
  setRelay(RELAY2_PIN, true,  2); delay(800);
  setRelay(RELAY2_PIN, false, 2); delay(400);
  setRelay(RELAY1_PIN, true,  1);
  setRelay(RELAY2_PIN, true,  2); delay(800);
  setRelay(RELAY1_PIN, false, 1);
  setRelay(RELAY2_PIN, false, 2);
  Serial.println("CYCLE: done");
}

void loop() {
  if (!Serial.available()) return;
  String cmd = Serial.readStringUntil('\n');
  cmd.trim();
  if (cmd.length() == 0) return;

  if      (cmd == "R1:ON")   setRelay(RELAY1_PIN, true,  1);
  else if (cmd == "R1:OFF")  setRelay(RELAY1_PIN, false, 1);
  else if (cmd == "R2:ON")   setRelay(RELAY2_PIN, true,  2);
  else if (cmd == "R2:OFF")  setRelay(RELAY2_PIN, false, 2);
  else if (cmd == "ALL:ON")  { setRelay(RELAY1_PIN, true,  1); setRelay(RELAY2_PIN, true,  2); }
  else if (cmd == "ALL:OFF") { setRelay(RELAY1_PIN, false, 1); setRelay(RELAY2_PIN, false, 2); }
  else if (cmd == "CYCLE")   cycle();
  else if (cmd == "STATUS") {
    Serial.print("STATUS: R1=");
    Serial.print(r1State ? "ON" : "OFF");
    Serial.print(" R2=");
    Serial.println(r2State ? "ON" : "OFF");
  }
  else {
    Serial.print("UNKNOWN: ");
    Serial.println(cmd);
  }
}
