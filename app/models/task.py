from pydantic import BaseModel
from uuid import UUID
from enum import Enum

class KafkaMessage(BaseModel):
    data: str
    callback_url: str

class ConvertTask(BaseModel):
    convert_id: UUID
    file_url: str
    task_type: int
    callback_postfix: str
    
    
class TaskType(Enum):
    CONVERT = 1
    DIARIZE = 2
    TRANSCRIBE = 3