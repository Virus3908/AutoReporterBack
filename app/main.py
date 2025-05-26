from app.kafka.consumer import start_consumer
from app.utils.logger import get_logger
from app.utils.startup import check_s3_connection

logger = get_logger("Main")

if __name__ == "__main__":
    try:
        logger.info("Check s3 connection")
        check_s3_connection()
        logger.info("Starting Kafka consumer service...")
        start_consumer()
    except KeyboardInterrupt:
        logger.info("Kafka consumer stopped by user.")
    except Exception as e:
        logger.exception(f"Unhandled exception in main: {e}")
