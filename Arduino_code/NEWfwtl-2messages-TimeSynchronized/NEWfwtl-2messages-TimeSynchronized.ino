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

// === Timing Parameters (in ms) ===
const unsigned long greenTimeDefault = 10000;
const unsigned long greenExtension = 5000;
const unsigned long yellowTime = 3000;
const unsigned long redBuffer = 3000;

bool extendNSGreen = false;
bool extendEWGreen = false;

void setup() {
  int pins[] = {redN, yellowN, greenN, redS, yellowS, greenS, redE, yellowE, greenE, redW, yellowW, greenW};
  for (int i = 0; i < 12; i++) {
    pinMode(pins[i], OUTPUT);
  }
  Serial.begin(9600);
}

void loop() {
  // === NORTH-SOUTH GREEN ===
  extendTraffic("NS");

  // === NORTH-SOUTH YELLOW ===
  setYellow("NS");
  delay(yellowTime);

  // === RED BUFFER + Listen for triggers ===
  allRed();
  listenForTrigger();

  // === EAST-WEST GREEN ===
  extendTraffic("EW");

  // === EAST-WEST YELLOW ===
  setYellow("EW");
  delay(yellowTime);

  // === RED BUFFER + Listen again ===
  allRed();
  listenForTrigger();
}

// === CONTROL FUNCTIONS ===

void extendTraffic(String direction) {
  // Set lights
  if (direction == "NS") {
    digitalWrite(redE, HIGH);
    digitalWrite(redW, HIGH);
    digitalWrite(greenN, HIGH);
    digitalWrite(greenS, HIGH);
    digitalWrite(redN, LOW);
    digitalWrite(redS, LOW);
  } else {
    digitalWrite(redN, HIGH);
    digitalWrite(redS, HIGH);
    digitalWrite(greenE, HIGH);
    digitalWrite(greenW, HIGH);
    digitalWrite(redE, LOW);
    digitalWrite(redW, LOW);
  }

  // Determine time
  unsigned long duration = greenTimeDefault;
  if (direction == "NS" && extendNSGreen) {
    duration += greenExtension;
    extendNSGreen = false;
  } else if (direction == "EW" && extendEWGreen) {
    duration += greenExtension;
    extendEWGreen = false;
  }

  // Inform Raspberry Pi
  Serial.print("PHASE=");
  Serial.print(direction);
  Serial.print("_GREEN;");
  Serial.print("DURATION=");
  Serial.println(duration);

  delay(duration);

  // Turn off green lights
  if (direction == "NS") {
    digitalWrite(greenN, LOW);
    digitalWrite(greenS, LOW);
  } else {
    digitalWrite(greenE, LOW);
    digitalWrite(greenW, LOW);
  }
}

void setYellow(String direction) {
  if (direction == "NS") {
    digitalWrite(yellowN, HIGH);
    digitalWrite(yellowS, HIGH);
  } else {
    digitalWrite(yellowE, HIGH);
    digitalWrite(yellowW, HIGH);
  }
  delay(yellowTime);
  if (direction == "NS") {
    digitalWrite(yellowN, LOW);
    digitalWrite(yellowS, LOW);
    digitalWrite(redN, HIGH);
    digitalWrite(redS, HIGH);
  } else {
    digitalWrite(yellowE, LOW);
    digitalWrite(yellowW, LOW);
    digitalWrite(redE, HIGH);
    digitalWrite(redW, HIGH);
  }
}

void allRed() {
  digitalWrite(redN, HIGH);
  digitalWrite(redS, HIGH);
  digitalWrite(redE, HIGH);
  digitalWrite(redW, HIGH);
  delay(redBuffer);
}

void listenForTrigger() {
  unsigned long start = millis();
  while (millis() - start < redBuffer) {
    if (Serial.available()) {
      String message = Serial.readStringUntil('\n');
      message.trim();

      // Expected format: NS=1,EW=0
      if (message.startsWith("NS=")) {
        int nsIndex = message.indexOf("NS=");
        int ewIndex = message.indexOf("EW=");
        if (nsIndex != -1 && ewIndex != -1) {
          int nsVal = message.substring(nsIndex + 3, message.indexOf(',', nsIndex)).toInt();
          int ewVal = message.substring(ewIndex + 3).toInt();
          extendNSGreen = (nsVal == 1);
          extendEWGreen = (ewVal == 1);
        }
      }
    }
  }
}
