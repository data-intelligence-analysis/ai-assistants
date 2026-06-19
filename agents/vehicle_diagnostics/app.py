#!usr/bin/python3

#AI OBD Agent
import asyncio
import json
import time
import socket
import os
import threading
import pyttsx3
import obd
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pydantic import BaseModel
from openai import OpenAI




# =========================
# CONFIG
# =========================
#CONFIGURE SPEECH SYSTEM
VOICE_ENABLED = True  # Toggle speech on/off
SPEECH_SYSTEM = "offline"  # Choose: "openai", "offline", or "macos"

# LLM HELPER
client = OpenAI(api_key="YOUR_API_KEY")
engine = pyttsx3.init()


# =========================
# SPEECH SYSTEM
# =========================
def format_for_speech(text):
    return text.replace("%", " percent").replace("rpm", " R P M")

def speak(text: str, system):
    """
    Speaks the text using the selected system. 
    Defaults to SPEECH_SYSTEM to prevent signature mismatch errors.
    """
    if not VOICE_ENABLED:
        return
        
    text_clean = format_for_speech(text)
    match system:
        case "openai":
            audio = client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="alloy",
                input=text_clean
            )
            # Option A: Use the SDK's built-in file-writing helper
            audio.write_to_file("speech.mp3")
            os.system("afplay speech.mp3")
            # Option B (Alternative): If you prefer using a 'with open' context manager:
            # with open("speech.mp3", "wb") as f:
            #     f.write(audio.read())
            # os.system("afplay speech.mp3")
        case "offline":
            engine.say(text_clean)
            engine.runAndWait()
        case "macos":
            def _run():
                os.system(f'say "{text_clean}"')
                # select a voice
                # os.system(f'say -v Samantha "{text}"')
            threading.Thread(target=_run).start()
        case _:
            # Raising an error for invalid input
            raise ValueError(f"Invalid command: '{system}'. Expected 'openai' or 'offline', or 'macos'.")
        
# =========================
# INTENT PARSING (LLM)
# =========================
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

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}  # Forces JSON response
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Failed to parse intent: {e}")
        return {"intent": "unknown", "metric": None, "action": "get_value"}

# =========================
# VEHICLE TELEMETRICS ANALYTICS
# =========================
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

# def advanced_efficiency(data):
#     rpm = data.get("rpm", 0)
#     speed = data.get("speed", 0)

#     score = 100

#     if rpm > 3000:
#         score -= 30
#     if speed < 20 and rpm > 2000:
#         score -= 20
#     if speed > 60 and rpm < 2000:
#         score += 10

#     if score > 85:
#         status = "Excellent"
#     elif score > 60:
#         status = "Good"
#     else:
#         status = "Poor"

#     return {
#         "score": score,
#         "status": status
#     }

# =========================
# REAL OBD vs EMULATOR SOCKET LISTENER
# =========================
latest_data = {"rpm": 0, "speed": 0, "fuel": 0}
connected_clients = []

async def obd_listener():
    """
    To use a REAL car OBD-II adapter, replace this entire function with:
    """
    # connection = obd.OBD() # Auto-connects to USB/Bluetooth ELM327
    connection = obd.Async()
    connection.watch(obd.commands.RPM)
    connection.start()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 8765))
    server.listen(1)

    print("OBD Bridge running on port 8765...")

    client, addr = server.accept()
    print("Client connected:", addr)
    
    while True:
        latest_data["rpm"] = connection.query(obd.commands.RPM).value.magnitude if connection.query(obd.commands.RPM).value else None,
        latest_data["speed"] = connection.query(obd.commands.SPEED).value.magnitude if connection.query(obd.commands.SPEED).value else None,
        latest_data["fuel"] = connection.query(obd.commands.FUEL_LEVEL).value.magnitude if connection.query(obd.commands.FUEL_LEVEL).value else None
        client.send((json.dumps(latest_data) + "\n").encode())
        # time.sleep(1)
        await asyncio.sleep(1)
    

async def simulated_obd_listener(obd=None):
    """
    If using an emulator, this connects to the TCP stream.
    """
    global latest_data
    OBD_HOST = "0.0.0.0" #"host.docker.internal"
    OBD_PORT = 8000
    
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("0.0.0.0", 8765)) # s.connect((OBD_HOST, OBD_PORT))
            print(f"Connected to OBD stream at {OBD_HOST}:{OBD_PORT}")
            while True:
                #provide simulated data for testing
                #Fix this error - Connected to OBD stream at 0.0.0.0:8000 OBD Connection lost/failed: [Errno 107] Transport endpoint is not connected. Retrying in 5 seconds...
                if obd:
                    line = s.recv(1024).decode()
                    if line:
                        latest_data = json.loads(line.strip())
                    await asyncio.sleep(1)
                else:
                    # Simulate data for testing without an actual OBD stream
                    latest_data["rpm"] = 1500 + int(500 * time.time() % 1)  # Simulated RPM
                    latest_data["speed"] = 30 + int(10 * time.time() % 1)   # Simulated Speed
                    latest_data["fuel"] = 50 - int(5 * time.time() % 1)      # Simulated Fuel Level
                    print(f"Simulated Data: {latest_data}")
                    await asyncio.sleep(5)
        except Exception as e:
            print(f"OBD Connection lost/failed: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)

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

# =========================
# API & WEB INTERFACE
# =========================
# app.mount("/static", StaticFiles(directory="static"), name="static")
# Point FastAPI to your templates directory
# templates = Jinja2Templates(directory="templates")
base_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    asyncio.create_task(simulated_obd_listener(obd=False)) #set to true to connect to obd, false for simulated data
    yield
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)

# @app.get("/")
# async def ui():
#     # with open("templates/index.html") as f:
#     #     return HTMLResponse(f.read())
#     return FileResponse("templates/index.html")
# This calculates the exact absolute directory path dynamically

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    # Pass data to the HTML template via a dictionary context
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"username": "Dennis", "latest_data": latest_data}
    )

@app.websocket("/ui-stream")
async def ui_stream(ws: WebSocket):
    await ws.accept()
    connected_clients.append(ws)

    try:
        while True:
            await asyncio.sleep(1)
    except:
        connected_clients.remove(ws)

# @app.on_event("startup")
# async def startup():
#     asyncio.create_task(simulated_obd_listener())



@app.get("/data")
def get_data():
    return latest_data

@app.get("/ws")
def get_ws_data():
    # Fallback for browser access or when WebSocket isn't available.
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
    elif intent == "get_metric" or intent in ["speed", "rpm", "fuel"]:
        # Fallback to specific keys if generic metric isn't populated
        metric = intent_data.get("metric") or intent 
        value = latest_data.get(metric, "unknown")
        
        unit = "mph" if metric == "speed" else "percent" if metric == "fuel" else ""
        response_text = f"{metric} is {value} {unit}".strip()
        speak(response_text)
        return {"answer": response_text}
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
    response = "I don't understand that command yet."
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
# unzip vosk-model-small-en-us-0.15.zip