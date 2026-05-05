/*
 * ============================================================
 * Tomato Sorter v2.0 — Final Production Firmware
 * ============================================================
 *
 * Single firmware that handles all Arduino-side hardware:
 *   - Servo 2 (sorter)      - pin 10  PWM
 *   - Servo 3 (sorter flap) - pin 11  PWM
 *   - Servo 4               - pin 8   PWM
 *   - IR sensor             - pin 2   (interrupt-capable)
 *   - Relay 1 (Fan 1)       - pin 4   (active LOW)
 *   - Relay 2 (Fan 2)       - pin 7   (active LOW)
 *
 * Boot defaults:
 *   - Servo 2 + Servo 3 = OPEN saved positions (safe startup/rest position)
 *   - Servo 1 = DISABLED / not attached
 *   - Relay 1 = ON  (Fan 1 spinning)
 *   - Relay 2 = ON  (Fan 2 spinning)
 *
 * Serial protocol (9600 baud, newline-terminated):
 *
 *   Pi -> Arduino:
 *     SERVO1:OPEN          - disabled (ack only, no movement)
 *     SERVO1:CLOSE         - disabled (ack only, no movement)
 *     SERVO4:OPEN          - servo 4 opens (also turns AUTO off)
 *     SERVO4:CLOSE         - servo 4 closes (also turns AUTO off)
 *     SERVO4:AUTO_ON       - start auto-oscillator (closed<->open every 3.5s)
 *     SERVO4:AUTO_OFF      - stop auto-oscillator (holds current position)
 *     SERVO2:LEFT          - RIPE:   Servo 2 closed + Servo 3 open
 *     SERVO2:CENTER        - UNRIPE: Servo 2 open + Servo 3 closed
 *     SERVO2:RIGHT         - ROTTEN: Servo 2 open + Servo 3 open
 *     RELAY1:ON | OFF      - fan 1
 *     RELAY2:ON | OFF      - fan 2
 *     PING                 - returns PONG
 *     STATUS               - returns full state
 *
 *   Arduino -> Pi (asynchronous):
 *     IR:TRIGGERED         - object detected at sort point
 *     IR:CLEAR             - object passed
 *     SERVO1:DISABLED      - gate servo retired from the system
 *     SERVO4:DONE          - servo 4 movement complete
 *     SERVO2:DONE          - sorter movement complete
 *     READY                - boot complete
 */

#include <Servo.h>

// -------------------- Pin assignments --------------------
const int  SERVO2_PIN = 10;     // sorter
const int  SERVO3_PIN = 11;     // sorter flap 3
const int  SERVO4_PIN = 8;      // servo 4
const int  IR_PIN     = 2;      // interrupt-capable
const int  RELAY1_PIN = 4;      // fan 1
const int  RELAY2_PIN = 7;      // fan 2

// -------------------- Calibrated angles (from config/servo_angles.json)
const int SERVO4_CLOSED = 0;    // saved servo4_closed
const int SERVO4_OPEN   = 75;   // saved servo4_open

const int SORT2_OPEN    = 0;    // saved servo2_open
const int SORT2_CLOSED  = 89;   // saved servo2_closed
const int SORT3_OPEN    = 90;   // saved servo3_open
const int SORT3_CLOSED  = 0;    // saved servo3_closed

// -------------------- Relay polarity --------------------
const int RELAY_ON  = LOW;      // active LOW module
const int RELAY_OFF = HIGH;

// -------------------- Timing --------------------
const int  SERVO_SETTLE_MS     = 400;   // wait for servo to physically reach target
const unsigned long IR_DEBOUNCE_MS = 30;
const unsigned long SERVO4_AUTO_INTERVAL_MS = 3500;  // toggle every 3.5s
const long BAUD = 9600;

// -------------------- State --------------------
Servo sorter;
Servo sorter3;
Servo servo4;

int  sorterAngle  = SORT2_OPEN;
int  sorter3Angle = SORT3_OPEN;
int  servo4Angle  = SERVO4_CLOSED;   // boot rest = closed
bool relay1On     = true;       // default ON at boot
bool relay2On     = true;       // default ON at boot

