# voice_agent.py
import queue
import sounddevice as sd
import json
from vosk import Model, KaldiRecognizer

q = queue.Queue()

MODEL_PATH = "model/vosk-model-small-en-us-0.15"
model = Model(MODEL_PATH)
recognizer = KaldiRecognizer(model, 16000)

WAKE_WORD = "hey car"

def audio_callback(indata, frames, time, status):
    q.put(bytes(indata))

def listen_loop(on_command):
    with sd.RawInputStream(
        samplerate=16000,
        blocksize=8000,
        dtype="int16",
        channels=1,
        callback=audio_callback
    ):
        print("🎤 Listening for wake word...")

        buffer_text = ""
        active = False

        while True:
            data = q.get()

            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").lower()

                if not text:
                    continue

                print("Heard:", text)

                # 🔥 Wake word detection
                if WAKE_WORD in text:
                    print("🧠 Wake word detected!")
                    active = True
                    buffer_text = ""
                    continue

                # 🎧 Active conversation mode
                if active:
                    buffer_text += " " + text

                    # pause detection (simple)
                    if len(buffer_text.split()) > 3:
                        print("🧠 Processing:", buffer_text)
                        on_command(buffer_text.strip())
                        buffer_text = ""
                        active = False
                        print("🎤 Listening for wake word again...")