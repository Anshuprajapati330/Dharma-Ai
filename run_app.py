import os
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def start_backend():
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def start_frontend():
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    return subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "chatbot.py", "--server.port", "8501", "--server.headless", "true"],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def main():
    backend = start_backend()
    time.sleep(2)
    frontend = start_frontend()
    print("Backend starting at http://127.0.0.1:8000")
    print("Frontend starting at http://127.0.0.1:8501")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        backend.terminate()
        frontend.terminate()
        backend.wait(timeout=5)
        frontend.wait(timeout=5)


if __name__ == "__main__":
    main()
