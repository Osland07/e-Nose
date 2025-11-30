// ==========================================
// E-NOSE DUMMY SIMULATOR (MODE BODONG)
// ==========================================
// Cara pakai:
// 1. Upload ke Arduino.
// 2. Buka Serial Monitor (Baud 9600).
// 3. Ketik '1' lalu Enter -> Arduino akan kirim data palsu "TERDETEKSI BIOMARKER" (Nilai 100)
// 4. Ketik '0' lalu Enter -> Arduino akan kirim data palsu "TIDAK TERDETEKSI" (Nilai 0)
// 5. Ketik '2' lalu Enter -> Arduino akan kirim data "NGACAR" (Campur/Random)
// ==========================================

int mode = 0; // 0 = Bersih, 1 = Terdeteksi, 2 = Random

void setup() {
  Serial.begin(9600);
}

void loop() {
  // Cek apakah ada perintah dari user lewat Serial Monitor
  if (Serial.available() > 0) {
    char command = Serial.read();
    if (command == '1') {
      mode = 1;
      Serial.println("--- MODE: SIMULASI TERDETEKSI (High Values) ---");
    } else if (command == '0') {
      mode = 0;
      Serial.println("--- MODE: SIMULASI BERSIH (Low Values) ---");
    } else if (command == '2') {
      mode = 2;
      Serial.println("--- MODE: SIMULASI RANDOM ---");
    }
  }

  // Format Data 11 Kolom:
  // MQ2, MQ3, MQ4, MQ6, MQ7, MQ8, MQ135, QCM, Temp, Hum, Pres
  
  if (mode == 1) {
    // KASUS: TERDETEKSI BIOMARKER (Semua sensor Gas & QCM tinggi)
    // Kita pakai angka 100 supaya jauh dari 0 (mudah dibedakan oleh model dummy)
    Serial.println("100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,36.5,80.0,1000.0");
  
  } else if (mode == 0) {
    // KASUS: UDARA BERSIH / TIDAK TERDETEKSI (Semua sensor 0 atau rendah)
    Serial.println("0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,28.5,60.0,1000.0");
  
  } else {
    // KASUS: RANDOM (Untuk tes grafik bergerak-gerak)
    String data = "";
    for(int i=0; i<8; i++) {
      data += String(random(0, 100)); // Sensor Gas Random 0-100
      data += ",";
    }
    data += "30.0,70.0,1005.0"; // Temp, Hum, Pres statis aja
    Serial.println(data);
  }

  delay(1000); // Kirim data setiap 1 detik
}
