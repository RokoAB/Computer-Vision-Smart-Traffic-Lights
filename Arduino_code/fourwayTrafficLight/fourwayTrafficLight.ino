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

// Timings (in milliseconds)
const int greenTime = 5000;
const int yellowTime = 2000;
const int redBuffer = 1000;

void setup() {
  // Set all LED pins as OUTPUT
  int pins[] = {redN, yellowN, greenN, redS, yellowS, greenS, redE, yellowE, greenE, redW, yellowW, greenW};
  for (int i = 0; i < 12; i++) {
    pinMode(pins[i], OUTPUT);
  }
}

void loop() {
  // === North-South GREEN, East-West RED ===
  digitalWrite(greenN, HIGH);
  digitalWrite(greenS, HIGH);
  digitalWrite(redE, HIGH);
  digitalWrite(redW, HIGH);

  digitalWrite(redN, LOW);
  digitalWrite(redS, LOW);
  digitalWrite(greenE, LOW);
  digitalWrite(greenW, LOW);
  digitalWrite(yellowE, LOW);
  digitalWrite(yellowW, LOW);
  
  delay(greenTime);

  // === North-South YELLOW ===
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

  // === East-West GREEN, North-South RED ===
  digitalWrite(redN, HIGH);
  digitalWrite(redS, HIGH);
  digitalWrite(greenE, HIGH);
  digitalWrite(greenW, HIGH);
  digitalWrite(redE, LOW);
  digitalWrite(redW, LOW);
  delay(greenTime);

  // === East-West YELLOW ===
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
}
