from pydantic import BaseModel, HttpUrl
from uuid import UUID

class RequestFile(BaseModel):
    file_url: str
    callback_url: str

class ResponseStatus(BaseModel):
    uuid: UUID
    status: int