// Servo 4 auto-oscillator state
bool          servo4AutoOn   = false;            // default OFF at boot — only Pi START CYCLE arms it
unsigned long servo4LastFlip = 0;

int           lastIrState = HIGH;
unsigned long lastIrChange = 0;

volatile bool irTriggerPending = false;
volatile bool irClearPending = false;

// ====================================================
// Helpers
// ====================================================
void moveSorter(int deg) {
  sorter.write(deg);
  sorterAngle = deg;
  delay(SERVO_SETTLE_MS);
  Serial.println("SERVO2:DONE");
}

void moveSorter3(int deg) {
  sorter3.write(deg);
  sorter3Angle = deg;
  delay(SERVO_SETTLE_MS);
  Serial.println("SERVO3:DONE");
}

void moveFlapsSafe(int s2Target, int s3Target) {
  // Mechanical rule: Servo 2 and Servo 3 must never both be closed.
  if (s2Target == SORT2_CLOSED && s3Target == SORT3_CLOSED) {
    Serial.println("ERROR:INVALID_FLAP_COMBO");
    return;
  }

  if (s2Target == SORT2_CLOSED) {
    moveSorter3(SORT3_OPEN);
    moveSorter(s2Target);
  } else if (s3Target == SORT3_CLOSED) {
    moveSorter(SORT2_OPEN);
    moveSorter3(s3Target);
  } else {
    moveSorter(SORT2_OPEN);
    moveSorter3(SORT3_OPEN);
  }
}

void moveServo4(int deg) {
  servo4.write(deg);
  servo4Angle = deg;
  delay(SERVO_SETTLE_MS);
  Serial.println("SERVO4:DONE");
}

void setRelay1(bool on) {
  digitalWrite(RELAY1_PIN, on ? RELAY_ON : RELAY_OFF);
  relay1On = on;
  Serial.print("RELAY1:");
  Serial.println(on ? "ON" : "OFF");
}

void setRelay2(bool on) {
  digitalWrite(RELAY2_PIN, on ? RELAY_ON : RELAY_OFF);
  relay2On = on;
  Serial.print("RELAY2:");
  Serial.println(on ? "ON" : "OFF");
}

void onIrChange() {
  if (digitalRead(IR_PIN) == LOW) {
    irTriggerPending = true;
  } else {
    irClearPending = true;
  }
}

// ====================================================
// Setup / Loop
// ====================================================
void setup() {
  // Relays: drive HIGH/OFF first to avoid spurious click on boot
  pinMode(RELAY1_PIN, OUTPUT);
  pinMode(RELAY2_PIN, OUTPUT);
  digitalWrite(RELAY1_PIN, RELAY_OFF);
  digitalWrite(RELAY2_PIN, RELAY_OFF);

  // IR sensor
  pinMode(IR_PIN, INPUT_PULLUP);
  lastIrState = digitalRead(IR_PIN);
  attachInterrupt(digitalPinToInterrupt(IR_PIN), onIrChange, CHANGE);

  // Serial
  Serial.begin(BAUD);
  delay(200);

  // Servos -> safe startup positions
  sorter.attach(SERVO2_PIN);
  sorter3.attach(SERVO3_PIN);
  servo4.attach(SERVO4_PIN);
  sorter.write(SORT2_OPEN);
  sorter3.write(SORT3_OPEN);
  servo4.write(SERVO4_CLOSED);   // boot in CLOSED rest position
  delay(SERVO_SETTLE_MS);
  servo4LastFlip = millis();

  // Fans default ON
  setRelay1(true);
  setRelay2(true);

  Serial.println("READY");
  Serial.print("BOOT: sorter="); Serial.print(sorterAngle);
  Serial.print(" sorter3=");   Serial.print(sorter3Angle);
  Serial.print(" servo4=");    Serial.print(servo4Angle);
  Serial.print(" relay1=");    Serial.print(relay1On ? "ON" : "OFF");
  Serial.print(" relay2=");    Serial.println(relay2On ? "ON" : "OFF");
}

