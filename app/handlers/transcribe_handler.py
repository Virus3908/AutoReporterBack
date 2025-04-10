import os
import tempfile
import requests
import torchaudio
import whisper
import torch

from app.utils.logger import get_logger
from kafka.consumer.fetcher import ConsumerRecord
from app.generated.messages_pb2 import MessageTranscriptionTask, TranscriptionTaskResponse
from google.protobuf.json_format import MessageToDict

logger = get_logger("transcription")

device = "cuda" if torch.cuda.is_available() else "cpu"

def is_repeatable(text: str) -> bool:
    words = text.split()
    if not words:
        return False
    unique_ratio = len(set(words)) / len(words)
    return unique_ratio < 0.2

def transcribe_segment(wav_file: str, start: float, end: float, model) -> str:
    waveform, sample_rate = torchaudio.load(wav_file)

    start_sample = int(start * sample_rate)
    end_sample = int(end * sample_rate)
    segment_audio = waveform[:, start_sample:end_sample]

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        segment_path = temp_file.name
        torchaudio.save(segment_path, segment_audio, sample_rate)

    try:
        for cycle in range(3):
            result = model.transcribe(
                segment_path,
                language="ru",
                beam_size=10,
                temperature=cycle * 0.2,
            )
            text = result.get("text", "").strip()

            logger.debug(f"[Cycle {cycle}] Transcription: {text}")

            if (
                not text
                or (text and text.split()[0] != "Субтитры")
                or cycle >= 2
            ) and not is_repeatable(text):
                break

        if (cycle > 2 and len(text.split()) == 3) or text == "Продолжение следует...":
            text = ""
        return text

    finally:
        if os.path.exists(segment_path):
            os.remove(segment_path)

def send_callback(callback_url: str, data: dict) -> None:
    logger.info(f"PATCH to {callback_url} with data: {data}")
    try:
        response = requests.patch(callback_url, json=data)
        response.raise_for_status()
        logger.info(f"Callback successful: {response.status_code}")
    except requests.RequestException as e:
        logger.exception(f"Failed to send callback: {e}")
        raise

def handle_transcribe_task(msg: ConsumerRecord) -> None:
    try:
        task = MessageTranscriptionTask()
        task.ParseFromString(msg.value)
        logger.info(f"Start convert-task for task_id={task.task_id}")
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = os.path.join(tmpdir, f"{task.task_id}.wav")

            logger.info(f"Downloading file: {task.file_url}")
            r = requests.get(task.file_url)
            r.raise_for_status()

            with open(wav_path, "wb") as f:
                f.write(r.content)

            logger.info("Starting transcription...")
            model = whisper.load_model("turbo", device=device)
            transcription = transcribe_segment(wav_path, task.start_time, task.end_time, model)

            full_callback_url = task.callback_url + f"{task.task_id}"
            callback_data = TranscriptionTaskResponse(transcription=transcription)
            send_callback(full_callback_url, MessageToDict(callback_data))

    except Exception as e:
        logger.exception(f"Error during transcription task: {e}")