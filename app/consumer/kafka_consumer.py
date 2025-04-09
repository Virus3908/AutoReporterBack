import json
import time
from kafka import KafkaConsumer
from app.config.settings import settings
from app.models.kafka_message import KafkaMessage
from app.models.tasks import Task, TaskType
from app.handlers.convert_handler import handle_convert_task
from app.handlers.diarize_handler import handle_diarize_task
from app.handlers.transcribe_handler import handle_transcribe_task
from app.utils.logger import get_logger

logger = get_logger("KafkaConsumer")


def start_consumer():
    logger.info("Starting Kafka consumer")

    consumer = KafkaConsumer(
        settings.kafka_topic,
        bootstrap_servers=settings.kafka_brokers,
        auto_offset_reset="earliest",
        group_id=settings.kafka_group_id,
        enable_auto_commit=True,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )

    logger.info("Kafka consumer is running and waiting for messages")

    try:
        while True:
            records = consumer.poll(timeout_ms=500)

            if not records:
                time.sleep(0.1)
                continue

            for tp, messages in records.items():
                for msg in messages:
                    try:
                        outer_msg = KafkaMessage(**msg.value)
                        logger.info(f"Received message: {outer_msg.task_type} (Task ID: {outer_msg.task_id})")

                        task_data = json.loads(outer_msg.data)
                        handle_task(outer_msg, task_data)

                    except Exception as e:
                        logger.exception(f"Failed to process Kafka message: {e}")

    except KeyboardInterrupt:
        logger.info("Kafka consumer interrupted by user")
    except Exception as e:
        logger.exception(f"Unexpected error in consumer: {e}")
    finally:
        consumer.close()
        logger.info("Kafka consumer has stopped")


def handle_task(outer_msg: KafkaMessage, task_data: dict):
    task = Task(**task_data)

    if outer_msg.task_type == TaskType.CONVERT.value:
        handle_convert_task(task, outer_msg.callback_url)

    elif outer_msg.task_type == TaskType.DIARIZE.value:
        handle_diarize_task(task, outer_msg.callback_url)

    elif outer_msg.task_type == TaskType.TRANSCRIBE.value:
        handle_transcribe_task(task, outer_msg.callback_url)

    else:
        logger.warning(f"Unsupported task type received: {outer_msg.task_type}")