import gc
import os
import tempfile
from typing import List, Tuple

import requests
import torch
from pyannote.audio.pipelines import SpeakerDiarization

from app.config.settings import settings
from app.generated.messages_pb2 import (DiarizeTaskResponse, ErrorTaskResponse,
                                        MessageDiarizeTask, Segment,
                                        WrapperResponse)
from app.kafka.producer import callback_producer
from app.utils.logger import get_logger

logger = get_logger("diarize")

device = "cuda" if torch.cuda.is_available() else "cpu"


def diarize_audio(wav_file_path: str) -> Tuple[List[Tuple[int, float, float]], int]:
    logger.info(f"Running diarization on file: {wav_file_path}")

    pipeline = SpeakerDiarization.from_pretrained(
        "pyannote/speaker-diarization-3.1", use_auth_token=settings.hf_token
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

    del pipeline, diarization
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    if not segments:
        logger.warning("No valid segments found")
        return [], 0

    return filter_and_merge_segments(segments, min_duration=0.1), len(speaker_map)


def filter_and_merge_segments(
    segments: list[tuple[int, float, float]], min_duration: float = 0.1
) -> list[tuple[int, float, float]]:
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


def process_diarize_task(task_id: str, task: MessageDiarizeTask) -> None:
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = os.path.join(tmpdir, f"{task_id}.wav")

            logger.info(
                f"[{task_id}] Downloading audio from: {task.converted_file_url}"
            )
            response = requests.get(task.converted_file_url)
            response.raise_for_status()

            with open(wav_path, "wb") as f:
                f.write(response.content)

            logger.info(f"[{task_id}] Starting diarization...")
            segments, num_of_speakers = diarize_audio(wav_path)

            callback_data = WrapperResponse(
                task_id=task_id,
                diarize=DiarizeTaskResponse(
                    num_of_speakers=num_of_speakers,
                    segments=[
                        Segment(speaker=s, start_time=st, end_time=et)
                        for s, st, et in segments
                    ],
                ),
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
