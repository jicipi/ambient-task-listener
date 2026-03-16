from __future__ import annotations

import json
import tempfile
from pathlib import Path

import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write as write_wav

from app.action_extractor import extract_action_with_fallback as extract_action
from app.transcription import transcribe_audio_file
from app.storage import add_item
from app.cleaning import clean_item, normalize_transcript
from app.fuzzy_corrector import correct_item
from app.multi_action import extract_multiple_actions


CHANNELS = 1
DURATION_SECONDS = 5
INPUT_DEVICE = 2  # Micro MacBook Pro


def record_wav(
    output_path: str,
    duration_seconds: int = DURATION_SECONDS,
    channels: int = CHANNELS,
    input_device: int | None = INPUT_DEVICE,
) -> Path:

    device_info = sd.query_devices(input_device)
    sample_rate = int(device_info["default_samplerate"])

    print(f"\nDevice utilisé : {input_device} ({device_info['name']})")
    print(f"Sample rate utilisé : {sample_rate} Hz")

    print("3...")
    print("2...")
    print("1...")
    print(f"Enregistrement pendant {duration_seconds} secondes...")

    audio = sd.rec(
        int(duration_seconds * sample_rate),
        samplerate=sample_rate,
        channels=channels,
        dtype="int16",
        device=input_device,
    )

    sd.wait()

    print("Enregistrement terminé.")

    if channels == 1:
        audio_to_save = audio.reshape(-1)
    else:
        audio_to_save = audio

    peak = int(np.max(np.abs(audio_to_save)))
    print(f"Niveau max capté : {peak}")

    write_wav(output_path, sample_rate, audio_to_save)

    return Path(output_path)


def run_once() -> None:

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = tmp.name

    try:

        record_wav(wav_path)

        raw_transcript = transcribe_audio_file(wav_path)
        print(f"\nTranscript brut       : {raw_transcript}")

        transcript = normalize_transcript(raw_transcript)
        print(f"Transcript normalisé : {transcript}")

        results = extract_multiple_actions(transcript)

        if not results:
            print("Aucune action détectée")

        for result in results:

            if result["item"]:
                result["item"] = clean_item(result["item"])

                if result["list"] in ("todo", "todo_pro"):
                    result["item"] = correct_item(result["item"])

            added = add_item(result["list"], result["item"], transcript)
            if added:
                print(f"→ ajouté dans la liste {result['list']}")
            else:
                print(f"→ déjà présent dans la liste {result['list']}")
        
        payload = {
            "audio_file": wav_path,
            "transcript": transcript,
            "actions": results,
        }

        print("\n=== RÉSULTAT FINAL ===")
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    finally:

        try:
            Path(wav_path).unlink(missing_ok=True)
        except Exception:
            pass


def main():

    print("Ambient Task Listener - mode boucle")
    print("Appuie sur Entrée pour enregistrer")
    print("Tape q puis Entrée pour quitter\n")

    while True:

        command = input("> ")

        if command.strip().lower() == "q":
            print("Arrêt.")
            break

        run_once()


if __name__ == "__main__":
    main()