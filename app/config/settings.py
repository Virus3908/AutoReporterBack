import os
import yaml
from dotenv import load_dotenv
from pathlib import Path

class Settings:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Settings, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        load_dotenv()

        env_config_path = os.getenv("BACKEND_CONFIG_PATH")
        config_path = env_config_path or "app/config/config.yaml"

        config_file = Path(config_path)
        if not config_file.exists():
            self._create_default_config(config_file)

        with open(config_path, "r") as f:
            raw_cfg = yaml.safe_load(f)

        cfg = self._expand_env_vars(raw_cfg)

        kafka_cfg = cfg["kafka"]
        self.kafka_brokers = kafka_cfg["brokers"]
        self.kafka_topic = kafka_cfg["topic"]
        self.kafka_group_id = kafka_cfg.get("group_id", "default-group")

        tokens_cfg = cfg["tokens"]
        self.hf_token = tokens_cfg["hf_token"]

    def _create_default_config(self, path: Path):
        default = {
            "kafka": {
                "brokers": ["localhost:9092"],
                "topic": "tasks",
                "group_id": "${KAFKA_GROUP_ID}"
            },
            "server": {
                "host": "127.0.0.1",
                "port": 8000
            },
            "tokens": {
                "hf_token": "${HF_TOKEN}"
            }
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