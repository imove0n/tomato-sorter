/*
 * Tomato Sorter v2.0 — 360° Continuous Rotation Servo Calibration
 *
 * For continuous rotation servos (e.g., MG996R 360):
 *   value 0   = full speed CCW
 *   value 90  = stop (might need 88-92 fine-tune)
 *   value 180 = full speed CW
 *
 * Servo 1 (gate) on pin 9 stays closed.
 * Servo 2 + 3 are calibrated for time-based open/close.
 *
 * Wiring:
 *   Servo 1 → pin 9   (gate, held closed)
 *   Servo 2 → pin 10  (continuous rotation)
 *   Servo 3 → pin 11  (continuous rotation)
 *
 * Serial commands (9600 baud):
 *   N2:<val>          set Servo 2 neutral value (default 90)
 *   N3:<val>          set Servo 3 neutral value
 *   F2:<ms>           Servo 2 spin FORWARD (180) for <ms>, then stop
 *   R2:<ms>           Servo 2 spin REVERSE (0) for <ms>, then stop
 *   F3:<ms>           Servo 3 forward
 *   R3:<ms>           Servo 3 reverse
 *   S2 / S3           stop servo 2 or 3 immediately (sends neutral)
 *   PROBE2            tries values 85..95 to find true neutral
 *   PROBE3            same for servo 3
 *   STATUS
 */

#include <Servo.h>

const int  SERVO1_PIN = 9;
const int  SERVO2_PIN = 10;
const int  SERVO3_PIN = 11;
const long BAUD       = 9600;

Servo gate, s2, s3;

int s2Neutral = 90;
int s3Neutral = 90;

void setup() {
  Serial.begin(BAUD);
  gate.attach(SERVO1_PIN);
  s2.attach(SERVO2_PIN);
  s3.attach(SERVO3_PIN);
  gate.write(0);
  s2.write(s2Neutral);
  s3.write(s3Neutral);
  delay(400);
  Serial.println("BOOT: 360 servo calibrate ready");
  Serial.print("INIT: s2 neutral="); Serial.print(s2Neutral);
  Serial.print(" s3 neutral=");      Serial.println(s3Neutral);
}

void spinFor(Servo &srv, int speedVal, int durMs, int neutral, char which, char dir) {
  Serial.print("SPIN");
  Serial.print(which);
  Serial.print(":");
  Serial.print(dir);
  Serial.print(":");
  Serial.println(durMs);
  srv.write(speedVal);
  delay(durMs);
  srv.write(neutral);
  Serial.print("STOPPED");
  Serial.println(which);
}

void probe(Servo &srv, char which) {
  Serial.print("PROBE"); Serial.print(which); Serial.println(": testing 85..95");
  for (int v = 85; v <= 95; v++) {
    Serial.print("  trying "); Serial.println(v);
    srv.write(v);
    delay(2000);   // 2s for each value to observe
  }
  srv.write(90);
  Serial.println("PROBE_DONE — pick the value where servo stayed still");
}

void loop() {
  if (!Serial.available()) return;
  String cmd = Serial.readStringUntil('\n');
  cmd.trim();
  if (cmd.length() == 0) return;

  if (cmd.startsWith("N2:"))      { s2Neutral = cmd.substring(3).toInt(); s2.write(s2Neutral); Serial.print("N2="); Serial.println(s2Neutral); }
  else if (cmd.startsWith("N3:")) { s3Neutral = cmd.substring(3).toInt(); s3.write(s3Neutral); Serial.print("N3="); Serial.println(s3Neutral); }
  else if (cmd.startsWith("F2:")) spinFor(s2, 180, cmd.substring(3).toInt(), s2Neutral, '2', 'F');
  else if (cmd.startsWith("R2:")) spinFor(s2, 0,   cmd.substring(3).toInt(), s2Neutral, '2', 'R');
  else if (cmd.startsWith("F3:")) spinFor(s3, 180, cmd.substring(3).toInt(), s3Neutral, '3', 'F');
  else if (cmd.startsWith("R3:")) spinFor(s3, 0,   cmd.substring(3).toInt(), s3Neutral, '3', 'R');
  else if (cmd == "S2")           { s2.write(s2Neutral); Serial.println("STOPPED2"); }
  else if (cmd == "S3")           { s3.write(s3Neutral); Serial.println("STOPPED3"); }
  else if (cmd == "PROBE2")       probe(s2, '2');
  else if (cmd == "PROBE3")       probe(s3, '3');
  else if (cmd == "STATUS") {
    Serial.print("STATUS: s2_neutral="); Serial.print(s2Neutral);
    Serial.print(" s3_neutral=");        Serial.println(s3Neutral);
  }
  else { Serial.print("UNKNOWN: "); Serial.println(cmd); }
}
