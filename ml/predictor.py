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
        # Fit the label encoder with the known classes from the training script
        self.le.fit(['Terdeteksi Daging Babi', 'Tidak Terdeteksi'])

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
            
            if self.model is None or self.scaler is None or self.feature_columns is None:
                print("Error: Model file is incomplete. It must contain 'model', 'scaler', and 'columns'.")
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

    def predict(self, buffered_data):
        """
        Takes a buffer of raw data, extracts features, and makes a prediction.
        'buffered_data' is a list of raw, comma-separated sensor strings.
        """
        if self.model is None or self.scaler is None:
            return "Error: Model not loaded.", 0.0

        try:
            # 1. Convert buffer to DataFrame
            sensor_names = ['MQ2', 'MQ3', 'MQ4', 'MQ6', 'MQ7', 'MQ8', 'MQ135', 'QCM']
            data_list = [list(map(float, row.split(','))) for row in buffered_data]
            df = pd.DataFrame(data_list, columns=sensor_names)

            # 2. Extract features
            features = extract_features(df)
            
            # 3. Convert to DataFrame with correct column order
            features_df = pd.DataFrame([features], columns=self.feature_columns).fillna(0)

            # 4. Scale features
            scaled_features = self.scaler.transform(features_df)
            
            # 5. Make prediction
            prediction_idx = self.model.predict(scaled_features)
            probability = self.model.predict_proba(scaled_features)
            
            # 6. Decode label and get confidence
            result_label = self.le.inverse_transform(prediction_idx)[0]
            confidence = np.max(probability) * 100
            
            return result_label, confidence
            
        except ValueError as e:
            print(f"Error processing data: {e}")
            return "Error: Invalid data format.", 0.0
        except Exception as e:
            print(f"Error during prediction: {e}")
            return f"Error: Prediction failed.", 0.0

    @staticmethod
    def get_available_models():
        """Lists all .joblib files in the MODEL_DIR directory."""
        if not os.path.exists(Predictor.MODEL_DIR):
            os.makedirs(Predictor.MODEL_DIR)
            return []
        
        models = [f for f in os.listdir(Predictor.MODEL_DIR) if f.endswith('.joblib')]
        return models

