import sounddevice as sd
import numpy as np
import openwakeword
import queue
import json
from vosk import Model as VoskModel, KaldiRecognizer
import threading
import time

from ai import call



HOTWORD_MODEL_PATH = "models/hey_jarvis_v0.1.onnx"
SENSITIVITY = 0.4

oww_model = openwakeword.Model(
    inference_framework="onnx",
    wakeword_models=[HOTWORD_MODEL_PATH]
)

vosk_model = VoskModel("models/vosk-model-small-en-us-0.15")
q = queue.Queue()

# flag, hogy STT fusson-e
stt_running = False

def stt_process(duration=7):
    global stt_running
    stt_running = True
    rec = KaldiRecognizer(vosk_model, 16000)
    print("🎙 STT: beszélj most...")
    start = time.time()

    while True:
        if not q.empty():
            data = q.get()
            if rec.AcceptWaveform(data):
                start = time.time()  # reset időzítő, ha van adat
                res = json.loads(rec.Result())
                text = res.get("text", "")
                if text.strip() and len(text.split()) > 2:
                    print("📝 STT felismert:", text)
                    call(text)  # itt indítjuk a TTS-et
                    start = time.time()  # reset időzítő a beszéd után
                    q.queue.clear()
                    print("🎙 STT: beszéljen most...")
            else:
                if time.time() - start > duration:
                    break
        else:
            if time.time() - start > duration:
                break

    print("🔄 Vissza a hotword figyeléshez...")
    stt_running = False

def callback(indata, frames, time_, status):
    global stt_running
    audio = np.frombuffer(indata, dtype=np.int16)
    prediction = oww_model.predict(audio)

    # Ha már STT megy, ne indítsd újra
    if not stt_running:
        for key, value in prediction.items():
            if value > SENSITIVITY:
                print(f"✅ Hotword felismerve: {key} ({value:.2f})")
                threading.Thread(target=stt_process, args=(5,), daemon=True).start()

    # Mindig pakoljuk a hangot a STT queue-ba
    q.put(indata.tobytes())

with sd.InputStream(callback=callback, channels=1, samplerate=16000, dtype='int16'):
    print("🎤 Csak a Jarvis hotword-re figyelek...")
    while True:
        sd.sleep(1000)
