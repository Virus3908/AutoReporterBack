import os
import tempfile
import requests
import gc
import torch

from pyannote.audio.pipelines import SpeakerDiarization
from app.config.settings import settings
from app.utils.logger import get_logger
from app.models.tasks import Task

logger = get_logger("diarize")

device = "cuda" if torch.cuda.is_available() else "cpu"

def diarize_audio(wav_file_path: str) -> list[tuple[int, float, float]]:
    logger.info(f"Running diarization on file: {wav_file_path}")

    pipeline = SpeakerDiarization.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=settings.hf_token
    )
    pipeline.to(torch.device(device))

    diarization = pipeline(wav_file_path)

    speaker_map = {}
    next_speaker_id = 0
    segments = []

    for turn, _, speaker in diarization.itertracks(yield_label=True):
        duration = turn.end - turn.start
        if duration < 0.2:
            continue

        if speaker not in speaker_map:
            speaker_map[speaker] = next_speaker_id
            next_speaker_id += 1

        segments.append((speaker_map[speaker], turn.start, turn.end))

    logger.info(f"Diarization complete. Speakers: {len(speaker_map)}")

    # Cleanup to free memory
    del pipeline, diarization
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return filter_and_merge_segments(segments, min_duration=0.1)

def filter_and_merge_segments(segments: list[tuple[int, float, float]], min_duration: float = 0.1) -> list[tuple[int, float, float]]:
    if not segments:
        logger.warning("No segments to process after diarization.")
        return []

    segments.sort(key=lambda x: x[1])
    merged = []

    for seg in segments:
        speaker, start, end = seg
        duration = end - start
        if duration < min_duration:
            continue

        if merged and speaker == merged[-1][0]:
            last_speaker, last_start, _ = merged[-1]
            merged[-1] = (last_speaker, last_start, end)
        else:
            merged.append(seg)

    return merged

def send_callback(callback_url: str, data: dict) -> requests.Response:
    logger.info(f"Sending PATCH callback to {callback_url} with data: {data}")
    response = requests.patch(callback_url, json=data)
    response.raise_for_status()
    return response

def handle_diarize_task(task: Task, callback_url: str):
    logger.info(f"Processing diarize task: {task.task_id}")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = os.path.join(tmpdir, f"{task.task_id}.wav")

            logger.info(f"Downloading audio from: {task.file_url}")
            response = requests.get(task.file_url)
            response.raise_for_status()

            with open(wav_path, "wb") as f:
                f.write(response.content)

            logger.info("Starting diarization...")
            segments = diarize_audio(wav_path)

            callback_data = {
                "segments": [
                    {"speaker": speaker, "start": round(start, 3), "end": round(end, 3)}
                    for speaker, start, end in segments
                ]
            }

            full_callback_url = callback_url.rstrip("/") + task.callback_postfix.rstrip("/") + f"/{task.task_id}"
            send_callback(full_callback_url, callback_data)

            logger.info("Callback sent successfully.")

    except Exception as e:
        logger.exception(f"Error during diarize task {task.task_id}: {e}")