from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.core.database import get_db
from app.schemas.convert import RequestFile, ResponseStatus
from app.models.task_models import Task, Convert
from app.core.db_transaction import transaction

router = APIRouter(prefix="/api", tags=["convert"])

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
            id=uuid4(),
            task_id=task_id,
            file_url=payload.file_url
        )
        db.add(new_convert)


    return ResponseStatus(uuid=task_id, status=0)