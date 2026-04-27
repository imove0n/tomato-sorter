/*
 * Tomato Sorter v2.0 — Servo Calibration Sketch
 *
 * Purpose: dial in the exact angles for Servo 1 (gate)
 * before locking them in config/settings.yaml.
 *
 * Wiring:
 *   Servo signal (orange/yellow) -> Arduino pin 9
 *   Servo VCC    (red)           -> external 5V PSU on breadboard 2
 *   Servo GND    (brown/black)   -> breadboard 2 GND (common with Arduino GND)
 *
 * Serial protocol (9600 baud, newline-terminated):
 *   A:<deg>     move servo to angle (0-180)
 *   SWEEP       slow sweep 0 -> 180 -> 0 (visual check)
 *   STATUS      report current angle
 *
 * Examples:
 *   A:0     full one direction
 *   A:90    middle
 *   A:180   full other direction
 */

#include <Servo.h>

const int  SERVO1_PIN = 9;
const long BAUD       = 9600;

Servo gate;
int   currentAngle = 90;

void setup() {
  Serial.begin(BAUD);
  gate.attach(SERVO1_PIN);
  gate.write(currentAngle);
  delay(300);
  Serial.println("BOOT: Servo calibrate ready (pin 9). Default 90 deg.");
  Serial.println("CMD: A:<0-180>  SWEEP  STATUS");
}

void moveTo(int deg) {
  deg = constrain(deg, 0, 180);
  gate.write(deg);
  currentAngle = deg;
  Serial.print("MOVED: ");
  Serial.println(deg);
}

void sweep() {
  Serial.println("SWEEP: 0 -> 180");
  for (int a = 0; a <= 180; a += 5) {
    gate.write(a);
    delay(40);
  }
  Serial.println("SWEEP: 180 -> 0");
  for (int a = 180; a >= 0; a -= 5) {
    gate.write(a);
    delay(40);
  }
  gate.write(currentAngle);
  Serial.print("SWEEP_DONE. Returned to ");
  Serial.println(currentAngle);
}

void loop() {
  if (!Serial.available()) return;

  String cmd = Serial.readStringUntil('\n');
  cmd.trim();
  if (cmd.length() == 0) return;

  if (cmd.startsWith("A:")) {
    int deg = cmd.substring(2).toInt();
    moveTo(deg);
  } else if (cmd == "SWEEP") {
    sweep();
  } else if (cmd == "STATUS") {
    Serial.print("ANGLE: ");
    Serial.println(currentAngle);
  } else {
    Serial.print("UNKNOWN: ");
    Serial.println(cmd);
  }
}
