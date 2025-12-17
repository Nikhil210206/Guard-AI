import sounddevice as sd
import numpy as np
import time

def print_sound_level(indata, frames, time, status):
    if status:
        print(f"Status: {status}")
    volume_norm = np.linalg.norm(indata) * 10
    bar = "|" * int(volume_norm * 50)
    print(f"\rVolume: {volume_norm:.4f} {bar}", end="", flush=True)

print("Monitoring audio levels... Press Ctrl+C to stop.")
try:
    with sd.InputStream(callback=print_sound_level, channels=1, samplerate=44100):
        while True:
            time.sleep(0.1)
except KeyboardInterrupt:
    print("\nStopped.")
except Exception as e:
    print(f"\nError: {e}")
