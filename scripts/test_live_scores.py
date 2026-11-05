import os, sys, time
import numpy as np
import sounddevice as sd
from openwakeword.model import Model

model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'voice', 'wakeword', 'hey_gagan.onnx')
oww = Model(wakeword_models=[model_path], inference_framework="onnx")

print("Recording from Device 20 for 10 seconds. PLEASE SPEAK 'Hey Gagan' NOW!")
samples = []
def cb(indata, frames, time_info, status):
    samples.append(indata.copy())

try:
    with sd.InputStream(device=20, samplerate=16000, channels=1, callback=cb):
        for s in range(10):
            time.sleep(1.0)
            if samples:
                recent = np.concatenate(samples[-10:]).flatten()
                rms = np.sqrt(np.mean(recent**2))
                int16 = (recent * 32767).astype(np.int16)
                if len(int16) >= 1280:
                    pred = oww.predict(int16[-1280:])
                    print(f"Sec {s+1:2d} | RMS: {rms:.6f} | Score: {pred.get('hey_gagan', 0.0):.6f} | Raw: {pred}")
except Exception as e:
    print(f"Error: {e}")
