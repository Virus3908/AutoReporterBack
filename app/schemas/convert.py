from pydantic import BaseModel
from uuid import UUID

class RequestFile(BaseModel):
    file_url: str
    callback_url: str

class ResponseStatus(BaseModel):
    uuid: UUID
    status: int

class Segment(BaseModel):
    start_time: float
    end_time: float
    speaker: int

class RequestSegment(BaseModel):
    file_url: str
    callback_url: str
    segment: Segment 