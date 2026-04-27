/*
 * Tomato Sorter v2.0 — IR Sensor Test Sketch
 *
 * Wiring:
 *   IR VCC -> Arduino 5V
 *   IR GND -> Arduino GND
 *   IR OUT -> Arduino pin 2  (interrupt-capable)
 *
 * Behavior:
 *   - Reports state changes only (not continuous spam)
 *   - Most modules: HIGH = clear, LOW = something detected
 *     We auto-detect both polarities and just report TRIGGERED / CLEAR
 *   - Built-in LED mirrors the trigger state for quick visual debug
 *
 * Serial protocol (9600 baud):
 *   IR:TRIGGERED   - object detected in front of sensor
 *   IR:CLEAR       - no object
 *   STATUS         - on demand, prints current state
 */

const int  IR_PIN = 2;
const int  LED    = LED_BUILTIN;
const long BAUD   = 9600;

int lastState     = -1;     // forces first-loop print
unsigned long lastChange = 0;
const unsigned long DEBOUNCE_MS = 30;

void setup() {
  pinMode(IR_PIN, INPUT);
  pinMode(LED, OUTPUT);
  Serial.begin(BAUD);
  delay(200);
  Serial.println("BOOT: IR sensor test ready (pin 2)");
  Serial.println("Wave hand or pass tomato in front of sensor");
}

void loop() {
  // Check for STATUS command
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd == "STATUS") {
      int s = digitalRead(IR_PIN);
      Serial.print("STATUS: pin=");
      Serial.print(s);
      Serial.print(" -> ");
      Serial.println(s == LOW ? "TRIGGERED (LOW)" : "CLEAR (HIGH)");
    }
  }

  int s = digitalRead(IR_PIN);

  // Report only on state change, with debounce
  if (s != lastState && (millis() - lastChange) > DEBOUNCE_MS) {
    lastState  = s;
    lastChange = millis();

    // Most IR modules: LOW means triggered. We'll report both polarities
    // explicitly so the Pi side doesn't have to guess.
    if (s == LOW) {
      Serial.println("IR:TRIGGERED");
      digitalWrite(LED, HIGH);
    } else {
      Serial.println("IR:CLEAR");
      digitalWrite(LED, LOW);
    }
  }
}
