#define SensorPin A0    // Analog input connected to pH module output
unsigned long int avgValue;
int buf[10], temp;

void setup() {
  pinMode(13, OUTPUT);
  Serial.begin(9600);
  Serial.println("Ready");
}

void loop() {
  for (int i=0; i<10; i++) {
    buf[i] = analogRead(SensorPin);
    delay(10);
  }
  for (int i=0; i<9; i++) {
    for (int j=i+1; j<10; j++) {
      if (buf[i] > buf[j]) {
        temp = buf[i];
        buf[i] = buf[j];
        buf[j] = temp;
      }
    }
  }
  avgValue = 0;
  for (int i=2; i<8; i++) avgValue += buf[i];

  // Convert to voltage
  float voltage = (float)avgValue * 5.0 / 1024 / 6;

  // Convert voltage to pH (requires calibration!)
  // The numbers 7 and 2.5 below are placeholders and should be adjusted
  // after calibrating with pH 4.0 and pH 7.0 buffer solutions.
  float phValue = -5.50 * voltage + 15.2;
  //float phValue = 7 + ((2.5 - voltage) / 0.18);

  Serial.print("pH: ");
  Serial.println(phValue, 2);

  digitalWrite(13, HIGH);
  delay(800);
  digitalWrite(13, LOW);

  // 9.6 ph measured at 4.0 buffer
  //12.63 measured at 7.0 buffer
}