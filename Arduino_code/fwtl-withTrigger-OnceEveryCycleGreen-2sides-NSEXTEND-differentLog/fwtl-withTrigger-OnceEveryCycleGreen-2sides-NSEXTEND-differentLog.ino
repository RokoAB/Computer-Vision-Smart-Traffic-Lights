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
const unsigned long greenTimeDefault = 12000;
const unsigned long greenExtension = 5000;
const unsigned long yellowTime = 3000;
const unsigned long redBuffer = 15000;

// === Globals ===
bool extendNSGreen = false;
bool extendEWGreen = false;
bool startSignalReceived = false;

void setup() {
  int pins[] = {redN, yellowN, greenN, redS, yellowS, greenS, redE, yellowE, greenE, redW, yellowW, greenW};
  for (int i = 0; i < 12; i++) {
    pinMode(pins[i], OUTPUT);
  }
  Serial.begin(9600);
}

void loop() {
  // === Wait for START signal before beginning any cycle ===
  if (!startSignalReceived) {
    if (Serial.available()) {
      String msg = Serial.readStringUntil('\n');
      msg.trim();
      if (msg.equalsIgnoreCase("START")) {
        startSignalReceived = true;
      }
    }
    return;
  }

  // === NORTH-SOUTH GREEN, EAST-WEST RED ===
  digitalWrite(redE, HIGH);
  digitalWrite(redW, HIGH);
  digitalWrite(greenN, HIGH);
  digitalWrite(greenS, HIGH);
  digitalWrite(redN, LOW);
  digitalWrite(redS, LOW);

  unsigned long greenTime = greenTimeDefault;
  if (extendNSGreen) {
    greenTime += greenExtension;
    extendNSGreen = false;
  }
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

  // === Listen for Trigger During RED (affects EW green) ===
  listenForTrigger(&extendNSGreen, &extendEWGreen);

  // === EAST-WEST GREEN, NORTH-SOUTH RED ===
  digitalWrite(redN, HIGH);
  digitalWrite(redS, HIGH);
  digitalWrite(greenE, HIGH);
  digitalWrite(greenW, HIGH);
  digitalWrite(redE, LOW);
  digitalWrite(redW, LOW);

  greenTime = greenTimeDefault;
  if (extendEWGreen) {
    greenTime += greenExtension;
    extendEWGreen = false;
  }
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

  // === Listen for Trigger During RED (affects next NS green) ===
  listenForTrigger(&extendNSGreen, &extendEWGreen);
}

// === Listen for Trigger Function ===
void listenForTrigger(bool* nsTriggerFlag, bool* ewTriggerFlag) {
  unsigned long start = millis();
  while (millis() - start < redBuffer) {
    if (Serial.available()) {
      String message = Serial.readStringUntil('\n');
      message.trim();

      if (message.equalsIgnoreCase("START")) {
        startSignalReceived = true;
        continue;
      }

      if (message.startsWith("NS=")) {
        int commaIndex = message.indexOf(',');
        if (commaIndex != -1) {
          int nsVal = message.substring(3, commaIndex).toInt();
          int ewVal = message.substring(commaIndex + 4).toInt(); // Skip "EW="

          *nsTriggerFlag = (nsVal == 1);
          *ewTriggerFlag = (ewVal == 1);

          // Immediate decision logic and response
          if (nsVal == 1 && ewVal == 0) {
            Serial.println("NSEXTEND");
          } else if (nsVal == 0 && ewVal == 1) {
            Serial.println("EWEXTEND");
          } else {
            Serial.println("DEFAULT");
          }
        }
      }
    }
  }
}
