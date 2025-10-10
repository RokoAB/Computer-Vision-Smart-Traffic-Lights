#include <EEPROM.h>

// === Pin Definitions ===
// North
const int redN = 22;
const int yellowN = 24;
const int greenN = 26;
// South
const int redS = 28;
const int yellowS = 30;
const int greenS = 32;
// East
const int redE = 34;
const int yellowE = 36;
const int greenE = 38;
// West
const int redW = 40;
const int yellowW = 42;
const int greenW = 44;

// === Timing Parameters ===
const unsigned long greenTimeDefault = 5000;
const unsigned long greenExtension = 5000;
const unsigned long yellowTime = 2000;
const unsigned long redBuffer = 5000;

// === Globals ===
bool extendNSGreen = false;
bool extendEWGreen = false;

void setup() {
  int pins[] = {redN, yellowN, greenN, redS, yellowS, greenS, redE, yellowE, greenE, redW, yellowW, greenW};
  for (int i = 0; i < 12; i++) {
    pinMode(pins[i], OUTPUT);
    digitalWrite(pins[i], LOW);  // Ensure all lights are off initially
  }

  Serial.begin(9600);
  delay(2000); // Allow serial to initialize

  byte flag = EEPROM.read(0);

  if (flag == 0) {
    // First boot or power-up — wait for reset
    Serial.println("🔁 Waiting for reset to start...");
    EEPROM.write(0, 1); // Set flag so next boot sends START
    while (true);       // Halt until reset button is pressed
  }
  if (flag == 1) {
  // Reset flag for future restarts
    EEPROM.write(0, 0);
  
    Serial.println("START");  // Notify Raspberry Pi we're ready
    Serial.println("✅ Arduino started. Waiting for triggers...");
  }
  }

void loop() {
  extendNSGreen = false;
  extendEWGreen = false;

  // === NORTH-SOUTH GREEN, EAST-WEST RED ===
  digitalWrite(redE, HIGH);
  digitalWrite(redW, HIGH);
  digitalWrite(greenN, HIGH);
  digitalWrite(greenS, HIGH);
  digitalWrite(redN, LOW);
  digitalWrite(redS, LOW);

  unsigned long greenTime = greenTimeDefault;
  if (extendNSGreen) greenTime += greenExtension;
  delay(greenTime);

  // === NORTH-SOUTH YELLOW ===
  digitalWrite(greenN, LOW);
  digitalWrite(greenS, LOW);
  digitalWrite(yellowN, HIGH);
  digitalWrite(yellowS, HIGH);
  delay(yellowTime);
  digitalWrite(yellowN, LOW);
  digitalWrite(yellowS, LOW);
  digitalWrite(redN, HIGH);
  digitalWrite(redS, HIGH);
  delay(redBuffer);

  listenForTrigger(&extendNSGreen, &extendEWGreen);

  // === EAST-WEST GREEN, NORTH-SOUTH RED ===
  digitalWrite(redN, HIGH);
  digitalWrite(redS, HIGH);
  digitalWrite(greenE, HIGH);
  digitalWrite(greenW, HIGH);
  digitalWrite(redE, LOW);
  digitalWrite(redW, LOW);

  greenTime = greenTimeDefault;
  if (extendEWGreen) greenTime += greenExtension;
  delay(greenTime);

  // === EAST-WEST YELLOW ===
  digitalWrite(greenE, LOW);
  digitalWrite(greenW, LOW);
  digitalWrite(yellowE, HIGH);
  digitalWrite(yellowW, HIGH);
  delay(yellowTime);
  digitalWrite(yellowE, LOW);
  digitalWrite(yellowW, LOW);
  digitalWrite(redE, HIGH);
  digitalWrite(redW, HIGH);
  delay(redBuffer);

  listenForTrigger(&extendNSGreen, &extendEWGreen);
}

// === Listen for Trigger Function ===
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
