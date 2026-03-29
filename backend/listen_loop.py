import tempfile
from pathlib import Path

import numpy as np
from scipy.io.wavfile import write

from app.transcription import transcribe_audio_file
from app.multi_action import extract_multiple_actions
from app.cleaning import normalize_transcript, clean_item
from app.cleaning import parse_shopping_item
from app.storage import add_item
from app.storage import add_pending_item
from app.vad_listener import VADRecorder
from app.fuzzy_corrector import correct_item


import requests

recorder = VADRecorder(device=2) #Macbook pro
#recorder = VADRecorder(device=1) #Airpods
#recorder = VADRecorder(device=4) #MacBook pro avec Airpods connectés


def notify_backend(event: str = "update") -> None:
    try:
        requests.post(
            "http://127.0.0.1:8000/internal/notify",
            json={"event": event},
            timeout=1,
        )
    except Exception:
        pass


def process_audio(audio_bytes):
    if not audio_bytes:
        print("Aucun audio capté.")
        return

    audio_array = np.frombuffer(audio_bytes, dtype=np.int16)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = tmp.name

    write(wav_path, 16000, audio_array)

    try:
        transcript = transcribe_audio_file(wav_path)
        transcript = normalize_transcript(transcript)

        print("\nTranscript :", transcript)

        actions = extract_multiple_actions(transcript)
        print("DEBUG actions =", actions)

        if not actions:
            print("Aucune action détectée")
            return

        for action in actions:
            if action["item"]:
                item = clean_item(action["item"])

                if action["list"] in ("todo", "todo_pro"):
                    item = correct_item(item)

                if action["intent"] == "unknown":
                    continue

                if action.get("decision") == "ignore":
                    print("→ ignoré")
                    continue

                if action.get("decision") == "confirm":
                    print("→ à confirmer :", action["intent"], "-", item)
                    add_pending_item(action)
                    notify_backend("update")
                    continue

                added = add_item(action["list"], item, transcript)

                if action["list"] == "shopping":
                    parsed = parse_shopping_item(item)
                    display_text = parsed["text"]

                    if parsed["quantity"] is not None:
                        if parsed["unit"]:
                            display_text = f'{parsed["quantity"]} {parsed["unit"]} {parsed["text"]}'
                        else:
                            display_text = f'{parsed["quantity"]} {parsed["text"]}'
                else:
                    display_text = item

                if added:
                    print("→ ajouté dans", action["list"], ":", display_text)
                    notify_backend("update")
                else:
                    print("→ déjà présent dans", action["list"], ":", display_text)

    finally:
        Path(wav_path).unlink(missing_ok=True)


def main():
    print("\nAmbient Task Listener — écoute continue")
    print("Parle quand tu veux. Ctrl+C pour arrêter.\n")

    try:
        while True:
            audio = recorder.record_phrase()
            process_audio(audio)
    except KeyboardInterrupt:
        print("\nArrêt propre.")

if __name__ == "__main__":
    main()