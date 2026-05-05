/*
 * Tomato Sorter v2.0 — Servo 2 + Servo 3 + Servo 4 Calibration Sketch
 *
 * Servo 1 is held closed. Servo 2 + 3 act as a flap pair:
 *   Servo 2 CLOSED + Servo 3 OPEN   → tomato goes to RIPE bin
 *   Servo 2 OPEN   + Servo 3 CLOSED → tomato goes to UNRIPE bin
 *   Servo 2 OPEN   + Servo 3 OPEN   → tomato goes to ROTTEN bin
 *   Servo 2 CLOSED + Servo 3 CLOSED → INVALID (blocks tomato)
 *
 * Wiring:
 *   Servo 1 → Arduino pin 9   (gate, held closed)
 *   Servo 2 → Arduino pin 10
 *   Servo 3 → Arduino pin 11
 *   Servo 4 → Arduino pin 8
 *
 * Serial protocol (9600 baud):
 *   B:<deg>     move Servo 2 to angle
 *   C:<deg>     move Servo 3 to angle
 *   D:<deg>     move Servo 4 to angle
 *   A:<deg>     move Servo 1 (gate)
 *   SWEEP2      Servo 2 sweep
 *   SWEEP3      Servo 3 sweep
 *   SWEEP4      Servo 4 sweep
 *   PULSE3      detach Servo 3 and toggle pin 11 HIGH/LOW for signal testing
 *   PULSE4      detach Servo 4 and toggle pin 8 HIGH/LOW for signal testing
 *   STATUS      report current angles
 */

#include <Servo.h>

const int  SERVO1_PIN = 9;     // gate
const int  SERVO2_PIN = 10;    // sorter flap 2
const int  SERVO3_PIN = 11;    // sorter flap 3
const int  SERVO4_PIN = 8;     // servo 4
const long BAUD       = 9600;

Servo gate;
Servo flap2;
Servo flap3;
Servo servo4;

// Keep these in sync with config/servo_angles.json saved positions.
const int SERVO2_OPEN = 0;
const int SERVO3_OPEN = 90;
const int SERVO4_OPEN = 90;

int gateAngle  = 0;
int s2Angle    = SERVO2_OPEN;
int s3Angle    = SERVO3_OPEN;
int s4Angle    = SERVO4_OPEN;

void setup() {
  Serial.begin(BAUD);
  gate.attach(SERVO1_PIN);
  flap2.attach(SERVO2_PIN);
  flap3.attach(SERVO3_PIN);
  servo4.attach(SERVO4_PIN);
  gate.write(gateAngle);
  flap2.write(s2Angle);
  flap3.write(s3Angle);
  servo4.write(s4Angle);
  delay(400);
  Serial.println("BOOT: Servo 2+3+4 calibrate ready");
  Serial.print("INIT: gate="); Serial.print(gateAngle);
  Serial.print(" servo2="); Serial.print(s2Angle);
  Serial.print(" servo3="); Serial.print(s3Angle);
  Serial.print(" servo4="); Serial.println(s4Angle);
  Serial.println("CMD: B:<deg> C:<deg> D:<deg> A:<deg> SWEEP2 SWEEP3 SWEEP4 PULSE3 PULSE4 STATUS");
}

void moveServo(Servo &s, int &angle, int deg, char which) {
  deg = constrain(deg, 0, 180);
  s.write(deg);
  angle = deg;
  Serial.print("SERVO");
  Serial.print(which);
  Serial.print(": ");
  Serial.println(deg);
}

void sweep(Servo &s, int &angle, char which) {
  Serial.print("SWEEP"); Serial.println(which);
  for (int a = 0; a <= 180; a += 5) { s.write(a); delay(30); }
  for (int a = 180; a >= 0; a -= 5) { s.write(a); delay(30); }
  s.write(angle);
  Serial.println("SWEEP_DONE");
}

void pulsePin11() {
  Serial.println("PULSE3: pin 11 HIGH/LOW x10");
  flap3.detach();
  pinMode(SERVO3_PIN, OUTPUT);
  for (int i = 0; i < 10; i++) {
    digitalWrite(SERVO3_PIN, HIGH);
    delay(250);
    digitalWrite(SERVO3_PIN, LOW);
    delay(250);
  }
  flap3.attach(SERVO3_PIN);
  flap3.write(s3Angle);
  Serial.println("PULSE_DONE");
}

void pulsePin6() {
  Serial.println("PULSE4: pin 8 HIGH/LOW x10");
  servo4.detach();
  pinMode(SERVO4_PIN, OUTPUT);
  for (int i = 0; i < 10; i++) {
    digitalWrite(SERVO4_PIN, HIGH);
    delay(250);
    digitalWrite(SERVO4_PIN, LOW);
    delay(250);
  }
  servo4.attach(SERVO4_PIN);
  servo4.write(s4Angle);
  Serial.println("PULSE_DONE");
}

void loop() {
  if (!Serial.available()) return;
  String cmd = Serial.readStringUntil('\n');
  cmd.trim();
  if (cmd.length() == 0) return;

  if      (cmd.startsWith("B:")) moveServo(flap2, s2Angle, cmd.substring(2).toInt(), '2');
  else if (cmd.startsWith("C:")) moveServo(flap3, s3Angle, cmd.substring(2).toInt(), '3');
  else if (cmd.startsWith("D:")) moveServo(servo4, s4Angle, cmd.substring(2).toInt(), '4');
  else if (cmd.startsWith("A:")) moveServo(gate,  gateAngle, cmd.substring(2).toInt(), '1');
  else if (cmd == "SWEEP2") sweep(flap2, s2Angle, '2');
  else if (cmd == "SWEEP3") sweep(flap3, s3Angle, '3');
  else if (cmd == "SWEEP4") sweep(servo4, s4Angle, '4');
  else if (cmd == "PULSE3") pulsePin11();
  else if (cmd == "PULSE4") pulsePin6();
  else if (cmd == "STATUS") {
    Serial.print("STATUS: gate=");   Serial.print(gateAngle);
    Serial.print(" servo2=");        Serial.print(s2Angle);
    Serial.print(" servo3=");        Serial.print(s3Angle);
    Serial.print(" servo4=");        Serial.println(s4Angle);
  } else {
    Serial.print("UNKNOWN: "); Serial.println(cmd);
  }
}
