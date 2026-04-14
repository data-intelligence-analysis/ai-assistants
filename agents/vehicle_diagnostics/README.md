# Vehicle Diagnostics

Let’s build you a local AI OBD agent that runs in Docker on your laptop and talks to your car via your OBDLink MX+ (MX201).

This will:

Connect to your car via Bluetooth (BLE or serial)

Stream live data (RPM, speed, fuel, etc.)

Expose a local API (FastAPI)

Support LLM + voice commands

Run entirely in a Docker container



---

🧠 Architecture

[Car ECU] 
   ↓
[OBDLink MX+]
   ↓ Bluetooth
[Mac (Docker Container)]
   ↓
[Python OBD Agent]
   ├── python-obd (data)
   ├── BLE fallback (bleak)
   ├── FastAPI (API)
   ├── WebSocket (streaming)
   ├── Voice + LLM (commands)

```bash
Mic → Wake Word ("Hey Car") → Listen → Transcribe → LLM → OBD Data → Response → Speak
```

---

⚠️ Important (Mac + Docker Limitation)

Docker cannot directly access Bluetooth on macOS.

👉 So we use this pattern:

Host (Mac) handles Bluetooth connection

Docker connects via:

Serial bridge, or

TCP socket proxy




---

✅ Step 1 — Install Dependencies on Mac (Host)

brew install blueutil
pip install python-obd bleak

Pair your MX+:

bluetoothctl
# or use macOS Bluetooth settings


---

✅ Step 2 — Create OBD Bridge (Host → Docker)

Create:

obd_bridge.py

import obd
import socket
import json
import time

connection = obd.OBD()  # auto-connect

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("0.0.0.0", 8765))
server.listen(1)

print("OBD Bridge running on port 8765...")

client, addr = server.accept()
print("Client connected:", addr)

while True:
    data = {
        "rpm": connection.query(obd.commands.RPM).value.magnitude if connection.query(obd.commands.RPM).value else None,
        "speed": connection.query(obd.commands.SPEED).value.magnitude if connection.query(obd.commands.SPEED).value else None,
        "fuel": connection.query(obd.commands.FUEL_LEVEL).value.magnitude if connection.query(obd.commands.FUEL_LEVEL).value else None,
    }

    client.send((json.dumps(data) + "\n").encode())
    time.sleep(1)

Run it:

python obd_bridge.py


---

🐳 Step 3 — Dockerized AI Agent

Dockerfile

FROM python:3.11-slim

WORKDIR /app

RUN pip install fastapi uvicorn websockets openai pydantic

COPY . .

CMD ["python", "app.py"]


---

app.py (AI OBD Agent)

import asyncio
import json
import socket
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel

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
    text = q.text.lower()

    if "fuel" in text:
        return {"answer": f"Fuel level is {latest_data.get('fuel')}%"}
    elif "speed" in text:
        return {"answer": f"Speed is {latest_data.get('speed')} mph"}
    elif "rpm" in text:
        return {"answer": f"RPM is {latest_data.get('rpm')}"}

    return {"answer": "I don't understand yet."}


---

▶️ Step 4 — Run the Container

docker build -t obd-agent .
docker run -p 8000:8000 obd-agent


---

🌐 Step 5 — Test

Get live data:

curl http://localhost:8000/data

Ask AI:

curl -X POST http://localhost:8000/ask \
-H "Content-Type: application/json" \
-d '{"text":"how much fuel do I have?"}'


---

🎤 Step 6 — Add Voice (Optional Upgrade)

We can integrate:

Vosk (offline) OR

OpenAI Whisper (cloud)


Say:

> “What’s my fuel level?”



→ Agent responds via API or speech


---

🔥 Step 7 — Upgrade to Full AI Agent

Next upgrades I can build for you:

🧠 LLM Integration

Natural language → OBD commands

“Am I driving efficiently?”


📊 Streaming Dashboard

Real-time charts (RPM, speed, fuel)


🚨 Smart Alerts

Engine overheating

Low fuel warning


☁️ Cloud Sync

Store trips + analytics


📱 Connect to Your React Native App

Same API → mobile dashboard



---

⚡ Pro Tip (Performance)

Use async OBD polling:

connection = obd.Async()
connection.watch(obd.commands.RPM)
connection.start()


---

🚀 Summary

You now have:

Local Docker AI agent

Real-time car telemetry

Voice-ready + AI-ready architecture

Works with your MX+ adapter



---

If you want next level, I can:

🔥 Add **auto trip recording + driving score AI**

📊 Build a **Tesla-style dashboard UI**

🤖 Turn this into a **full SaaS (subscription-based OBD platform)**