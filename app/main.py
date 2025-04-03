from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.database import engine
from app.core.s3_client import s3_client
from app.core.startup import logger, check_db_connection, check_s3_connection
from app.core.logger import logger
from app.routes.routes import router as convert_router
from app.worker.task_worker import task_worker
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        task_loop = asyncio.create_task(task_worker())
        yield
        logger.info("Shutting down")
        task_loop.cancel()
    except Exception as e:
        logger.critical(f"Startup failed: {e}")
        raise    
    
app = FastAPI(lifespan=lifespan)

app.include_router(convert_router)
