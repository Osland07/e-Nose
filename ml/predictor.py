import joblib
import os
import numpy as np

MODEL_DIR = "model"

class Predictor:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.loaded_model_name = None

    def load_model(self, model_filename):
        """
        Loads a trained SVM model and its associated scaler from a .joblib file.
        The file is expected to contain a dictionary with 'model' and 'scaler' keys.
        """
        model_path = os.path.join(MODEL_DIR, model_filename)
        if not os.path.exists(model_path):
            print(f"Error: Model file not found at {model_path}")
            self.model = None
            self.scaler = None
            self.loaded_model_name = None
            return False
        
        try:
            payload = joblib.load(model_path)
            self.model = payload.get('model')
            self.scaler = payload.get('scaler')
            self.loaded_model_name = model_filename
            print(f"Model '{model_filename}' loaded successfully.")
            return True
        except Exception as e:
            print(f"Error loading model '{model_filename}': {e}")
            self.model = None
            self.scaler = None
            self.loaded_model_name = None
            return False

    def predict(self, raw_data_string):
        """
        Takes a raw data string from Arduino, processes it, and makes a prediction.
        Assumes raw_data_string is comma-separated values, e.g., "100,200,300".
        """
        if self.model is None or self.scaler is None:
            return "Error: Model not loaded."

        try:
            # 1. Parse raw data string
            features = np.array([float(x.strip()) for x in raw_data_string.split(',')]).reshape(1, -1)
            
            # 2. Scale features
            scaled_features = self.scaler.transform(features)
            
            # 3. Make prediction
            prediction = self.model.predict(scaled_features)
            
            # Assuming the model predicts 0 for Non-Halal and 1 for Halal
            # This might need adjustment based on the actual model output
            result = "Halal" if prediction[0] == 1 else "Non-Halal"
            return result
        except ValueError:
            return "Error: Invalid data format from Arduino."
        except Exception as e:
            return f"Error during prediction: {e}"

def get_available_models():
    """Lists all .joblib files in the MODEL_DIR directory."""
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
        return []
    
    models = [f for f in os.listdir(MODEL_DIR) if f.endswith('.joblib')]
    return models

