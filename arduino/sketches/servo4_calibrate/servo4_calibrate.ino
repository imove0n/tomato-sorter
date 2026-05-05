/*
 * Tomato Sorter v2.0 — Servo 4 Calibration Sketch
 *
 * Wiring:
 *   Servo 4 signal -> Arduino pin 8
 *
 * Serial protocol (9600 baud, newline-terminated):
 *   D:<deg>     move Servo 4 to angle (0-180)
 *   SWEEP       slow sweep of Servo 4
 *   PULSE/PULSE4 detach servo and toggle pin 8 HIGH/LOW for signal testing
 *   STATUS      report current angle
 */

#include <Servo.h>

const int  SERVO4_PIN = 8;
const long BAUD       = 9600;
const int  SERVO4_OPEN = 90;   // update after saving servo4_open

Servo servo4;

int s4Angle = SERVO4_OPEN;

void setup() {
  Serial.begin(BAUD);
  servo4.attach(SERVO4_PIN);
  servo4.write(s4Angle);
  delay(300);
  Serial.println("BOOT: Servo 4 calibrate ready (pin 8).");
  Serial.print("INIT: servo4=");
  Serial.println(s4Angle);
  Serial.println("CMD: D:<0-180>  SWEEP  PULSE/PULSE4  STATUS");
}

void moveServo4(int deg) {
  deg = constrain(deg, 0, 180);
  servo4.write(deg);
  s4Angle = deg;
  Serial.print("SERVO4: ");
  Serial.println(deg);
}

void sweepServo4() {
  Serial.println("SWEEP: 0 -> 180");
  for (int a = 0; a <= 180; a += 5) {
    servo4.write(a);
    delay(40);
  }
  Serial.println("SWEEP: 180 -> 0");
  for (int a = 180; a >= 0; a -= 5) {
    servo4.write(a);
    delay(40);
  }
  servo4.write(s4Angle);
  Serial.print("SWEEP_DONE. Returned to ");
  Serial.println(s4Angle);
}

void pulsePin6() {
  Serial.println("PULSE: pin 8 HIGH/LOW x10");
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

  if (cmd.startsWith("D:")) {
    moveServo4(cmd.substring(2).toInt());
  } else if (cmd == "SWEEP") {
    sweepServo4();
  } else if (cmd == "PULSE" || cmd == "PULSE4") {
    pulsePin6();
  } else if (cmd == "STATUS") {
    Serial.print("STATUS: servo4=");
    Serial.println(s4Angle);
  } else {
    Serial.print("UNKNOWN: ");
    Serial.println(cmd);
  }
}
