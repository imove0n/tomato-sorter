/*
 * Tomato Sorter v2.0 — Servo 3 Calibration Sketch
 *
 * This sketch intentionally does NOT attach or write Servo 2.
 * Use it when Servo 2 is already open and must stay still while calibrating Servo 3.
 *
 * Wiring:
 *   Servo 3 signal -> Arduino pin 11
 *
 * Serial protocol (9600 baud, newline-terminated):
 *   C:<deg>     move Servo 3 to angle (0-180)
 *   SWEEP       slow sweep of Servo 3
 *   STATUS      report current angle
 */

#include <Servo.h>

const int  SERVO3_PIN = 11;
const long BAUD       = 9600;
const int  SERVO3_OPEN = 90;   // keep in sync with config/servo_angles.json servo3_open

Servo flap3;

int s3Angle = SERVO3_OPEN;

void setup() {
  Serial.begin(BAUD);
  flap3.attach(SERVO3_PIN);
  flap3.write(s3Angle);
  delay(300);
  Serial.println("BOOT: Servo 3 calibrate ready (pin 11). Servo 2 untouched.");
  Serial.print("INIT: servo3=");
  Serial.println(s3Angle);
  Serial.println("CMD: C:<0-180>  SWEEP  STATUS");
}

void moveServo3(int deg) {
  deg = constrain(deg, 0, 180);
  flap3.write(deg);
  s3Angle = deg;
  Serial.print("SERVO3: ");
  Serial.println(deg);
}

void sweepServo3() {
  Serial.println("SWEEP: 0 -> 180");
  for (int a = 0; a <= 180; a += 5) {
    flap3.write(a);
    delay(40);
  }
  Serial.println("SWEEP: 180 -> 0");
  for (int a = 180; a >= 0; a -= 5) {
    flap3.write(a);
    delay(40);
  }
  flap3.write(s3Angle);
  Serial.print("SWEEP_DONE. Returned to ");
  Serial.println(s3Angle);
}

void loop() {
  if (!Serial.available()) return;

  String cmd = Serial.readStringUntil('\n');
  cmd.trim();
  if (cmd.length() == 0) return;

  if (cmd.startsWith("C:")) {
    moveServo3(cmd.substring(2).toInt());
  } else if (cmd == "SWEEP") {
    sweepServo3();
  } else if (cmd == "STATUS") {
    Serial.print("STATUS: servo3=");
    Serial.println(s3Angle);
  } else {
    Serial.print("UNKNOWN: ");
    Serial.println(cmd);
  }
}
