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
const unsigned long redBuffer = 1000;

// === Globals ===
bool extendNSGreen = false;
bool extendEWGreen = false;
bool extensionUsedThisCycle = false;

void setup() {
  int pins[] = {redN, yellowN, greenN, redS, yellowS, greenS, redE, yellowE, greenE, redW, yellowW, greenW};
  for (int i = 0; i < 12; i++) {
    pinMode(pins[i], OUTPUT);
  }
  Serial.begin(9600);
}

void loop() {
  // === Reset extension tracking at start of full cycle ===
  extensionUsedThisCycle = false;

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

  // Listen for both NS and EW triggers
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

  // === Listen for Trigger During RED (affects next EW green) ===
  // Listen for both NS and EW triggers
  listenForTrigger(&extendNSGreen, &extendEWGreen);

}

  // === Listen for Trigger Function ===
  void listenForTrigger(bool* nsTriggerFlag, bool* ewTriggerFlag) {
    unsigned long start = millis();
    while (millis() - start < redBuffer) {
      if (Serial.available()) {
        String message = Serial.readStringUntil('\n');
        message.trim();
  
        // Expecting message like "NS=1,EW=0"
        if (message.startsWith("NS=")) {
          int nsIndex = message.indexOf("NS=");
          int ewIndex = message.indexOf("EW=");
          if (nsIndex != -1 && ewIndex != -1) {
            int nsVal = message.substring(nsIndex + 3, message.indexOf(',', nsIndex)).toInt();
            int ewVal = message.substring(ewIndex + 3).toInt();
  
            *nsTriggerFlag = (nsVal == 1);
            *ewTriggerFlag = (ewVal == 1);
          }
        }
      }
    }
  }
