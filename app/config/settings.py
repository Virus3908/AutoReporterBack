import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from app.utils.logger import get_logger

logger = get_logger("settings")


class Settings:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Settings, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        load_dotenv()

        env_config_path = os.getenv("BACKEND_CONFIG_PATH")
        config_path = env_config_path or "app/config/config.yaml"

        config_file = Path(config_path)
        if not config_file.exists():
            self._create_default_config(config_file)

        try:
            with open(config_path, "r") as f:
                raw_cfg = yaml.safe_load(f)
        except yaml.YAMLError as e:
            logger.error(f"Error parsing config.yaml: {e}")
            raise

        cfg = self._expand_env_vars(raw_cfg)

        kafka_cfg = cfg["kafka"]
        self.kafka_brokers = kafka_cfg["brokers"]
        self.kafka_group_id = kafka_cfg.get("group_id", "default-group")
        self.kafka_consumer_topic = kafka_cfg["consumer"]
        self.kafka_producer_topic = kafka_cfg["producer"]

        tokens_cfg = cfg["tokens"]
        self.hf_token = tokens_cfg["hf_token"]
        if not self.hf_token:
            logger.warning("Hugging Face token is not set!")

        ollama_cfg = cfg["ollama"]
        self.ollama_url = ollama_cfg["url"]
        self.ollama_model = ollama_cfg["model"]
        self.ollama_num_context = ollama_cfg["num_context"]

        s3_cfg = cfg["s3"]
        self.s3_access_key = s3_cfg["access_key"]
        self.s3_secret_key = s3_cfg["secret_key"]
        self.s3_endpoint = s3_cfg["endpoint_url"]
        self.s3_bucket = s3_cfg["bucket"]
        self.s3_public_base_url = s3_cfg["public_base_url"]
        self.s3_region = s3_cfg["region"]

    def _create_default_config(self, path: Path):
        default = {
            "kafka": {
                "brokers": ["localhost:9092"],
                "consumer": "task",
                "producer": "callback",
                "group_id": "${KAFKA_GROUP_ID}",
            },
            "server": {"host": "127.0.0.1", "port": 8000},
            "s3": {
                "access_key": "${AWS_ACCESS_KEY_ID}",
                "secret_key": "${AWS_SECRET_ACCESS_KEY}",
                "region": "${AWS_REGION}",
                "bucket": "${S3_BUCKET_NAME}",
                "endpoint_url": "${S3_ENDPOINT_URL}",
                "public_base_url": "${S3_PUBLIC_BASE_URL}",
            },
            "tokens": {"hf_token": "${HF_TOKEN}"},
            "ollama": {
                "url": "http://localhost:11434",
                "model": "llama2",
                "num_context": 2048,
            },
        }
        with open(path, "w") as f:
            yaml.dump(default, f)
        print(f"[INFO] Default config created at {path}. Please check values.")

    def _expand_env_vars(self, obj):
        if isinstance(obj, dict):
            return {k: self._expand_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._expand_env_vars(i) for i in obj]
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            env_var = obj[2:-1]
            return os.getenv(env_var, "")
        else:
            return obj


settings = Settings()
