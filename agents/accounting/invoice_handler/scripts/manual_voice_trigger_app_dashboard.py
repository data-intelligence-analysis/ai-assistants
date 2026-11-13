import argparse
import json
import os
import queue
import subprocess
import sys
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)
WORKSPACE_DIR = Path(__file__).resolve().parents[1]
DASHBOARD_APP = WORKSPACE_DIR / "dashboard" / "invoice_dashboard_app.py"
TOKEN_PATH = WORKSPACE_DIR / "dashboard" / "token.json"
DEFAULT_MODEL_PATH = WORKSPACE_DIR / "dashboard" / "vosk-model-small-en-us-0.15"
environment_mode = ''
VOICE_COMMANDS = {
    "show test invoice dashboard": "test",
    "open test invoice dashboard": "test",
    "test invoice dashboard": "test",
    "show production invoice dashboard": "production",
    "open production invoice dashboard": "production",
    "production invoice dashboard": "production",
    "show invoice dashboard": "test" if environment_mode in ("testing", "test") else "production",
}


class DashboardStartError(Exception):
    pass


def _dashboard_mode(command: str) -> str | None:
    normalized_command = " ".join(command.casefold().split())
    return VOICE_COMMANDS.get(normalized_command)


def _listen_for_voice_commands(environment_mode: str | None = None) -> None:
    model_path = Path(os.environ.get("VOSK_MODEL_PATH", DEFAULT_MODEL_PATH))
    if not model_path.is_dir():
        raise RuntimeError(
            "Offline speech model not found. Download and extract "
            "vosk-model-small-en-us-0.15 under dashboard/, or set "
            "VOSK_MODEL_PATH to the model directory."
        )

    try:
        import sounddevice as sd
        from vosk import KaldiRecognizer, Model
    except ImportError as error:
        raise RuntimeError(
            "Offline microphone listening requires vosk and sounddevice. "
            "Install the invoice_handler requirements."
        ) from error

    sample_rate = 16000
    model = Model(str(model_path))
    recognizer = KaldiRecognizer(
        model, sample_rate, json.dumps(list(VOICE_COMMANDS))
    )
    audio_queue: queue.Queue[bytes] = queue.Queue()

    def audio_callback(indata, _frames, _time_info, status) -> None:
        if status:
            print(f"Microphone warning: {status}", file=sys.stderr, flush=True)
        audio_queue.put(bytes(indata))

    print(
        "Listening on the terminal microphone. Say a supported invoice dashboard "
        "command; press Ctrl+C to stop.",
        flush=True,
    )
    try:
        with sd.RawInputStream(
            samplerate=sample_rate,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=audio_callback,
        ):
            while True:
                audio_data = audio_queue.get()
                if not recognizer.AcceptWaveform(audio_data):
                    continue

                command = json.loads(recognizer.Result()).get("text", "").strip()
                if not command:
                    continue

                print(f"Recognized voice command: {command}", flush=True)
                mode = _dashboard_mode(command)
                if mode is None:
                    print("That voice command is not supported.", flush=True)
                    continue
                if environment_mode is not None:
                    mode = environment_mode

                try:
                    process = _start_dashboard(mode)
                except DashboardStartError as error:
                    print(f"Dashboard launch failed: {error}", file=sys.stderr)
                    continue
                print(
                    f"Starting the {mode} invoice dashboard "
                    f"(process {process.pid}).",
                    flush=True,
                )
    except sd.PortAudioError as error:
        raise RuntimeError(f"Could not access the microphone: {error}") from error


def _start_dashboard(mode: str, port: int = 8501) -> subprocess.Popen:
    environment = os.environ.copy()
    environment.pop("APP_DATA_MODE", None)

    if mode == "production" and not environment.get("GOOGLE_TOKEN_JSON"):
        try:
            environment["GOOGLE_TOKEN_JSON"] = TOKEN_PATH.read_text(encoding="utf-8")
        except OSError as error:
            raise DashboardStartError(
                "Could not read the Gmail authorization token."
            ) from error

    environment_argument = "testing" if mode == "test" else "production"
    try:
        return subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(DASHBOARD_APP),
                f"--server.port={port}",
                "--server.address=127.0.0.1",
                "--",
                "--environment",
                environment_argument,
            ],
            cwd=WORKSPACE_DIR,
            env=environment,
            close_fds=True,
        )
    except OSError as error:
        raise DashboardStartError(
            "Could not start the invoice dashboard app."
        ) from error


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

    app.logger.info("Recognized voice command: %s", data["command"])
    mode = _dashboard_mode(data["command"])
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

    mode = app.config.get("ENVIRONMENT_MODE") or mode
    try:
        process = _start_dashboard(mode, app.config.get("PORT", 8501))
    except DashboardStartError as error:
        app.logger.error("Dashboard launch failed: %s", error)
        return jsonify(
            {"status": "error", "message": str(error)}
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
    parser = argparse.ArgumentParser(description="Trigger the invoice dashboard.")
    parser.add_argument(
        "--voice",
        nargs="+",
        metavar="COMMAND",
        help="run a supported command directly instead of listening",
    )
    parser.add_argument(
        "--http",
        action="store_true",
        help="start the optional localhost HTTP trigger instead of listening",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="port for the invoice dashboard",
    )
    parser.add_argument(
        "--environment",
        "--mode",
        choices=("testing", "production"),
        help="force the dashboard environment, overriding the mode in voice commands",
    )
    arguments = parser.parse_args()

    if arguments.voice and arguments.http:
        parser.error("--voice and --http cannot be used together")

    if isinstance(arguments.environment, str) and arguments.environment in ("testing", "test", "production"):
        environment_mode = (
            "test"
            if arguments.environment in ("testing", "test")
            else arguments.environment
        )
    else:
        raise ValueError("environment must be one of 'testing', 'test', or 'production'")
    app.config["ENVIRONMENT_MODE"] = environment_mode
    if arguments.port is not None:
        app.config["PORT"] = arguments.port

    if arguments.voice:
        voice = _dashboard_mode(" ".join(arguments.voice))
        if voice is None:
            parser.error(
                "unsupported voice command; use 'show test invoice dashboard' or "
                "'show production invoice dashboard'"
            )
        if environment_mode is not None:
            voice = environment_mode
        try:
            process = _start_dashboard(voice, app.config.get("PORT", 8501))
        except DashboardStartError as error:
            app.logger.error("Dashboard launch failed: %s", error)
            raise SystemExit(1) from error
        print(f"Starting the {voice} invoice dashboard (process {process.pid}).")
    elif arguments.http:
        app.run(host="127.0.0.1", port=app.config.get("PORT", 5001))
    else:
        try:
            _listen_for_voice_commands(environment_mode)
        except RuntimeError as error:
            parser.error(str(error))
