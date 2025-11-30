// ==================================================
// E-NOSE REALISTIC SENSOR SIMULATOR (SVM READY)
// ==================================================
// Meniru karakteristik sensor MOS (MQ Series) & QCM
// Output: 11 Kolom Data CSV
// Kontrol via Serial Monitor: ketik '0' (Bersih) atau '1' (Babi)

int currentMode = 0; // 0 = Udara Bersih, 1 = Daging Babi

void setup() {
  Serial.begin(9600);
  randomSeed(analogRead(0));
}

void loop() {
  // Cek Input Serial untuk ganti mode
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    if (cmd == '0') currentMode = 0;
    if (cmd == '1') currentMode = 1;
  }

  String dataLine = "";

  // --- SENSOR 1-8 (MQ Series & QCM) ---
  // MQ2, MQ3, MQ4, MQ6, MQ7, MQ8, MQ135, QCM
  
  if (currentMode == 0) {
    // KASUS: UDARA BERSIH (Baseline)
    // Nilai rendah (10-50) + Noise kecil
    for (int i = 0; i < 8; i++) {
      float baseValue = 30.0 + (i * 2); // Sedikit variasi tiap sensor
      float noise = random(-200, 200) / 100.0; // Noise +/- 2.00
      dataLine += String(baseValue + noise);
      dataLine += ",";
    }
  } 
  else {
    // KASUS: TERDETEKSI DAGING (Respon Tinggi)
    // Karakteristik: MQ135 (Amonia/Sulfid) & MQ3 (Alkohol) biasanya naik drastis di daging
    
    // MQ2 (Asap/LPG) - Naik dikit
    dataLine += String(150.0 + random(-5, 5)) + ",";
    
    // MQ3 (Alkohol) - Naik Sedang
    dataLine += String(300.0 + random(-10, 10)) + ",";
    
    // MQ4 (Methane) - Naik dikit
    dataLine += String(120.0 + random(-5, 5)) + ",";
    
    // MQ6 (LPG) - Rendah
    dataLine += String(80.0 + random(-5, 5)) + ",";
    
    // MQ7 (CO) - Rendah
    dataLine += String(90.0 + random(-5, 5)) + ",";
    
    // MQ8 (Hydrogen) - Sedang
    dataLine += String(180.0 + random(-5, 5)) + ",";
    
    // MQ135 (Air Quality/Bau Busuk) - NAIK DRASTIS (Indikator utama)
    dataLine += String(550.0 + random(-15, 15)) + ",";
    
    // QCM (Massa) - Respon Signifikan
    dataLine += String(600.0 + random(-20, 20)) + ",";
  }

  // --- SENSOR LINGKUNGAN (Temp, Hum, Pres) ---
  // Statis dengan noise sangat kecil
  dataLine += String(28.5 + (random(-10, 10)/100.0)) + ","; // Temp
  dataLine += String(65.0 + (random(-100, 100)/100.0)) + ","; // Hum
  dataLine += String(1005.0 + (random(-10, 10)/100.0)); // Pres

  Serial.println(dataLine);
  delay(500); // Kirim data 2x per detik (lebih real-time)
}
