import joblib
import os
import numpy as np
import pandas as pd
from ml.feature_extractor import extract_features

class Predictor:
    MODEL_DIR = "model"

    def __init__(self):
        self.model = None # Compatibility for UI state checks
        pass # Stateless, load on demand to save memory/avoid conflicts

    def load_model_from_payload(self, payload):
        """Compatibility: Validates payload (UI requirement)"""
        if not payload or 'model' not in payload: return False
        self.model = payload.get('model') # Store for UI checks
        return True

    def load_model(self, model_filename):
        """Compatibility: Loads model to check validity"""
        payload, err = self._load_pipeline(model_filename)
        if err: return False
        return True

    def _load_pipeline(self, model_filename):
        """
        Memuat Model, Scaler, dan Metadata dari file .joblib
        """
        path = os.path.join(self.MODEL_DIR, model_filename)
        if not os.path.exists(path):
            return None, f"File {model_filename} tidak ditemukan."
        
        try:
            payload = joblib.load(path)
            # Validasi Payload
            if not isinstance(payload, dict):
                return None, "Format model usang/corrupt."
            
            return payload, None
        except Exception as e:
            return None, str(e)

    def predict_from_dataframe(self, df, whitelist=None):
        """
        Fungsi Utama Prediksi dari DataFrame (Raw Data Sensor).
        Mengembalikan: (Label Final, Confidence, Details List)
        """
        # 1. PREPROCESSING DATA
        # Normalisasi Header (Hapus spasi, Uppercase)
        df.columns = [str(c).upper().strip().replace(' ', '') for c in df.columns]
        
        # Ekstraksi Fitur Statistik
        # Kita extract SEMUA kemungkinan fitur dulu (default 8 sensor)
        # Nanti model akan memilih fitur yang dia butuhkan saja.
        try:
            features = extract_features(df) # Output: Dictionary
            # Bungkus jadi DataFrame 1 baris
            X_raw = pd.DataFrame([features])
        except Exception as e:
            return "Error Ekstraksi Fitur", 0.0, [{"name": "System", "label": "Error", "conf": 0.0}]

        # 2. SIAPKAN MODEL (Voting System)
        available_models = self._get_model_list(whitelist)
        if not available_models:
            return "Belum Ada Model", 0.0, []

        votes = []
        
        # 3. PREDIKSI SETIAP MODEL
        for model_name in available_models:
            payload, err = self._load_pipeline(model_name)
            if err: continue
            
            model = payload.get('model')
            scaler = payload.get('scaler')
            train_cols = payload.get('columns') # Urutan kolom saat training
            
            # A. Penyelarasan Fitur (CRITICAL STEP)
            # Pastikan X_input punya kolom yang SAMA PERSIS dengan saat training
            if train_cols:
                # Reindex: Buang fitur berlebih, isi 0 untuk fitur yang kurang
                X_ready = X_raw.reindex(columns=train_cols, fill_value=0)
            else:
                # Fallback untuk model lama
                X_ready = X_raw.fillna(0)
                
            # B. Scaling
            try:
                if scaler:
                    X_scaled = scaler.transform(X_ready)
                else:
                    X_scaled = X_ready
            except:
                continue # Skip model jika scaling gagal

            # C. Prediksi
            try:
                # Dapatkan Probability (jika support)
                if hasattr(model, "predict_proba"):
                    probs = model.predict_proba(X_scaled)[0] # [Prob_Kelas0, Prob_Kelas1]
                    classes = model.classes_
                    
                    # Cari kelas dengan probabilitas tertinggi
                    max_idx = np.argmax(probs)
                    pred_label = str(classes[max_idx])
                    confidence = probs[max_idx] * 100
                    
                else:
                    # Fallback jika model tidak support probability (misal SVM linear)
                    pred_idx = model.predict(X_scaled)[0]
                    if hasattr(model, 'classes_'):
                        pred_label = str(model.classes_[pred_idx])
                    else:
                        pred_label = str(pred_idx)
                    confidence = 100.0 # Blind confidence

                # Mapping Legacy (Jaga-jaga model lama yang outputnya 0/1)
                if pred_label == "0": pred_label = "Terdeteksi (Legacy)"
                if pred_label == "1": pred_label = "Tidak Terdeteksi (Legacy)"

                # Simpan Vote
                votes.append({
                    "name": model_name.replace(".joblib", ""),
                    "label": pred_label,
                    "conf": confidence
                })
                
            except Exception as e:
                print(f"Error predict {model_name}: {e}")

        if not votes:
            return "Gagal Prediksi", 0.0, []

        # 4. HITUNG HASIL VOTING (Simple Majority)
        from collections import Counter
        
        # Kumpulkan semua label pemenang
        labels = [v['label'] for v in votes]
        counts = Counter(labels)
        
        # Pemenang terbanyak
        winner_label, winner_count = counts.most_common(1)[0]
        
        # Hitung Confidence Rata-Rata untuk Pemenang
        # (Hanya rata-rata dari model yang memilih pemenang tersebut)
        winner_confs = [v['conf'] for v in votes if v['label'] == winner_label]
        avg_conf = sum(winner_confs) / len(winner_confs)
        
        # Penyesuaian Confidence Global (Penalti jika voting tidak bulat)
        # Jika 3 model pilih A, 2 model pilih B -> Confidence A turun sedikit
        vote_agreement = winner_count / len(votes) # 0.0 - 1.0
        
        final_conf = avg_conf * vote_agreement

        return winner_label, final_conf, votes

    def predict_all_models(self, buffered_data, whitelist=None):
        """Wrapper untuk data buffer (string csv)"""
        # Parse CSV string ke DataFrame
        try:
            parsed_data = []
            for row in buffered_data:
                if not row.strip(): continue
                vals = list(map(float, row.split(',')))
                parsed_data.append(vals)
            
            if not parsed_data: return "Data Kosong", 0.0, []
            
            # Asumsi 8 Sensor Standar jika dari Buffer Device
            cols = ['MQ2', 'MQ3', 'MQ4', 'MQ6', 'MQ7', 'MQ8', 'MQ135', 'QCM']
            # Potong/Pad
            clean_data = []
            for p in parsed_data:
                if len(p) >= 8: clean_data.append(p[:8])
                else: clean_data.append(p + [0]*(8-len(p)))
                
            df = pd.DataFrame(clean_data, columns=cols)
            return self.predict_from_dataframe(df, whitelist)
            
        except Exception as e:
            return f"Error Buffer: {str(e)}", 0.0, []

    def get_available_models(self):
        """Public wrapper to list models"""
        return self._get_model_list(None)

    def _get_model_list(self, whitelist):
        if not os.path.exists(self.MODEL_DIR): return []
        files = [f for f in os.listdir(self.MODEL_DIR) if f.endswith('.joblib')]
        if whitelist:
            return [f for f in files if f in whitelist]
        return files