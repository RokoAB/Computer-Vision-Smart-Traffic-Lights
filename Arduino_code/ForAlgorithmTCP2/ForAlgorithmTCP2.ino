String PorukaZaKontroler = "";
bool startReceived = false;

// === Pin Assignments ===
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

// === Timing ===
unsigned long defaultGreenDuration = 5000;   // 5 seconds
unsigned long extendedGreenDuration = 10000; // 10 seconds
unsigned long yellowDuration = 2000;         // 2 seconds

void setup() {
  Serial.begin(9600);

  // Set all light pins as OUTPUT
  int pins[] = {redN, yellowN, greenN, redS, yellowS, greenS, redE, yellowE, greenE, redW, yellowW, greenW};
  for (int i = 0; i < 12; i++) {
    pinMode(pins[i], OUTPUT);
  }

  allLightsOff();
  Serial.println("Arduino ready.");
}

void loop() {
  if (Serial.available()) {
    char ch = Serial.read();
    if (ch == '\n') {
      poruka(PorukaZaKontroler);
      PorukaZaKontroler = "";
    } else {
      PorukaZaKontroler += ch;
    }
  }
}

void poruka(String mod) {
  mod.trim();

  if (mod == "START") {
    Serial.println("START received.");
    startReceived = true;
    semafor("DEFAULT");
  } 
  else if (startReceived && (mod == "NSEXTEND" || mod == "EWEXTEND" || mod == "DEFAULT")) {
    Serial.println("naredba received: " + mod);
    semafor(mod);
  }
}

void semafor(String naredba) {
  unsigned long nsGreenTime = defaultGreenDuration;
  unsigned long ewGreenTime = defaultGreenDuration;

  if (naredba == "NSEXTEND") {
    nsGreenTime = extendedGreenDuration;
  } else if (naredba == "EWEXTEND") {
    ewGreenTime = extendedGreenDuration;
  }

  // === NS GREEN phase (North & South green, East & West red)
  setNSLights(HIGH, LOW, LOW);
  setEWLights(LOW, LOW, HIGH);
  delay(nsGreenTime);

  // === NS YELLOW
  setNSLights(LOW, HIGH, LOW);
  delay(yellowDuration);

  // === NS RED
  setNSLights(LOW, LOW, HIGH);

  // === EW GREEN phase (East & West green, North & South red)
  setEWLights(HIGH, LOW, LOW);
  delay(ewGreenTime);

  // === EW YELLOW
  setEWLights(LOW, HIGH, LOW);
  delay(yellowDuration);

  // === EW RED
  setEWLights(LOW, LOW, HIGH);
}

void setNSLights(bool green, bool yellow, bool red) {
  digitalWrite(greenN, green);
  digitalWrite(yellowN, yellow);
  digitalWrite(redN, red);

  digitalWrite(greenS, green);
  digitalWrite(yellowS, yellow);
  digitalWrite(redS, red);
}

void setEWLights(bool green, bool yellow, bool red) {
  digitalWrite(greenE, green);
  digitalWrite(yellowE, yellow);
  digitalWrite(redE, red);

  digitalWrite(greenW, green);
  digitalWrite(yellowW, yellow);
  digitalWrite(redW, red);
}

void allLightsOff() {
  int pins[] = {redN, yellowN, greenN, redS, yellowS, greenS, redE, yellowE, greenE, redW, yellowW, greenW};
  for (int i = 0; i < 12; i++) {
    digitalWrite(pins[i], LOW);
  }
}
