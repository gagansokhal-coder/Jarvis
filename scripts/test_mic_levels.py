import sounddevice as sd
import numpy as np
import time

for target in [1, 20]:
    try:
        samples = []
        def cb(indata, frames, time_info, status):
            samples.append(np.sqrt(np.mean(indata**2)))
        with sd.InputStream(device=target, samplerate=16000, channels=1, callback=cb):
            time.sleep(1.0)
        print(f"Device {target}: Max RMS = {max(samples):.6f}, Avg = {np.mean(samples):.6f}")
    except Exception as e:
        print(f"Device {target} error: {e}")
