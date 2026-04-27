/*
 * Tomato Sorter v2.0 — Serial Test Sketch
 *
 * Purpose: validate Pi <-> Arduino USB serial communication
 * before any hardware is wired up.
 *
 * Behavior:
 *   - Built-in LED blinks slowly (heartbeat)
 *   - On startup, prints a banner over Serial
 *   - Echoes any command back with "OK:<cmd>"
 *   - Special command "PING" replies with "PONG"
 *
 * Run from Pi:
 *   arduino-cli upload -p /dev/ttyUSB0 \
 *     --fqbn arduino:avr:uno arduino/sketches/serial_test
 */

const long BAUD = 9600;
const int  LED  = LED_BUILTIN;

unsigned long lastBlink = 0;
bool ledState = false;

void setup() {
  pinMode(LED, OUTPUT);
  Serial.begin(BAUD);
  delay(200);
  Serial.println("BOOT: Tomato Sorter v2.0 Arduino — serial test ready");
}

void loop() {
  // Heartbeat blink every 500ms
  if (millis() - lastBlink >= 500) {
    ledState = !ledState;
    digitalWrite(LED, ledState ? HIGH : LOW);
    lastBlink = millis();
  }

  // Read serial commands
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd.length() == 0) return;

    if (cmd == "PING") {
      Serial.println("PONG");
    } else {
      Serial.print("OK:");
      Serial.println(cmd);
    }
  }
}
