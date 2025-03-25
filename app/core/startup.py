import asyncio
from sqlalchemy.ext.asyncio import AsyncEngine
from botocore.exceptions import ClientError
from sqlalchemy import text
from app.core.logger import logger


async def check_db_connection(engine: AsyncEngine, retries: int = 3, delay: int = 2):
    for attempt in range(1, retries + 1):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Successfully connected to the database.")
            return
        except Exception as e:
            logger.warning(f"DB connection failed (attempt {attempt}/{retries}): {e}")
            if attempt < retries:
                await asyncio.sleep(delay)
            else:
                logger.critical("Could not connect to the database after multiple attempts.")
                raise
            
async def check_s3_connection(s3_client, retries: int = 3, delay: int = 2):
    for attempt in range(1, retries + 1):
        try:
            s3_client.client.head_bucket(Bucket=s3_client.bucket)
            logger.info(f"Successfully connected to S3 bucket '{s3_client.bucket}'")
            return
        except ClientError as e:
            logger.warning(f"S3 connection failed (attempt {attempt}/{retries}): {e}")
            if attempt < retries:
                await asyncio.sleep(delay)
            else:
                logger.critical("Could not connect to S3 after multiple attempts.")
                raise