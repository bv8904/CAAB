import os
import numpy as np
import random
import config
import cv2

try:
    import tensorflow as tf
    from tensorflow.keras.models import load_model, Sequential
    from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
    from tensorflow.keras.applications import MobileNetV2
    import h5py
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    print("Warning: TensorFlow not found. Using simulation mode.")

class AgeClassifier:
    def __init__(self):
        self.model = None
        self.load_model()

    def load_model(self):
        if TF_AVAILABLE and os.path.exists(config.MODEL_PATH):
            try:
                # Try standard loading first
                self.model = load_model(config.MODEL_PATH)
                print("Model loaded successfully.")
            except Exception as e:
                try:
                    # Fallback: Load using h5py and rebuild model architecture
                    print(f"Standard load failed, attempting h5py rebuild: {str(e)[:80]}")
                    with h5py.File(config.MODEL_PATH, 'r') as f:
                        # Extract model config from the h5 file
                        if 'model_config' in f.attrs:
                            import json
                            model_config = json.loads(f.attrs['model_config'])
                            # Remove quantization_config from all layers
                            def clean_config(config_dict):
                                if isinstance(config_dict, dict):
                                    config_dict.pop('quantization_config', None)
                                    for v in config_dict.values():
                                        clean_config(v)
                                elif isinstance(config_dict, list):
                                    for item in config_dict:
                                        clean_config(item)
                            
                            clean_config(model_config)
                            # Rebuild model from cleaned config
                            from tensorflow.keras.models import model_from_json
                            self.model = model_from_json(json.dumps(model_config))
                            # Load weights
                            self.model.load_weights(config.MODEL_PATH)
                            print("Model loaded successfully via h5py rebuild.")
                        else:
                            raise Exception("No model_config found in h5 file")
                except Exception as e2:
                    print(f"H5py rebuild failed: {e2}")
                    print("Model will run in Mock Mode (returns default predictions)")
                    self.model = None
        else:
            print("Model not found or TF unavailable. Running in Mock Mode.")

    def predict(self, frame):
        """
        Returns:
            0: Child
            1: Adult
        """
        if self.model is None:
            # Mocking: Return Adult by default for testing if no model
            return 1
        
        try:
            # Preprocessing
            img = cv2.resize(frame, config.FRAME_SIZE)
            img = img / 255.0
            img = np.expand_dims(img, axis=0)
            
            prediction = self.model.predict(img)
            # Assuming output is a sigmoid probability where < 0.5 is Child, > 0.5 is Adult
            # Usage depends on how the model was trained. 
            # Let's assume class 0 = Child, class 1 = Adult based on request.
            class_idx = 1 if prediction[0][0] > 0.5 else 0
            return class_idx
        except Exception as e:
            print(f"Prediction Error: {e}")
            return 0 # Fail-safe: Assume Child
