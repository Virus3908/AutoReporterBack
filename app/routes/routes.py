from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.core.database import get_db
from app.schemas.convert import RequestFile, ResponseStatus, RequestSegment
from app.models.task_models import Task, Convert, Diarize, Transcribe
from app.core.db_transaction import transaction

router = APIRouter(prefix="/api", tags=["convert", "diarize", "transcribe"])

@router.post("/convert", response_model=ResponseStatus)
async def create_convert_task(
    payload: RequestFile,
    db: AsyncSession = Depends(get_db)
):
    task_id = uuid4()

    async with transaction(db):
        new_task = Task(
            id=task_id,
            type=1,
            status=0,
            callback_url=payload.callback_url
        )
        db.add(new_task)

        new_convert = Convert(
            task_id=task_id,
            file_url=payload.file_url
        )
        db.add(new_convert)


    return ResponseStatus(uuid=task_id, status=0)

@router.post("/diarize", response_model=ResponseStatus)
async def create_diarize_task(
    payload: RequestFile,
    db: AsyncSession = Depends(get_db)
):
    task_id = uuid4()
    
    async with transaction(db):
        new_task = Task(
            id=task_id,
            type=2,
            status=0,
            callback_url=payload.callback_url
        )
        db.add(new_task)    
        new_diarize = Diarize(
            task_id=task_id,
            file_url=payload.file_url
        )
        db.add(new_diarize)
    
    return ResponseStatus(uuid=task_id, status=0)

@router.post("/transcribe", response_model=ResponseStatus)
async def create_transcribe_task(
    payload: RequestSegment,
    db: AsyncSession = Depends(get_db)
):
    task_id = uuid4()
    async with transaction(db):
        new_task = Task(
            id=task_id,
            type=3,
            status=0,
            callback_url=payload.callback_url
        )
        db.add(new_task)
        new_transcribe = Transcribe(
            task_id=task_id,
            file_url=payload.file_url,
            start_time=payload.segment.start_time,
            end_time=payload.segment.end_time
        )
        db.add(new_transcribe)
        
    return ResponseStatus(uuid=task_id, status=0)
    