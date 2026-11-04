import os
import sys
import queue
import time
import numpy as np
import sounddevice as sd

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_path = os.path.join(BASE_DIR, 'voice', 'wakeword', 'hey_gagan.onnx')

print("=" * 60)
print("     GAGAN AI - LIVE WAKE WORD MICROPHONE TEST")
print("=" * 60)

try:
    from openwakeword.model import Model
    oww_model = Model(wakeword_models=[model_path], inference_framework="onnx")
    print("✅ Model loaded successfully!")
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    sys.exit(1)

audio_queue = queue.Queue()

def audio_callback(indata, frames, time_info, status):
    if status:
        pass
    audio_queue.put(indata.copy())

SAMPLE_RATE = 16000
CHUNK_SIZE = 1280 # 80ms at 16kHz
THRESHOLD = 0.40

print("\n🎤 Opening microphone stream (Sample Rate: 16000Hz)...")
print(f"👂 Say 'Hey Gagan' or 'Hey Gagan Rajput' (Confidence Threshold: {THRESHOLD})")
print("Press Ctrl+C to stop.\n")

buffer = np.array([], dtype=np.int16)
start_time = time.time()

with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, callback=audio_callback):
    try:
        while True:
            try:
                data = audio_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            int16_chunk = (data.flatten() * 32767).astype(np.int16)
            buffer = np.concatenate((buffer, int16_chunk))

            while len(buffer) >= CHUNK_SIZE:
                frame = buffer[:CHUNK_SIZE]
                buffer = buffer[CHUNK_SIZE:]

                pred = oww_model.predict(frame)
                score = pred.get('hey_gagan', 0.0)

                if score > 0.15:
                    print(f"  [Score: {score:.3f}] ... listening")

                if score >= THRESHOLD:
                    print(f"\n🎉 WAKE WORD TRIGGERED! Score: {score:.3f} | Phrase: 'Hey Gagan'")
                    oww_model.reset()
                    buffer = np.array([], dtype=np.int16)
                    while not audio_queue.empty():
                        audio_queue.get_nowait()
                    time.sleep(1.0)
                    print("\n👂 Ready for next trigger...")

    except KeyboardInterrupt:
        print("\nTest stopped.")
