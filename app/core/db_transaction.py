from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from app.core.logger import logger

@asynccontextmanager
async def transaction(db: AsyncSession):
    try:
        yield
        await db.commit()
    except SQLAlchemyError as e:
        await db.rollback()
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Database error: " + str(e))