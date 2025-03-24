from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db

app = FastAPI()

@app.get("/ping")
async def ping(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT 1"))
    value = result.scalar()
    return {"message": "pong", "db_response": value}

