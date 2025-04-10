import json
import time
import threading
from kafka import KafkaConsumer
from app.config.settings import settings
from app.handlers.convert_handler import handle_convert_task
from app.handlers.diarize_handler import handle_diarize_task
from app.handlers.transcribe_handler import handle_transcribe_task
from app.utils.logger import get_logger

logger = get_logger("KafkaConsumer")

TOPIC_HANDLER_MAP = {
    "convert": handle_convert_task,
    "diarize": handle_diarize_task,
    "transcribe": handle_transcribe_task,
}

def start_consumer_for_topic(topic: str):
    logger.info(f"Starting consumer for topic: {topic}")

    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=settings.kafka_brokers,
        auto_offset_reset="earliest",
        group_id=f"{settings.kafka_group_id}-{topic}",
        enable_auto_commit=True,
        value_deserializer=lambda m: m,
    )

    handler = TOPIC_HANDLER_MAP[topic]

    try:
        while True:
            records = consumer.poll(timeout_ms=500)
            if not records:
                time.sleep(0.1)
                continue

            for tp, messages in records.items():
                for msg in messages:
                    try:
                        logger.info(f"Handling task from topic '{topic}' with offset {msg.offset}")
                        handler(msg)

                    except Exception as e:
                        logger.exception(f"Failed to process message from topic {topic}: {e}")
    except KeyboardInterrupt:
        logger.info(f"Kafka consumer for topic {topic} stopped by user")
    finally:
        consumer.close()
        logger.info(f"Kafka consumer for topic {topic} closed")

def start_all_consumers():
    for topic in settings.kafka_topics:
        if topic not in TOPIC_HANDLER_MAP:
            logger.warning(f"⚠️ No handler defined for topic: {topic}, skipping.")
            continue

        t = threading.Thread(target=start_consumer_for_topic, args=(topic,), daemon=True)
        t.start()

    logger.info("Selected Kafka topic consumers started.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping all Kafka consumers.")