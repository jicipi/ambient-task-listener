from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.action_extractor import extract_action_with_fallback as extract_action
from app.schemas import TextInput, ListItemInput, UpdateItemInput, RenameItemInput
from app.storage import add_item, get_all_lists, get_list, delete_item, update_item_done, rename_item
from app.transcription import transcribe_audio_file, transcribe_bytes_to_text


app = FastAPI(title="Ambient Task Listener Backend")

#app.add_middleware(
#>    CORSMiddleware,
#    allow_origins=[
#        "http://localhost:49951",
#        "http://127.0.0.1:49951",
#        "http://localhost:8000",
#        "http://127.0.0.1:8000",
#    ],
#    allow_credentials=True,
#    allow_methods=["*"],
#    allow_headers=["*"],
#)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VALID_LISTS = {"shopping", "todo", "todo_pro", "appointments", "ideas"}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/lists")
def read_all_lists() -> dict:
    return get_all_lists()


@app.get("/lists/{list_name}")
def read_list(list_name: str) -> dict:
    if list_name not in VALID_LISTS:
        raise HTTPException(status_code=404, detail="Unknown list")

    return {
        "list": list_name,
        "items": get_list(list_name),
    }


@app.post("/lists/{list_name}")
def create_list_item(list_name: str, payload: ListItemInput) -> dict:
    if list_name not in VALID_LISTS:
        raise HTTPException(status_code=404, detail="Unknown list")

    added = add_item(list_name, payload.item, payload.source_transcript)

    return {
        "list": list_name,
        "item": payload.item,
        "added": added,
    }


@app.delete("/lists/{list_name}/item/{item_id}")
def remove_list_item(list_name: str, item_id: str) -> dict:
    if list_name not in VALID_LISTS:
        raise HTTPException(status_code=404, detail="Unknown list")

    deleted = delete_item(list_name, item_id)

    return {
        "list": list_name,
        "item_id": item_id,
        "deleted": deleted,
    }


@app.patch("/lists/{list_name}/item/{item_id}")
def patch_list_item(list_name: str, item_id: str, payload: UpdateItemInput) -> dict:
    if list_name not in VALID_LISTS:
        raise HTTPException(status_code=404, detail="Unknown list")

    updated = update_item_done(list_name, item_id, payload.done)

    return {
        "list": list_name,
        "item_id": item_id,
        "updated": updated,
        "done": payload.done,
    }

@app.delete("/lists/{list_name}")
def clear_list(list_name: str) -> dict:
    if list_name not in VALID_LISTS:
        raise HTTPException(status_code=404, detail="Unknown list")

    from app.storage import _save_list

    _save_list(list_name, [])

    return {
        "list": list_name,
        "cleared": True
    }

@app.patch("/lists/{list_name}/item/{item_id}/rename")
def rename_list_item(list_name: str, item_id: str, payload: RenameItemInput) -> dict:
    if list_name not in VALID_LISTS:
        raise HTTPException(status_code=404, detail="Unknown list")

    updated = rename_item(list_name, item_id, payload.text)

    return {
        "list": list_name,
        "item_id": item_id,
        "updated": updated,
        "text": payload.text,
    }

@app.post("/extract")
def extract(text_input: TextInput) -> dict:
    action = extract_action(text_input.text)
    return {
        "transcript": text_input.text,
        **action,
    }


@app.post("/transcribe-file")
def transcribe_file(payload: TextInput) -> dict:
    audio_path = payload.text.strip()

    if not Path(audio_path).exists():
        raise HTTPException(status_code=404, detail="Audio file not found")

    transcript = transcribe_audio_file(audio_path)
    return {
        "transcript": transcript,
    }


@app.post("/audio-to-action")
async def audio_to_action(file: UploadFile = File(...)) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    suffix = Path(file.filename).suffix.lower() or ".wav"
    allowed_suffixes = {".wav", ".mp3", ".m4a", ".mp4", ".mpeg", ".mpga", ".webm"}

    if suffix not in allowed_suffixes:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format: {suffix}",
        )

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")

    transcript = transcribe_bytes_to_text(audio_bytes, suffix=suffix)
    action = extract_action(transcript)

    return {
        "filename": file.filename,
        "transcript": transcript,
        **{k: v for k, v in action.items() if k != "transcript"},
    }