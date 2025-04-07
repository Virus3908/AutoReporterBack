from pydantic import BaseModel
from uuid import UUID
from enum import Enum

class KafkaMessage(BaseModel):
    data: str
    callback_url: str
    task_type: int
