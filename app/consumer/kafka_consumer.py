import json
from kafka import KafkaConsumer
from app.config.settings import settings
from app.handlers.convert_handler import handle_convert_task
from app.models.task import TaskType
from app.utils.logger import get_logger
from app.models.task import KafkaMessage, ConvertTask
import time

logger = get_logger("KafkaConsumer")

TASK_HANDLERS = {
    TaskType.CONVERT: handle_convert_task,
    # TaskType.DIARIZE: handle_diarize_task,  # Добавим позже
}

def start_consumer():
    logger.info("Starting Kafka consumer...")

    consumer = KafkaConsumer(
        settings.kafka_topic,
        bootstrap_servers=settings.kafka_brokers,
        auto_offset_reset="earliest",
        group_id="convert-group",
        enable_auto_commit=True,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )

    logger.info("Kafka consumer started. Listening for messages...")

    while True:
        records = consumer.poll(timeout_ms=500)

        if not records:
            time.sleep(0.1) 
            continue

        for tp, messages in records.items():
            for msg in messages:
                try:
                    outer_msg = KafkaMessage(**msg.value)
                    logger.info(f"Received KafkaMessage: {outer_msg}")

                    task_data = json.loads(outer_msg.data)
                    task = ConvertTask(**task_data)

                    handle_convert_task(task, outer_msg.callback_url)

                except Exception as e:
                    logger.exception(f"Error processing Kafka message: {e}")