from kafka import KafkaProducer
from google.protobuf.message import Message
from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger("KafkaProducer")

class CallbackProducer:
    def __init__(self):
        self.topic = settings.kafka_producer_topic
        logger.info(f"Producer will send messages to topic: {self.topic}")

        self.producer = KafkaProducer(
            bootstrap_servers=settings.kafka_brokers,
            value_serializer=lambda m: m.SerializeToString()
        )

    def send_callback(self, msg: Message, key: str = None):
        try:
            future = self.producer.send(
                topic=self.topic,
                key=key.encode() if key else None,
                value=msg
            )
            result = future.get(timeout=10)
            logger.info(f"Message sent to Kafka topic {self.topic}, offset: {result.offset}")
        except Exception as e:
            logger.exception(f"Failed to send message to Kafka: {e}")

    def close(self):
        self.producer.flush()
        self.producer.close()
  
callback_producer = CallbackProducer()