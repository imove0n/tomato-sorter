/*
 * Servo Signal Finder
 *
 * Temporary diagnostic sketch. It drives one Arduino pin at a time so you can
 * discover whether the servo signal wire is really on the pin you think it is.
 *
 * Commands:
 *   P6       test Arduino D6
 *   P5       test Arduino D5
 *   P3       test Arduino D3
 *   P11      test Arduino D11
 *   P10      test Arduino D10
 *   STATUS   show active pin
 */

#include <Servo.h>

const long BAUD = 9600;

Servo testServo;
int activePin = -1;
int activeAngle = 90;

void attachPin(int pin) {
  if (activePin == pin) return;
  if (activePin >= 0) testServo.detach();
  activePin = pin;
  testServo.attach(activePin);
  testServo.write(activeAngle);
  delay(300);
  Serial.print("ATTACHED: D");
  Serial.println(activePin);
}

void movePattern() {
  if (activePin < 0) {
    Serial.println("NO_PIN");
    return;
  }
  int angles[] = {0, 90, 180, 90, 20, 160, 90};
  for (int i = 0; i < 7; i++) {
    activeAngle = angles[i];
    testServo.write(activeAngle);
    Serial.print("PIN D");
    Serial.print(activePin);
    Serial.print(" -> ");
    Serial.println(activeAngle);
    delay(700);
  }
}

void setup() {
  Serial.begin(BAUD);
  delay(300);
  Serial.println("BOOT: Servo signal finder ready");
  Serial.println("CMD: P6 P5 P3 P11 P10 STATUS");
}

void loop() {
  if (!Serial.available()) return;

  String cmd = Serial.readStringUntil('\n');
  cmd.trim();
  cmd.toUpperCase();
  if (cmd.length() == 0) return;

  if (cmd == "P6") {
    attachPin(6);
    movePattern();
  } else if (cmd == "P5") {
    attachPin(5);
    movePattern();
  } else if (cmd == "P3") {
    attachPin(3);
    movePattern();
  } else if (cmd == "P11") {
    attachPin(11);
    movePattern();
  } else if (cmd == "P10") {
    attachPin(10);
    movePattern();
  } else if (cmd == "STATUS") {
    Serial.print("STATUS: pin=");
    Serial.print(activePin);
    Serial.print(" angle=");
    Serial.println(activeAngle);
  } else {
    Serial.print("UNKNOWN: ");
    Serial.println(cmd);
  }
}
