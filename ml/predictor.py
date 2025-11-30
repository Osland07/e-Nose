import joblib
import os
import numpy as np
import pandas as pd
from ml.feature_extractor import extract_features
from sklearn.preprocessing import LabelEncoder

class Predictor:
    MODEL_DIR = "model"

    def __init__(self):
        self.model = None
        self.scaler = None
        self.le = LabelEncoder()
        self.feature_columns = None
        self.loaded_model_name = None
        # Fit the label encoder with the new generic classes
        self.le.fit(['Terdeteksi Biomarker', 'Tidak Terdeteksi'])

    def load_model(self, model_filename):
        """
        Loads a trained model, its scaler, and feature columns from a .joblib file.
        The file is expected to contain a dictionary with 'model', 'scaler', and 'columns' keys.
        """
        model_path = os.path.join(self.MODEL_DIR, model_filename)
        if not os.path.exists(model_path):
            print(f"Error: Model file not found at {model_path}")
            self.model = None
            self.scaler = None
            self.feature_columns = None
            self.loaded_model_name = None
            return False
        
        try:
            payload = joblib.load(model_path)
            self.model = payload.get('model')
            self.scaler = payload.get('scaler')
            # The training script needs to save the column order
            self.feature_columns = payload.get('columns') 
            self.loaded_model_name = model_filename
            
            missing_keys = []
            if self.model is None: missing_keys.append('model')
            if self.scaler is None: missing_keys.append('scaler')
            if self.feature_columns is None: missing_keys.append('columns')

            if missing_keys:
                print(f"Error: Model file '{model_filename}' is incomplete. Missing keys: {missing_keys}")
                return False

            print(f"Model '{model_filename}' loaded successfully.")
            return True
        except Exception as e:
            print(f"Error loading model '{model_filename}': {e}")
            self.model = None
            self.scaler = None
            self.feature_columns = None
            self.loaded_model_name = None
            return False

    def load_model_from_payload(self, payload):
        """
        Loads a model from a pre-loaded payload dictionary.
        """
        try:
            self.model = payload.get('model')
            self.scaler = payload.get('scaler')
            self.feature_columns = payload.get('columns')
            
            if self.model is None or self.scaler is None or self.feature_columns is None:
                print("Error: Model payload is incomplete.")
                return False
            
            return True
        except Exception as e:
            print(f"Error loading model from payload: {e}")
            self.model = None
            self.scaler = None
            self.feature_columns = None
            return False

    def predict_all_models(self, buffered_data, whitelist=None):
        """
        ENSEMBLE MODE: Memprediksi menggunakan model yang dipilih.
        whitelist: List nama file model yang boleh ikut voting. Jika None/Kosong, pakai semua.
        """
        # 1. Parse Data Sekali Saja
        sensor_names = ['MQ2', 'MQ3', 'MQ4', 'MQ6', 'MQ7', 'MQ8', 'MQ135', 'QCM']
        try:
            parsed_data = []
            for row in buffered_data:
                vals = list(map(float, row.split(',')))
                if len(vals) >= 8: parsed_data.append(vals[:8])
            
            if not parsed_data: return "Error", 0.0, []
            
            df = pd.DataFrame(parsed_data, columns=sensor_names)
            features = extract_features(df)
        except:
            return "Error Data", 0.0, []

        # 2. Loop Model (Filtered)
        all_models = self.get_available_models()
        
        # Filter berdasarkan whitelist jika ada
        if whitelist:
            active_models = [m for m in all_models if m in whitelist]
            if not active_models: active_models = all_models # Fallback jika whitelist salah
        else:
            active_models = all_models

        results = []
        votes = {}
        
        for model_file in active_models:
            # Load model sementara
            full_path = os.path.join(self.MODEL_DIR, model_file)
            try:
                payload = joblib.load(full_path)
                tmp_model = payload.get('model')
                tmp_scaler = payload.get('scaler')
                tmp_cols = payload.get('columns')
                
                # Preprocess
                feat_df = pd.DataFrame([features])
                if tmp_cols: feat_df = feat_df.reindex(columns=tmp_cols, fill_value=0)
                else: feat_df = feat_df.fillna(0)
                
                X_scaled = tmp_scaler.transform(feat_df)
                
                # Predict
                pred_idx = tmp_model.predict(X_scaled)[0]
                proba = np.max(tmp_model.predict_proba(X_scaled)) * 100
                
                # Decode Label
                # Kita asumsikan semua model pakai encoder yang mirip/sama
                # Atau kita coba decode manual jika memungkinkan
                try:
                    label = self.le.inverse_transform([pred_idx])[0]
                except:
                    # Fallback: coba tebak dari atribut classes_ model jika ada
                    if hasattr(tmp_model, 'classes_'):
                        label = tmp_model.classes_[pred_idx]
                    else:
                        label = str(pred_idx)

                # Simpan Hasil
                model_name = model_file.replace(".joblib", "").replace("MODEL_", "").replace("REAL_", "")
                results.append({
                    "name": model_name,
                    "label": label,
                    "conf": proba
                })
                
                # Voting
                votes[label] = votes.get(label, 0) + 1
                
            except Exception as e:
                print(f"Skip model {model_file}: {e}")

        if not results:
            return "No Models", 0.0, []

        # 3. Hitung Pemenang Voting
        winner = max(votes, key=votes.get)
        vote_count = votes[winner]
        total_models = len(results)
        confidence = (vote_count / total_models) * 100
        
        return winner, confidence, results

    def predict(self, buffered_data):
        """
        Takes a buffer of raw data, extracts features, and makes a prediction.
        'buffered_data' is a list of raw, comma-separated sensor strings.
        """
        # --- JALUR KHUSUS SIMULASI (BYPASS) ---
        try:
            first_row = buffered_data[0].strip()
            if ',' not in first_row:
                # Logic Bypass untuk data tunggal '0' atau '1'
                val = float(first_row)
                if val == 1.0: return "Terdeteksi Biomarker", 100.0
                else: return "Tidak Terdeteksi", 100.0
        except:
            pass 
        # --------------------------------------

        if self.model is None or self.scaler is None:
            return "Error: Model not loaded.", 0.0

        try:
            # 1. Convert buffer to DataFrame
            # Kita asumsikan data masuk formatnya: MQ2...QCM, Temp, Hum, Pres (11 kolom)
            # TAPI model cuma butuh 8 kolom pertama (MQ2...QCM)
            
            sensor_names = ['MQ2', 'MQ3', 'MQ4', 'MQ6', 'MQ7', 'MQ8', 'MQ135', 'QCM']
            
            parsed_data = []
            for row in buffered_data:
                vals = list(map(float, row.split(',')))
                # Ambil 8 kolom pertama saja untuk prediksi
                if len(vals) >= 8:
                    parsed_data.append(vals[:8])
                else:
                    # Kalau data korup/kurang, skip atau padding (kita skip aja biar aman)
                    continue
            
            if not parsed_data:
                 return "Error: Data kosong/rusak.", 0.0

            df = pd.DataFrame(parsed_data, columns=sensor_names)

            # 2. Extract features (Statistik dari 8 sensor tadi)
            features = extract_features(df)
            
            # 3. Convert to DataFrame with correct column order for Model
            # Pastikan urutan kolom fitur sama persis dengan saat training
            if self.feature_columns:
                # Buat DF kosong dengan kolom lengkap, lalu isi
                features_df = pd.DataFrame([features])
                # Reindex/urutkan kolom, isi 0 jika ada fitur yang hilang
                features_df = features_df.reindex(columns=self.feature_columns, fill_value=0)
            else:
                features_df = pd.DataFrame([features]).fillna(0)

            # 4. Scale features
            scaled_features = self.scaler.transform(features_df)
            
            # 5. Make prediction
            prediction_idx = self.model.predict(scaled_features)
            probability = self.model.predict_proba(scaled_features)
            
            # 6. Decode label
            # Cek apakah label encoder punya kelas yang cukup
            if hasattr(self.le, 'inverse_transform'):
                try:
                    result_label = self.le.inverse_transform(prediction_idx)[0]
                except:
                    # Fallback jika label tidak dikenal
                    result_label = "Kelas " + str(prediction_idx[0])
            else:
                result_label = str(prediction_idx[0])

            confidence = np.max(probability) * 100
            
            return result_label, confidence
            
        except ValueError as e:
            print(f"Error processing data: {e}")
            return "Error: Invalid data format.", 0.0
        except Exception as e:
            print(f"Error during prediction: {e}")
            import traceback
            traceback.print_exc()
            return f"Error: Prediction failed.", 0.0

    @staticmethod
    def get_available_models():
        """Lists all .joblib files in the MODEL_DIR directory."""
        if not os.path.exists(Predictor.MODEL_DIR):
            os.makedirs(Predictor.MODEL_DIR)
            return []
        
        models = [f for f in os.listdir(Predictor.MODEL_DIR) if f.endswith('.joblib')]
        return models

