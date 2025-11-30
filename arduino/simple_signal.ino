// ==========================================
// E-NOSE SIMPLE SIGNAL (HASIL LANGSUNG)
// ==========================================
// Arduino hanya mengirim sinyal hasil akhir.
// Python akan menerjemahkannya langsung tanpa ML.
// Kirim '1' -> Python baca: "Terdeteksi Biomarker"
// Kirim '0' -> Python baca: "Tidak Terdeteksi"

bool resultIsPositive = true; // UBAH INI: true = Positif, false = Negatif

void setup() {
  Serial.begin(9600);
}

void loop() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    if (cmd == '1') resultIsPositive = true;
    if (cmd == '0') resultIsPositive = false;
  }

  if (resultIsPositive) {
    Serial.println("1"); 
  } else {
    Serial.println("0");
  }
  
  delay(1000);
}
