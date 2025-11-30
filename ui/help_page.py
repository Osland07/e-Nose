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
        <h1 style="color: #1E3A8A;">📘 Panduan Pengguna E-Nose AI</h1>
        <hr>
        
        <h3>1. Cara Menggunakan Sistem</h3>
        <ol>
            <li><b>Persiapan:</b> Pastikan Arduino terhubung ke USB. Jika tidak ada alat, aktifkan <i>Mode Simulasi</i> di Dashboard.</li>
            <li><b>Pilih Model:</b> Masuk ke Dashboard, klik tombol <b>"⚙️ Atur Voting"</b> untuk memilih model AI mana saja yang akan digunakan sebagai juri.</li>
            <li><b>Mulai Deteksi:</b> Klik tombol biru <b>"Mulai Deteksi"</b>. Tunggu proses pengambilan data (default 15 detik).</li>
            <li><b>Lihat Hasil:</b> 
                <ul>
                    <li>Hasil utama muncul di kotak besar.</li>
                    <li>Klik <b>"🔍 Lihat Detail Voting"</b> untuk melihat skor dari masing-masing model.</li>
                </ul>
            </li>
        </ol>

        <h3>2. Training Model Baru (Menu Training Center)</h3>
        <p>Gunakan fitur ini jika Anda memiliki data sampel baru (Sapi/Babi) dalam format CSV.</p>
        <ul>
            <li>Siapkan folder <code>sample_data</code> yang berisi sub-folder sesuai label (misal: folder <code>Sapi</code> dan folder <code>Babi</code>).</li>
            <li>Centang model yang ingin dilatih.</li>
            <li>Klik <b>Mulai Training</b>.</li>
        </ul>

        <hr>
        <h3 style="color: #B91C1C;">⚠ Catatan Khusus Performa Model</h3>
        
        <table border="1" cellspacing="0" cellpadding="10" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #F1F5F9;">
                <th>Jenis Model</th>
                <th>Karakteristik</th>
                <th>Kebutuhan Hardware</th>
            </tr>
            <tr>
                <td><b>SVM & KNN</b></td>
                <td>Sangat Cepat, Ringan, Stabil.</td>
                <td><span style="color:green;">Ringan</span> (Semua Laptop Bisa)</td>
            </tr>
            <tr>
                <td><b>Random Forest</b></td>
                <td>Akurasi Tinggi, Anti-Noise.</td>
                <td><span style="color:orange;">Sedang</span> (RAM min 4GB)</td>
            </tr>
            <tr>
                <td><b>XGBoost</b></td>
                <td>Sangat Detail, Juara Kompetisi.</td>
                <td><span style="color:orange;">Sedang</span></td>
            </tr>
            <tr>
                <td><b>Deep Neural Net (DNN/MLP)</b></td>
                <td><b>SANGAT BERAT</b>. Meniru otak manusia. Butuh waktu training lama.</td>
                <td><span style="color:red;">Berat</span> (CPU i5/i7 Gen Baru, RAM min 8GB, SSD Wajib)</td>
            </tr>
        </table>

        <br>
        <h3>3. Spesifikasi Minimum Sistem</h3>
        <ul>
            <li><b>OS:</b> Windows 10/11 (64-bit)</li>
            <li><b>Processor:</b> Intel Core i3 (Gen 8+) atau setara.</li>
            <li><b>RAM:</b> 4 GB (Disarankan 8 GB jika menggunakan Neural Network).</li>
            <li><b>Storage:</b> SSD (Agar proses load model cepat).</li>
        </ul>
        
        <p><i>© 2025 E-Nose Research Team</i></p>
        """
        
        self.browser.setHtml(html_content)
        layout.addWidget(self.browser)
