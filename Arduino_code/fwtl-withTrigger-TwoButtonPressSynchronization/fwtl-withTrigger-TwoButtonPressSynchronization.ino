#include <EEPROM.h>

// === Pin Definitions ===
const int redN = 22, yellowN = 24, greenN = 26;
const int redS = 28, yellowS = 30, greenS = 32;
const int redE = 34, yellowE = 36, greenE = 38;
const int redW = 40, yellowW = 42, greenW = 44;

// === Timing Parameters ===
const unsigned long greenTimeDefault = 5000;
const unsigned long greenExtension = 5000;
const unsigned long yellowTime = 2000;
const unsigned long redBuffer = 5000;

// === Globals ===
bool extendNSGreen = false;
bool extendEWGreen = false;

void setup() {
  // Set all pins to output and turn off
  int pins[] = {redN, yellowN, greenN, redS, yellowS, greenS, redE, yellowE, greenE, redW, yellowW, greenW};
  for (int i = 0; i < 12; i++) {
    pinMode(pins[i], OUTPUT);
    digitalWrite(pins[i], LOW);
  }

  Serial.begin(9600);
  delay(2000); // Wait for Serial to initialize

  // === EEPROM Reset Count Logic ===
  byte resetCount = EEPROM.read(0);

  if (resetCount < 1) {
    EEPROM.write(0, 1);  // First reset
    Serial.println("🔁 First reset detected. Press reset again to start.");
    while (true);        // Halt here
  }

  // Second reset: Send START and reset counter
  EEPROM.write(0, 0);    // Reset counter for future use
  Serial.println("START");
  Serial.println("✅ Arduino started. Waiting for triggers...");
}

void loop() {
  extendNSGreen = false;
  extendEWGreen = false;

  // === NORTH-SOUTH GREEN ===
  digitalWrite(redE, HIGH); digitalWrite(redW, HIGH);
  digitalWrite(greenN, HIGH); digitalWrite(greenS, HIGH);
  digitalWrite(redN, LOW); digitalWrite(redS, LOW);

  unsigned long greenTime = greenTimeDefault;
  if (extendNSGreen) greenTime += greenExtension;
  delay(greenTime);

  // === NORTH-SOUTH YELLOW ===
  digitalWrite(greenN, LOW); digitalWrite(greenS, LOW);
  digitalWrite(yellowN, HIGH); digitalWrite(yellowS, HIGH);
  delay(yellowTime);
  digitalWrite(yellowN, LOW); digitalWrite(yellowS, LOW);
  digitalWrite(redN, HIGH); digitalWrite(redS, HIGH);
  delay(redBuffer);

  listenForTrigger(&extendNSGreen, &extendEWGreen);

  // === EAST-WEST GREEN ===
  digitalWrite(redN, HIGH); digitalWrite(redS, HIGH);
  digitalWrite(greenE, HIGH); digitalWrite(greenW, HIGH);
  digitalWrite(redE, LOW); digitalWrite(redW, LOW);

  greenTime = greenTimeDefault;
  if (extendEWGreen) greenTime += greenExtension;
  delay(greenTime);

  // === EAST-WEST YELLOW ===
  digitalWrite(greenE, LOW); digitalWrite(greenW, LOW);
  digitalWrite(yellowE, HIGH); digitalWrite(yellowW, HIGH);
  delay(yellowTime);
  digitalWrite(yellowE, LOW); digitalWrite(yellowW, LOW);
  digitalWrite(redE, HIGH); digitalWrite(redW, HIGH);
  delay(redBuffer);

  listenForTrigger(&extendNSGreen, &extendEWGreen);
}

// === Trigger Listener ===
void listenForTrigger(bool* nsTriggerFlag, bool* ewTriggerFlag) {
  unsigned long start = millis();
  while (millis() - start < redBuffer) {
    if (Serial.available()) {
      String message = Serial.readStringUntil('\n');
      message.trim();

      if (message.startsWith("NS=")) {
        int nsIndex = message.indexOf("NS=");
        int ewIndex = message.indexOf("EW=");
        if (nsIndex != -1 && ewIndex != -1) {
          int nsVal = message.substring(nsIndex + 3, message.indexOf(',', nsIndex)).toInt();
          int ewVal = message.substring(ewIndex + 3).toInt();

          *nsTriggerFlag = (nsVal == 1);
          *ewTriggerFlag = (ewVal == 1);

          Serial.println(*nsTriggerFlag ? "EXTEND" : "DEFAULT");
          Serial.println(*ewTriggerFlag ? "EXTEND" : "DEFAULT");
        }
      }
    }
  }
}
