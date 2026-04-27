/*
 * Tomato Sorter v2.0 — Servo 2 (Sorter) Calibration Sketch
 *
 * Servo 1 is held at its 'closed' angle the whole time so the gate
 * stays put while you dial in Servo 2's three sort positions.
 *
 * Wiring:
 *   Servo 1 signal -> Arduino pin 9   (gate, holds closed)
 *   Servo 2 signal -> Arduino pin 10  (sorter, the one we're calibrating)
 *   Both servos share +5V and GND from breadboard 2
 *
 * Serial protocol (9600 baud, newline-terminated):
 *   B:<deg>     move Servo 2 to angle (0-180)
 *   A:<deg>     move Servo 1 (gate) to angle  (default 0 = closed)
 *   SWEEP       slow sweep of Servo 2 (visual check)
 *   STATUS      report current angles
 */

#include <Servo.h>

const int  SERVO1_PIN = 9;    // gate
const int  SERVO2_PIN = 10;   // sorter
const long BAUD       = 9600;
const int  GATE_CLOSED = 0;   // matches saved closed angle

Servo gate;
Servo sorter;

int gateAngle   = GATE_CLOSED;
int sorterAngle = 90;

void setup() {
  Serial.begin(BAUD);
  gate.attach(SERVO1_PIN);
  sorter.attach(SERVO2_PIN);
  gate.write(gateAngle);
  sorter.write(sorterAngle);
  delay(300);
  Serial.println("BOOT: Servo 2 calibrate ready (pin 10).");
  Serial.print("INIT: gate=");
  Serial.print(gateAngle);
  Serial.print(" sorter=");
  Serial.println(sorterAngle);
  Serial.println("CMD: B:<0-180>  A:<0-180>  SWEEP  STATUS");
}

void moveSorter(int deg) {
  deg = constrain(deg, 0, 180);
  sorter.write(deg);
  sorterAngle = deg;
  Serial.print("SORTER: ");
  Serial.println(deg);
}

void moveGate(int deg) {
  deg = constrain(deg, 0, 180);
  gate.write(deg);
  gateAngle = deg;
  Serial.print("GATE: ");
  Serial.println(deg);
}

void sweepSorter() {
  Serial.println("SWEEP: 0 -> 180");
  for (int a = 0; a <= 180; a += 5) {
    sorter.write(a);
    delay(40);
  }
  Serial.println("SWEEP: 180 -> 0");
  for (int a = 180; a >= 0; a -= 5) {
    sorter.write(a);
    delay(40);
  }
  sorter.write(sorterAngle);
  Serial.print("SWEEP_DONE. Returned to ");
  Serial.println(sorterAngle);
}

void loop() {
  if (!Serial.available()) return;

  String cmd = Serial.readStringUntil('\n');
  cmd.trim();
  if (cmd.length() == 0) return;

  if (cmd.startsWith("B:")) {
    moveSorter(cmd.substring(2).toInt());
  } else if (cmd.startsWith("A:")) {
    moveGate(cmd.substring(2).toInt());
  } else if (cmd == "SWEEP") {
    sweepSorter();
  } else if (cmd == "STATUS") {
    Serial.print("STATUS: gate=");
    Serial.print(gateAngle);
    Serial.print(" sorter=");
    Serial.println(sorterAngle);
  } else {
    Serial.print("UNKNOWN: ");
    Serial.println(cmd);
  }
}
