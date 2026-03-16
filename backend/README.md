# Backend

Backend local du projet Ambient Task Listener.

## Rôle

- recevoir ou traiter de l’audio
- transcrire localement sur le Mac
- détecter une action utile
- produire un JSON exploitable par l’application

## Stack

- Python 3.11 arm64
- MLX Whisper
- FastAPI
- Uvicorn

## Setup

Créer et activer le venv avec le Python arm64 :

```bash
/opt/homebrew/bin/python3.11 -m venv .venv
source .venv/bin/activate