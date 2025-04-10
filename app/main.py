from app.consumer.kafka_consumer import start_all_consumers
from app.utils.logger import get_logger

logger = get_logger("Main")

if __name__ == "__main__":
    try:
        logger.info("Starting Kafka consumer service...")
        start_all_consumers()
    except KeyboardInterrupt:
        logger.info("Kafka consumer stopped by user.")
    except Exception as e:
        logger.exception(f"Unhandled exception in main: {e}")