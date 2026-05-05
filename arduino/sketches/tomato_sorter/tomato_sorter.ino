/*
 * ============================================================
 * Tomato Sorter v2.0 — Final Production Firmware
 * ============================================================
 *
 * Single firmware that handles all Arduino-side hardware:
 *   - Servo 1 (gate)        - pin 9   PWM
 *   - Servo 2 (sorter)      - pin 10  PWM
 *   - Servo 3 (sorter flap) - pin 11  PWM
 *   - Servo 4               - pin 8   PWM
 *   - IR sensor             - pin 2   (interrupt-capable)
 *   - Relay 1 (Fan 1)       - pin 4   (active LOW)
 *   - Relay 2 (Fan 2)       - pin 7   (active LOW)
 *
 * Boot defaults:
 *   - Servo 1 = CLOSED (0 deg)
 *   - Servo 2 + Servo 3 = OPEN saved positions (safe startup/rest position)
 *   - Relay 1 = ON  (Fan 1 spinning)
 *   - Relay 2 = ON  (Fan 2 spinning)
 *
 * Serial protocol (9600 baud, newline-terminated):
 *
 *   Pi -> Arduino:
 *     SERVO1:OPEN          - gate opens, releases 1 tomato
 *     SERVO1:CLOSE         - gate closes
 *     SERVO4:OPEN          - servo 4 opens
 *     SERVO4:CLOSE         - servo 4 closes
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
 *     SERVO1:DONE          - gate movement complete
 *     SERVO4:DONE          - servo 4 movement complete
 *     SERVO2:DONE          - sorter movement complete
 *     READY                - boot complete
 */

#include <Servo.h>

// -------------------- Pin assignments --------------------
const int  SERVO1_PIN = 9;      // gate
const int  SERVO2_PIN = 10;     // sorter
const int  SERVO3_PIN = 11;     // sorter flap 3
const int  SERVO4_PIN = 8;      // servo 4
const int  IR_PIN     = 2;      // interrupt-capable
const int  RELAY1_PIN = 4;      // fan 1
const int  RELAY2_PIN = 7;      // fan 2

// -------------------- Calibrated angles (from config/servo_angles.json)
const int GATE_CLOSED   = 0;
const int GATE_OPEN     = 50;
const int SERVO4_CLOSED = 95;   // saved servo4_closed
const int SERVO4_OPEN   = 0;    // saved servo4_open

const int SORT2_OPEN    = 0;    // saved servo2_open
const int SORT2_CLOSED  = 89;   // saved servo2_closed
const int SORT3_OPEN    = 90;   // saved servo3_open
const int SORT3_CLOSED  = 0;    // saved servo3_closed

// -------------------- Relay polarity --------------------
const int RELAY_ON  = LOW;      // active LOW module
const int RELAY_OFF = HIGH;

// -------------------- Timing --------------------
const int  GATE_OPEN_HOLD_MS   = 250;   // how long gate stays open per drop
const int  SERVO_SETTLE_MS     = 400;   // wait for servo to physically reach target
const unsigned long IR_DEBOUNCE_MS = 30;
const long BAUD = 9600;

// -------------------- State --------------------
Servo gate;
Servo sorter;
Servo sorter3;
Servo servo4;

int  gateAngle    = GATE_CLOSED;
int  sorterAngle  = SORT2_OPEN;
int  sorter3Angle = SORT3_OPEN;
int  servo4Angle  = SERVO4_OPEN;
bool relay1On     = true;       // default ON at boot
bool relay2On     = true;       // default ON at boot

int           lastIrState = HIGH;
unsigned long lastIrChange = 0;

// ====================================================
// Helpers
// ====================================================
void moveGate(int deg) {
  gate.write(deg);
  gateAngle = deg;
  delay(SERVO_SETTLE_MS);
  Serial.println("SERVO1:DONE");
}

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
  pinMode(IR_PIN, INPUT);

  // Serial
  Serial.begin(BAUD);
  delay(200);

  // Servos -> safe startup positions
  gate.attach(SERVO1_PIN);
  sorter.attach(SERVO2_PIN);
  sorter3.attach(SERVO3_PIN);
  servo4.attach(SERVO4_PIN);
  gate.write(GATE_CLOSED);
  sorter.write(SORT2_OPEN);
  sorter3.write(SORT3_OPEN);
  servo4.write(SERVO4_OPEN);
  delay(SERVO_SETTLE_MS);

  // Fans default ON
  setRelay1(true);
  setRelay2(true);

  Serial.println("READY");
  Serial.print("BOOT: gate="); Serial.print(gateAngle);
  Serial.print(" sorter=");    Serial.print(sorterAngle);
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

  // Servo 1 (gate)
  if      (cmd == "SERVO1:OPEN")  moveGate(GATE_OPEN);
  else if (cmd == "SERVO1:CLOSE") moveGate(GATE_CLOSED);

  // Servo 4
  else if (cmd == "SERVO4:OPEN")  moveServo4(SERVO4_OPEN);
  else if (cmd == "SERVO4:CLOSE") moveServo4(SERVO4_CLOSED);

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
    Serial.print("STATUS: gate=");
    Serial.print(gateAngle);
    Serial.print(" sorter=");
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
  int s = digitalRead(IR_PIN);
  if (s != lastIrState && (millis() - lastIrChange) > IR_DEBOUNCE_MS) {
    lastIrState  = s;
    lastIrChange = millis();
    if (s == LOW) Serial.println("IR:TRIGGERED");
    else          Serial.println("IR:CLEAR");
  }
}

void loop() {
  handleSerial();
  handleIR();
}
