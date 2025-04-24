from app.client.s3_client import s3_client
from app.utils.logger import get_logger
from botocore.exceptions import ClientError
from time import sleep

logger = get_logger("startup")


def check_s3_connection(retries: int = 3, delay: int = 1):
    for attempt in range(1, retries+1):
        try:
            s3_client.check_connection()
            logger.info("Seccessfully connected to S3 bucket")
            return
        except ClientError as e:
            logger.warning(f"S3 connection failed (attempt {attempt}/{retries}): {e}")
            if attempt < retries:
                sleep(delay)
            else:
                logger.critical("Could not connect to S3 after multiple attempts.")
                raise
            