
#AI OBD Agent
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