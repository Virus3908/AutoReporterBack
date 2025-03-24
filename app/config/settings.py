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

        db_cfg = cfg["database"]
        self.db_host = db_cfg["host"]
        self.db_port = db_cfg["port"]
        self.db_name = db_cfg["dbname"]
        self.db_user = db_cfg["user"]
        self.db_password = db_cfg["password"]

        s3_cfg = cfg["s3"]
        self.s3_endpoint = s3_cfg["endpoint"]
        self.s3_bucket = s3_cfg["bucket"]
        self.s3_access_key = s3_cfg["access_key"]
        self.s3_secret_key = s3_cfg["secret_key"]

        tokens_cfg =  cfg["tokens"]
        self.hf_token = tokens_cfg["hf_token"]

    def _create_default_config(self, path: Path):
        default = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "user": "${DB_USER}",
                "password": "${DB_PASSWORD}",
                "dbname": "mydb"
            },
            "s3": {
                "endpoint": "http://localhost:9000",
                "bucket": "bucket",
                "access_key": "${S3_ACCESS_KEY}",
                "secret_key": "${S3_SECRET_KEY}"
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

    def get_db_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

settings = Settings()