import subprocess
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)
WORKSPACE_DIR = Path(__file__).resolve().parents[1]
LAUNCHER = WORKSPACE_DIR / "scripts" / "voice_trigger_dashboard.sh"
VOICE_COMMANDS = {
    "show test invoice dashboard": "test",
    "open test invoice dashboard": "test",
    "test invoice dashboard": "test",
    "show production invoice dashboard": "production",
    "open production invoice dashboard": "production",
    "production invoice dashboard": "production",
}


@app.get("/health")
def health():
    return jsonify({"status": "ready"})


@app.post("/trigger-dashboard")
def trigger_dashboard():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("command"), str):
        return jsonify(
            {
                "status": "error",
                "message": "Send a JSON object with a supported voice command.",
            }
        ), 400

    command = " ".join(data["command"].casefold().split())
    mode = VOICE_COMMANDS.get(command)
    if mode is None:
        return jsonify(
            {
                "status": "rejected",
                "message": (
                    "Use 'show test invoice dashboard' or "
                    "'show production invoice dashboard'."
                ),
            }
        ), 400

    try:
        process = subprocess.Popen(
            ["/bin/bash", str(LAUNCHER), mode],
            cwd=WORKSPACE_DIR,
            close_fds=True,
        )
    except OSError as error:
        app.logger.error("Could not start the invoice dashboard launcher: %s", error)
        return jsonify(
            {"status": "error", "message": "Could not start the dashboard launcher."}
        ), 500

    return jsonify(
        {
            "status": "starting",
            "mode": mode,
            "process_id": process.pid,
            "message": f"Starting the {mode} invoice dashboard.",
        }
    ), 202


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001)
