from pydantic import BaseModel
from uuid import UUID
from enum import Enum

class TaskWithFile(BaseModel):
    task_id: UUID
    file_url: str
    callback_postfix: str
    
    
class TaskType(Enum):
    CONVERT = 1
    DIARIZE = 2
    TRANSCRIBE = 3
    