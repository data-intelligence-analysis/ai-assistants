
# OBD Bridge (Host -> Docker)

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