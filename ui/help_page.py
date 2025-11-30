from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl

class HelpPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True) # Bisa buka link
        self.browser.setStyleSheet("""
            QTextBrowser {
                background-color: white;
                padding: 20px;
                border: 1px solid #CBD5E1;
                border-radius: 10px;
                font-size: 14px;
                color: #334155;
            }
        """)
        
        # Konten HTML untuk Panduan
        html_content = """
        <h1 style="color: #1E3A8A;">📘 Panduan & Spesifikasi Teknis E-Nose</h1>
        <hr>
        
        <h3>1. Arsitektur Sistem</h3>
        <p>Sistem ini dirancang untuk mendeteksi biomarker volatil pada daging (Sapi/Babi) menggunakan array sensor gas dan algoritma Machine Learning.</p>
        <pre style="background-color: #F1F5F9; padding: 10px;">
 [SENSOR ARRAY]  --->  [ARDUINO]  --->  [PYTHON APP]
 (MQ2..MQ135)         (Serial)          (Feature Extraction)
                                              ⬇
                                        [AI MODELS]
                                     (SVM, RF, Neural Net)
                                              ⬇
                                       [HASIL DETEKSI]
        </pre>

        <h3>2. Spesifikasi Sensor (Hidung Elektronik)</h3>
        <table border="1" cellspacing="0" cellpadding="5" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #E2E8F0;"><th>Sensor</th><th>Target Gas Utama</th><th>Relevansi Biomarker</th></tr>
            <tr><td><b>MQ-2</b></td><td>Asap, LPG, Propana</td><td>Deteksi senyawa hidrokarbon umum.</td></tr>
            <tr><td><b>MQ-3</b></td><td>Alkohol, Etanol</td><td>Deteksi hasil fermentasi/pembusukan awal.</td></tr>
            <tr><td><b>MQ-4</b></td><td>Metana (CH4)</td><td>Gas rawa, indikator pembusukan lanjut.</td></tr>
            <tr><td><b>MQ-6</b></td><td>LPG, Butana</td><td>Referensi silang hidrokarbon.</td></tr>
            <tr><td><b>MQ-7</b></td><td>Karbon Monoksida (CO)</td><td>Indikator pembakaran tak sempurna.</td></tr>
            <tr><td><b>MQ-8</b></td><td>Hidrogen (H2)</td><td>Gas ringan hasil reaksi kimia daging.</td></tr>
            <tr><td><b>MQ-135</b></td><td>Amonia, Sulfida, Benzene</td><td><b>SANGAT PENTING:</b> Deteksi bau busuk/menyengat.</td></tr>
            <tr><td><b>QCM</b></td><td>Massa Partikel (Hz)</td><td>Deteksi molekul organik berat yang menempel.</td></tr>
        </table>

        <h3>3. Panduan Penggunaan (SOP)</h3>
        <ol>
            <li><b>Warming Up:</b> Nyalakan alat selama 5-10 menit agar heater sensor stabil (Nilai tidak drifting).</li>
            <li><b>Sampling (Durasi Optimal):</b> 
                <ul>
                    <li><b>Deteksi Cepat:</b> 15 detik (Sudah cukup untuk Random Forest/KNN).</li>
                    <li><b>Deteksi Akurat:</b> 30-60 detik (Disarankan untuk SVM dan Neural Network agar pola terlihat jelas).</li>
                </ul>
            </li>
            <li><b>Purging:</b> Jauhkan sensor ke udara bersih selama 30 detik sebelum tes berikutnya.</li>
        </ol>

        <h3>4. Troubleshooting Model AI</h3>
        <ul>
            <li><b>Hasil 50-60% (Ragu-ragu)?</b>: Kemungkinan data sampel mirip dengan data bersih. Coba latih ulang model dengan data baru.</li>
            <li><b>Grafik Flat/Diam?</b>: Periksa koneksi kabel USB Arduino.</li>
        </ul>
        
        <p><i>© 2025 E-Nose Research Team - Versi 3.0 Ultimate</i></p>
        """
        
        self.browser.setHtml(html_content)
        layout.addWidget(self.browser)
