# 🧠 AI-Report Backend

Проект для обработки мультимедийных данных с использованием Kafka, S3, и LLM (через Ollama).

## ⚙️ Состав

- **Kafka Consumer**: читает задачи из топика (`task`)
- **Kafka Producer**: отправляет результаты в `callback`-топик
- **S3**: хранение и загрузка файлов
- **Ollama**: генерация отчётов с использованием LLM
- **Hugging Face**: (опционально) для внешних моделей
- **ProtoBuf**: для сериализации сообщений

---

## 🚀 Быстрый старт

1. **Создай виртуальное окружение**:

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

2.	Установи зависимости:

```
pip install -r requirements.txt
```

3.	Настрой переменные окружения:

Создай .env файл или установи переменные среды:

```
KAFKA_GROUP_ID=python-consumer
KAFKA_BROKER_1 = localhost:9092

HF_TOKEN=token
OLLAMA_URL=0.0.0.0:11434
OLLAMA_MODEL=llama3.3
OLLAMA_NUM_CONTEXT=2048

AWS_ACCESS_KEY_ID = log
AWS_SECRET_ACCESS_KEY = pass
S3_ENDPOINT_URL = http://localhost:9000
S3_BUCKET_NAME = bicket
S3_PUBLIC_BASE_URL= localhost:9000
AWS_REGION = ru-1
```
4.	Сконфигурируй YAML (опционально):

Файл app/config/config.yaml будет сгенерирован автоматически при первом запуске, если не найден.
5.	Запусти проект:

```
make run
```

⸻

🧪 Дополнительно

Проверка кода:

```
make lint     # Проверка по flake8
make format   # Форматирование через black + isort
```

⸻

🛠️ Структура проекта
```
app/
├── client/           # Работа с S3
├── config/           # Загрузка конфигураций
├── generated/        # gRPC / protobuf файлы
├── handlers/         # Обработчики задач (convert, diarize, ...)
├── kafka/            # Kafka consumer / producer
├── utils/            # Логгер, запуск
└── main.py           # Точка входа
```

⸻

📌 Примечания<br />
	•	Kafka offset коммитится только после успешной обработки.<br />
	•	Используется protobuf для сериализации задач.<br />
	•	Генерация .proto файлов:<br />

```
make generate
```

⸻

📄 Лицензия

MIT