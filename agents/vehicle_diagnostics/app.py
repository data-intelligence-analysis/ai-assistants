#!usr/bin/python3

#AI OBD Agent
import asyncio
import json
import socket
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
from openai import OpenAI
import os
import threading
import pyttsx3
from fastapi.responses import HTMLResponse


client = OpenAI()
engine = pyttsx3.init()

def speak(text: str, system):
    match system
        case "openai":
            audio = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=text
    )
            with open("speech.mp3", "wb") as f:
        f.write(audio.read())
    
            os.system("afplay speech.mp3")
        case "offline":
            engine.say(text)
            engine.runAndWait()
        case "macos":
            if not VOICE_ENABLED:
               return

    def _run():
        os.system(f'say "{text}"')
        # select a voice
        # os.system(f'say -v Samantha "{text}"')
   threading.Thread(target=_run).start()
         case _:
            # Raising an error for invalid input
            raise ValueError(f"Invalid command: '{command}'. Expected 'start' or 'stop'.")
        

# MAC OS VOICE ENABLED SPEECH
VOICE_ENABLED = True  # toggle on/off
def format_for_speech(text):
    return text.replace("%", " percent").replace("rpm", " R P M")

def speak(text: str):
    if not VOICE_ENABLED:
        return

    def _run():
        os.system(f'say "{text}"')
        # select a voice
        # os.system(f'say -v Samantha "{text}"')
   threading.Thread(target=_run).start()



# LLM HELPER
client = OpenAI(api_key="YOUR_API_KEY")

def parse_intent(user_input: str):
    prompt = f"""
    You are an AI car assistant.
    Extract the user's intent from this sentence.

    Input: "{user_input}"

    Return JSON:
    {{
      "intent": "...",
      "metric": "...",
      "action": "analyze | get_value"
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return eval(response.choices[0].message.content)

# Driving Efficiency Logic
def analyze_efficiency(data):
    rpm = data.get("rpm") or 0
    speed = data.get("speed") or 0
    fuel = data.get("fuel") or 0

    if speed == 0:
        return "Vehicle is stationary."

    ratio = rpm / max(speed, 1)

    if rpm > 3000:
        return "You are driving aggressively (high RPM)."
    elif ratio > 120:
        return "Engine load is high for your speed. Try smoother acceleration."
    elif rpm < 2000 and speed > 40:
        return "You are driving efficiently."
    else:
        return "Driving is moderate, could be optimized."

def advanced_efficiency(data):
    rpm = data.get("rpm", 0)
    speed = data.get("speed", 0)

    score = 100

    if rpm > 3000:
        score -= 30
    if speed < 20 and rpm > 2000:
        score -= 20
    if speed > 60 and rpm < 2000:
        score += 10

    if score > 85:
        status = "Excellent"
    elif score > 60:
        status = "Good"
    else:
        status = "Poor"

    return {
        "score": score,
        "status": status
    }

connected_clients = []

def broadcast(event):
    for client in connected_clients:
        try:
            asyncio.create_task(client.send_json(event))
        except:
            pass

def handle_voice_command(text):
    broadcast({"type": "processing", "text": text})

    intent_data = parse_intent(text)

    broadcast({
        "type": "intent_detected",
        "intent": intent_data
    })

    response = ask(Query(text=text))
    answer = response["answer"]

    broadcast({
        "type": "response",
        "text": answer
    })

    speak(answer)

    broadcast({"type": "idle"})

    #add inside voice loop
    broadcast({"type": "listening"})

app = FastAPI()

OBD_HOST = "host.docker.internal"
OBD_PORT = 8765

latest_data = {}

async def obd_listener():
    global latest_data
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((OBD_HOST, OBD_PORT))

    while True:
        line = s.recv(1024).decode()
        if line:
            try:
                latest_data = json.loads(line.strip())
            except:
                pass

@app.get("/")
def ui():
    with open("templates/index.html") as f:
        return HTMLResponse(f.read())

@app.websocket("/ui-stream")
async def ui_stream(ws: WebSocket):
    await ws.accept()
    connected_clients.append(ws)

    try:
        while True:
            await asyncio.sleep(1)
    except:
        connected_clients.remove(ws)

@app.on_event("startup")
async def startup():
    asyncio.create_task(obd_listener())

@app.get("/data")
def get_data():
    return latest_data

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    while True:
        await ws.send_json(latest_data)
        await asyncio.sleep(1)

# 🧠 Simple AI Command Handler
class Query(BaseModel):
    text: str

@app.post("/ask")
def ask(q: Query):
    #text = q.lower()
    intent_data = parse_intent(q.text)
    intent = intent_data.get("intent")
    if intent == "efficiency_check":
        result = analyze_efficiency(latest_data)
        speak(result)
        return {"answer": result}

    elif intent == "get_metric":
        metric = intent_data.get("metric")
        value = latest_data.get(metric)
        speak(f"{metric} is {value}")
        return {"answer": f"{metric} is {value}"}
    elif intent == "fuel":
        response = f"Fuel level is {latest_data.get('fuel')}%"
        speak(response)
        return {"answer": f"Fuel level is {latest_data.get('fuel')}%"}
    elif intent == "speed":
        response = f"Speed is {latest_data.get('speed')} mph"
        speak(response)
        return {"answer": f"Speed is {latest_data.get('speed')} mph"}
    elif intent == "rpm":
        response = f"RPM is {latest_data.get('rpm')}"
        speak(response)
        return {"answer": f"RPM is {latest_data.get('rpm')}"}
    response = "I don't understand yet."
    speak(response)
    return {"answer": response}

@app.post("/voice/toggle")
def toggle_voice():
    global VOICE_ENABLED
    VOICE_ENABLED = not VOICE_ENABLED
    return {"voice_enabled": VOICE_ENABLED}

## Bash Test
#curl -X POST http://localhost:8000/ask \
#-H "Content-Type: application/json" \
#-d '{"text":"what is my speed?"}'

# List Voices
# say -v "?"

# wake word + Continuous Listening engine
#mkdir model
#cd model
#wget #https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip