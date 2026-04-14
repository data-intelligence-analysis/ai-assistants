
#AI OBD Agent
import asyncio
import json
import socket
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
from openai import OpenAI

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
        return {"answer": result}

    elif intent == "get_metric":
        metric = intent_data.get("metric")
        value = latest_data.get(metric)
        return {"answer": f"{metric} is {value}"}
    elif intent == "fuel":
        return {"answer": f"Fuel level is {latest_data.get('fuel')}%"}
    elif intent == "speed":
        return {"answer": f"Speed is {latest_data.get('speed')} mph"}
    elif intent == "rpm":
        return {"answer": f"RPM is {latest_data.get('rpm')}"}

    return {"answer": "I don't understand yet."}


