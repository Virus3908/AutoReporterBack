import threading
import time

from kafka import KafkaConsumer
from kafka.structs import OffsetAndMetadata

from app.config.settings import settings
from app.generated.messages_pb2 import WrapperTask
from app.handlers.convert_handler import process_convert_task
from app.handlers.diarize_handler import process_diarize_task
from app.handlers.summarize_handler import process_report_task
from app.handlers.transcribe_handler import process_transcribe_task
from app.utils.logger import get_logger

logger = get_logger("KafkaConsumer")


def handle_wrapper_task(wrapper: WrapperTask):
    task_id = wrapper.task_id
    task_type = wrapper.WhichOneof("task")

    if task_type == "convert":
        process_convert_task(task_id, wrapper.convert)

    elif task_type == "diarize":
        process_diarize_task(task_id, wrapper.diarize)

    elif task_type == "transcription":
        process_transcribe_task(task_id, wrapper.transcription)

    elif task_type == "semi_report":
        process_report_task(True, task_id, wrapper.semi_report)

    elif task_type == "report":
        process_report_task(False, task_id, wrapper.report)

    else:
        logger.warning(f"Unsupported task type: {task_type}")


def start_main_consumer():
    topic = settings.kafka_consumer_topic
    logger.info(f"Starting main Kafka consumer for topic: {topic}")

    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=settings.kafka_brokers,
        auto_offset_reset="earliest",
        group_id=f"{settings.kafka_group_id}-{topic}",
        enable_auto_commit=False,
        value_deserializer=lambda m: m,
    )

    try:
        while True:
            records = consumer.poll(timeout_ms=500)
            if not records:
                time.sleep(0.1)
                continue

            for tp, messages in records.items():
                for msg in messages:
                    try:
                        wrapper = WrapperTask()
                        wrapper.ParseFromString(msg.value)
                        logger.info(
                            f"Received task of type: {wrapper.WhichOneof('task')} at offset {msg.offset}"
                        )
                        handle_wrapper_task(wrapper)
                        consumer.commit(
                            offsets={tp: OffsetAndMetadata(msg.offset + 1, None, -1)}
                        )

                    except Exception as e:
                        logger.exception(f"Failed to process message: {e}")

    except KeyboardInterrupt:
        logger.info("Kafka consumer interrupted by user")

    finally:
        consumer.close()
        logger.info("Kafka consumer closed")


def start_consumer():
    t = threading.Thread(target=start_main_consumer, daemon=True)
    t.start()
    logger.info("Kafka consumer thread started.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down consumer.")
