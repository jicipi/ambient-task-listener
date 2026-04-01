from pydantic import BaseModel


class TextInput(BaseModel):
    text: str


class ListItemInput(BaseModel):
    item: str
    source_transcript: str | None = None
    scheduled_date: str | None = None


class UpdateItemInput(BaseModel):
    done: bool


class RenameItemInput(BaseModel):
    text: str


class ReorderInput(BaseModel):
    ids: list[str]