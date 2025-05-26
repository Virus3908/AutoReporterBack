import os
import tempfile

import requests
import torch
import torchaudio
import whisper

from app.generated.messages_pb2 import (ErrorTaskResponse,
                                        MessageTranscriptionTask,
                                        TranscriptionTaskResponse,
                                        WrapperResponse)
from app.kafka.producer import callback_producer
from app.utils.logger import get_logger

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
                not text or (text and text.split()[0] != "Субтитры") or cycle >= 2
            ) and not is_repeatable(text):
                break

        if (cycle > 2 and len(text.split()) == 3) or text == "Продолжение следует...":
            text = ""
        return text

    finally:
        if os.path.exists(segment_path):
            os.remove(segment_path)


def process_transcribe_task(task_id: str, task: MessageTranscriptionTask) -> None:
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = os.path.join(tmpdir, f"{task_id}.wav")

            logger.info(f"[{task_id}] Downloading file: {task.file_url}")
            r = requests.get(task.file_url)
            r.raise_for_status()

            with open(wav_path, "wb") as f:
                f.write(r.content)

            logger.info(f"[{task_id}] Starting transcription...")
            model = whisper.load_model("turbo", device=device)
            transcription = transcribe_segment(
                wav_path, task.start_time, task.end_time, model
            )

            callback_data = WrapperResponse(
                task_id=task_id,
                transcription=TranscriptionTaskResponse(transcription=transcription),
            )
            callback_producer.send_callback(callback_data, key=task_id)
    except Exception as e:
        try:
            error_data = WrapperResponse(
                task_id=task_id, error=ErrorTaskResponse(error=str(e))
            )
            logger.info(f"[{task_id}] Sending error callback to Kafka")
            callback_producer.send_callback(error_data, key=task_id)
        except Exception as cb_err:
            logger.error(f"[{task_id}] Failed to send error callback: {cb_err}")
        logger.exception(f"[{task_id}] Error during diarize task: {e}")
