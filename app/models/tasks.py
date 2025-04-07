from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from enum import Enum

class Task(BaseModel):
    task_id: UUID
    file_url: str
    callback_postfix: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    
class TaskType(Enum):
    CONVERT = 1
    DIARIZE = 2
    TRANSCRIBE = 3
    