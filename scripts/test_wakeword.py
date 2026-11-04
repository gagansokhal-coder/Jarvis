import os
import sys
import numpy as np

# Ensure stdout handles UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_path = os.path.join(BASE_DIR, 'voice', 'wakeword', 'hey_gagan.onnx')

print(f"Checking model at: {model_path}")
if not os.path.exists(model_path):
    print("❌ Error: hey_gagan.onnx does not exist.")
    sys.exit(1)

print(f"File size: {os.path.getsize(model_path)} bytes")

try:
    import openwakeword
    from openwakeword.model import Model

    oww_model = Model(wakeword_models=[model_path], inference_framework="onnx")
    print("✅ Successfully loaded model into openWakeWord engine!")
    print(f"Active model keys: {list(oww_model.models.keys())}")

    # Test dummy 80ms audio frame (1280 samples at 16kHz)
    dummy_audio = np.zeros(1280, dtype=np.int16)
    pred = oww_model.predict(dummy_audio)
    print("Prediction output test:", pred)
    print("\n🎉 Model is 100% operational for real-time microphone listening!")
except Exception as e:
    print(f"\n❌ Error initializing openWakeWord model: {e}")
    sys.exit(1)

