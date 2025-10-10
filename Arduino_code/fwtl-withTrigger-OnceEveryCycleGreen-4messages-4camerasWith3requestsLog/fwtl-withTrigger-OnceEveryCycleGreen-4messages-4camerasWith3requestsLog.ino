// === Pin Definitions ===
// North
const int crvenoN = 22;
const int zutoN = 24;
const int zelenoN = 26;
// South
const int crvenoS = 28;
const int zutoS = 30;
const int zelenoS = 32;
// East
const int crvenoE = 34;
const int zutoE = 36;
const int zelenoE = 38;
// West
const int crvenoW = 40;
const int zutoW = 42;
const int zelenoW = 44;

// === Timing Parameters ===
const unsigned long zelenoTimeDefault = 5000;
const unsigned long zelenoExtension = 5000;
const unsigned long zutoTime = 1000;
const unsigned long crvenoBuffer = 1000;

// === Globals ===
bool extendNSzeleno = false;
bool extendEWzeleno = false;
bool extensionUsedThisCycle = false;

// Request pattern tracking
String lastPattern = "";
int repeatCount = 0;

void setup() {
  int pins[] = {
    crvenoN, zutoN, zelenoN,
    crvenoS, zutoS, zelenoS,
    crvenoE, zutoE, zelenoE,
    crvenoW, zutoW, zelenoW
  };
  for (int i = 0; i < 12; i++) {
    pinMode(pins[i], OUTPUT);
  }
  Serial.begin(9600);
}

void loop() {
  extensionUsedThisCycle = false;

  // === NORTH-SOUTH zeleno ===
  digitalWrite(crvenoE, HIGH); digitalWrite(crvenoW, HIGH);
  digitalWrite(zelenoN, HIGH); digitalWrite(zelenoS, HIGH);
  digitalWrite(crvenoN, LOW); digitalWrite(crvenoS, LOW);

  unsigned long zelenoTime = zelenoTimeDefault;
  if (extendNSzeleno) {
    zelenoTime += zelenoExtension;
    extendNSzeleno = false;
  }

  delay(zelenoTime);

  // === NORTH-SOUTH zuto ===
  digitalWrite(zelenoN, LOW); digitalWrite(zelenoS, LOW);
  digitalWrite(zutoN, HIGH); digitalWrite(zutoS, HIGH);
  delay(zutoTime);
  
  digitalWrite(zutoN, LOW); digitalWrite(zutoS, LOW);
  digitalWrite(crvenoN, HIGH); digitalWrite(crvenoS, HIGH);
  delay(crvenoBuffer);

  // === Decide next extension ===
  decideExtensionFromInput();

  // === EAST-WEST zeleno ===
  digitalWrite(crvenoN, HIGH); digitalWrite(crvenoS, HIGH);
  digitalWrite(zelenoE, HIGH); digitalWrite(zelenoW, HIGH);
  digitalWrite(crvenoE, LOW); digitalWrite(crvenoW, LOW);

  zelenoTime = zelenoTimeDefault;
  if (extendEWzeleno) {
    zelenoTime += zelenoExtension;
    extendEWzeleno = false;
  }

  delay(zelenoTime);

  // === EAST-WEST zuto ===
  digitalWrite(zelenoE, LOW); digitalWrite(zelenoW, LOW);
  digitalWrite(zutoE, HIGH); digitalWrite(zutoW, HIGH);
  delay(zutoTime);
  digitalWrite(zutoE, LOW); digitalWrite(zutoW, LOW);
  digitalWrite(crvenoE, HIGH); digitalWrite(crvenoW, HIGH);
  delay(crvenoBuffer);
}

// === Decide extension based on camera input ===
void decideExtensionFromInput() {
  int N = 0, S = 0, E = 0, W = 0;
  unsigned long start = millis();

  while (millis() - start < crvenoBuffer) {
    if (Serial.available()) {
      String input = Serial.readStringUntil('\n');
      input.trim();

      N = getValue(input, "N");
      S = getValue(input, "S");
      E = getValue(input, "E");
      W = getValue(input, "W");
    }
  }

  int sum = N + S + E + W;
  String currentPattern = String(N) + S + E + W;

  // === Repeated pattern tracking ===
  if (currentPattern == lastPattern) {
    repeatCount++;
  } else {
    repeatCount = 1;
    lastPattern = currentPattern;
  }

  // === Default: no extension ===
  extendNSzeleno = false;
  extendEWzeleno = false;

  if (extensionUsedThisCycle) return;

  // === Invalid (conflicting) combinations, e.g., N+E or S+W etc. ===
  if ((N && E) || (N && W) || (S && E) || (S && W)) {
    return; // Do not extend for conflicting directions
  }

  // === Two on same road ===
  if (N == 1 && S == 1 && E == 0 && W == 0) {
    extendNSzeleno = true;
  } else if (E == 1 && W == 1 && N == 0 && S == 0) {
    extendEWzeleno = true;
  }

  // === Single camera ===
  else if (N == 1 || S == 1) {
    extendNSzeleno = true;
  } else if (E == 1 || W == 1) {
    extendEWzeleno = true;
  }

  // === 3 sides active ===
  if (sum == 3) {
    if (repeatCount % 2 == 1) {
      // First or third repeat gets extension
      if (N + S > E + W) {
        extendNSzeleno = true;
      } else {
        extendEWzeleno = true;
      }
    }
  }

  if (extendNSzeleno || extendEWzeleno) {
    extensionUsedThisCycle = true;
  }
}

// === Utility: Extract direction value from string ===
int getValue(String input, String key) {
  int idx = input.indexOf(key + "=");
  if (idx == -1) return 0;
  int valStart = idx + key.length() + 1;
  int valEnd = input.indexOf(',', valStart);
  if (valEnd == -1) valEnd = input.length();
  return input.substring(valStart, valEnd).toInt();
}
