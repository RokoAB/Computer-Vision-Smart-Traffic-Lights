// === Pin Definitions ===
const int redN = 22, yellowN = 24, greenN = 26;
const int redS = 28, yellowS = 30, greenS = 32;
const int redE = 34, yellowE = 36, greenE = 38;
const int redW = 40, yellowW = 42, greenW = 44;

// === Timing Parameters (in ms) ===
const unsigned long greenTimeDefault = 10000;
const unsigned long greenExtension = 5000;
const unsigned long yellowTime = 3000;
const unsigned long redBuffer = 3000;

bool extendNSGreen = false;
bool extendEWGreen = false;

void setup() {
  int pins[] = {redN, yellowN, greenN, redS, yellowS, greenS, redE, yellowE, greenE, redW, yellowW, greenW};
  for (int i = 0; i < 12; i++) pinMode(pins[i], OUTPUT);
  Serial.begin(9600);
}

void loop() {
  // === NORTH-SOUTH GREEN PHASE ===
  sendPhase("GREEN_NS");
  runGreen("NS", extendNSGreen);
  extendNSGreen = false;

  // === YELLOW ===
  setYellow("NS");

  // === ALL RED & TRIGGER CHECK ===
  allRed();
  sendPhase("RED_NS");
  requestAndReadTriggers();

  // === EAST-WEST GREEN PHASE ===
  sendPhase("GREEN_EW");
  runGreen("EW", extendEWGreen);
  extendEWGreen = false;

  // === YELLOW ===
  setYellow("EW");

  // === ALL RED & TRIGGER CHECK ===
  allRed();
  sendPhase("RED_EW");
  requestAndReadTriggers();
}

// === UTILITY FUNCTIONS ===

void runGreen(String dir, bool extend) {
  if (dir == "NS") {
    digitalWrite(redE, HIGH); digitalWrite(redW, HIGH);
    digitalWrite(greenN, HIGH); digitalWrite(greenS, HIGH);
    digitalWrite(redN, LOW); digitalWrite(redS, LOW);
  } else {
    digitalWrite(redN, HIGH); digitalWrite(redS, HIGH);
    digitalWrite(greenE, HIGH); digitalWrite(greenW, HIGH);
    digitalWrite(redE, LOW); digitalWrite(redW, LOW);
  }

  unsigned long duration = greenTimeDefault + (extend ? greenExtension : 0);
  delay(duration);

  // Turn off green lights
  if (dir == "NS") {
    digitalWrite(greenN, LOW); digitalWrite(greenS, LOW);
  } else {
    digitalWrite(greenE, LOW); digitalWrite(greenW, LOW);
  }
}

void setYellow(String dir) {
  if (dir == "NS") {
    digitalWrite(yellowN, HIGH); digitalWrite(yellowS, HIGH);
    delay(yellowTime);
    digitalWrite(yellowN, LOW); digitalWrite(yellowS, LOW);
    digitalWrite(redN, HIGH); digitalWrite(redS, HIGH);
  } else {
    digitalWrite(yellowE, HIGH); digitalWrite(yellowW, HIGH);
    delay(yellowTime);
    digitalWrite(yellowE, LOW); digitalWrite(yellowW, LOW);
    digitalWrite(redE, HIGH); digitalWrite(redW, HIGH);
  }
}

void allRed() {
  digitalWrite(redN, HIGH); digitalWrite(redS, HIGH);
  digitalWrite(redE, HIGH); digitalWrite(redW, HIGH);
  delay(redBuffer);
}

void sendPhase(String phaseName) {
  Serial.print("PHASE:");
  Serial.println(phaseName);
}

void requestAndReadTriggers() {
  Serial.println("SEND_TRIGGER");  // 🔁 Tell Pi to send triggers

  unsigned long start = millis();
  while (millis() - start < redBuffer) {
    if (Serial.available()) {
      String msg = Serial.readStringUntil('\n');
      msg.trim();

      // Format: NS=1,EW=0
      if (msg.startsWith("NS=")) {
        int nsIndex = msg.indexOf("NS=");
        int ewIndex = msg.indexOf("EW=");
        if (nsIndex != -1 && ewIndex != -1) {
          int nsVal = msg.substring(nsIndex + 3, msg.indexOf(',', nsIndex)).toInt();
          int ewVal = msg.substring(ewIndex + 3).toInt();
          extendNSGreen = (nsVal == 1);
          extendEWGreen = (ewVal == 1);
          Serial.print("✅ Triggers received: NS=");
          Serial.print(extendNSGreen);
          Serial.print(" EW=");
          Serial.println(extendEWGreen);
        }
      }
    }
  }
}