void handleSerial() {
  if (!Serial.available()) return;
  String cmd = Serial.readStringUntil('\n');
  cmd.trim();
  if (cmd.length() == 0) return;

  if      (cmd == "SERVO1:OPEN" || cmd == "SERVO1:CLOSE") Serial.println("SERVO1:DISABLED");

  // Servo 4
  else if (cmd == "SERVO4:OPEN")  { servo4AutoOn = false; moveServo4(SERVO4_OPEN); }
  else if (cmd == "SERVO4:CLOSE") { servo4AutoOn = false; moveServo4(SERVO4_CLOSED); }
  else if (cmd == "SERVO4:AUTO_ON") {
    servo4AutoOn   = true;
    servo4LastFlip = millis();
    moveServo4(SERVO4_CLOSED);                // start from CLOSED
    Serial.println("SERVO4:AUTO_ON");
  }
  else if (cmd == "SERVO4:AUTO_OFF") {
    servo4AutoOn = false;
    Serial.println("SERVO4:AUTO_OFF");
  }

  // Servo 2 + 3 sorter flap pair. Never command both closed.
  else if (cmd == "SERVO2:LEFT")   moveFlapsSafe(SORT2_CLOSED, SORT3_OPEN);   // ripe
  else if (cmd == "SERVO2:CENTER") moveFlapsSafe(SORT2_OPEN, SORT3_CLOSED);   // unripe
  else if (cmd == "SERVO2:RIGHT")  moveFlapsSafe(SORT2_OPEN, SORT3_OPEN);     // rotten/rest

  // Relays
  else if (cmd == "RELAY1:ON")  setRelay1(true);
  else if (cmd == "RELAY1:OFF") setRelay1(false);
  else if (cmd == "RELAY2:ON")  setRelay2(true);
  else if (cmd == "RELAY2:OFF") setRelay2(false);

  // Diagnostics
  else if (cmd == "PING") Serial.println("PONG");
  else if (cmd == "STATUS") {
    Serial.print("STATUS: sorter=");
    Serial.print(sorterAngle);
    Serial.print(" sorter3=");
    Serial.print(sorter3Angle);
    Serial.print(" servo4=");
    Serial.print(servo4Angle);
    Serial.print(" relay1=");
    Serial.print(relay1On ? "ON" : "OFF");
    Serial.print(" relay2=");
    Serial.print(relay2On ? "ON" : "OFF");
    int s = digitalRead(IR_PIN);
    Serial.print(" ir=");
    Serial.println(s == LOW ? "TRIGGERED" : "CLEAR");
  } else {
    Serial.print("UNKNOWN: ");
    Serial.println(cmd);
  }
}

void handleIR() {
  bool triggerPending;
  bool clearPending;

  noInterrupts();
  triggerPending = irTriggerPending;
  clearPending = irClearPending;
  irTriggerPending = false;
  irClearPending = false;
  interrupts();

  unsigned long now = millis();
  if (triggerPending && (lastIrState != LOW || (now - lastIrChange) > IR_DEBOUNCE_MS)) {
    lastIrState = LOW;
    lastIrChange = now;
    Serial.println("IR:TRIGGERED");
  }
  if (clearPending && (lastIrState != HIGH || (now - lastIrChange) > IR_DEBOUNCE_MS)) {
    lastIrState = HIGH;
    lastIrChange = now;
    Serial.println("IR:CLEAR");
  }
}

void handleServo4Auto() {
  if (!servo4AutoOn) return;
  if (millis() - servo4LastFlip < SERVO4_AUTO_INTERVAL_MS) return;

  // Toggle: if currently CLOSED -> OPEN, else -> CLOSED
  int target = (servo4Angle == SERVO4_CLOSED) ? SERVO4_OPEN : SERVO4_CLOSED;
  servo4.write(target);
  servo4Angle    = target;
  servo4LastFlip = millis();
  // No SERVO_SETTLE_MS delay here — keep loop() responsive to serial + IR.
}

void loop() {
  handleSerial();
  handleIR();
  handleServo4Auto();
}
