import os, sys, time
import numpy as np
import sounddevice as sd
from openwakeword.model import Model

model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'voice', 'wakeword', 'hey_gagan.onnx')
oww = Model(wakeword_models=[model_path], inference_framework="onnx")

print("Scanning all input audio devices...")
devs = sd.query_devices()
candidates = []
for idx, d in enumerate(devs):
    if d.get('max_input_channels', 0) > 0:
        name = d.get('name', '')
        host = sd.query_hostapis(d.get('hostapi', 0)).get('name', '')
        try:
            samples = []
            def cb(indata, frames, time_info, status):
                samples.append(indata.copy())
            with sd.InputStream(device=idx, samplerate=16000, channels=1, dtype='int16', callback=cb):
                time.sleep(0.3)
            audio = np.concatenate(samples).flatten()
            rms = np.sqrt(np.mean((audio.astype(np.float32) / 32767.0)**2))
            
            # Feed to openwakeword
            chunk = audio[:1280] if len(audio) >= 1280 else np.pad(audio, (0, 1280 - len(audio)))
            pred = oww.predict(chunk)
            score = pred.get('hey_gagan', 0.0)
            
            candidates.append((idx, name, host, rms, score))
            print(f"Device [{idx:2d}] ({host:18s}) {name[:40]:40s} | RMS={rms:.6f} | Ambient Score={score:.4f}")
        except Exception as e:
            print(f"Device [{idx:2d}] ({host:18s}) {name[:40]:40s} | FAILED: {e}")

candidates.sort(key=lambda x: x[3], reverse=True)
if candidates:
    print("\nTop working mic device:", candidates[0])

