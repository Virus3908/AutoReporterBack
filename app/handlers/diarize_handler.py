import os
import tempfile
import requests
import gc
import torch
from kafka.consumer.fetcher import ConsumerRecord

from pyannote.audio.pipelines import SpeakerDiarization
from app.config.settings import settings
from app.utils.logger import get_logger
from app.generated.messages_pb2 import MessageDiarizeTask, Segment, SegmentsTaskResponse, ErrorTaskResponse
from app.handlers.response import send_callback
from typing import List, Tuple 

logger = get_logger("diarize")

device = "cuda" if torch.cuda.is_available() else "cpu"

def diarize_audio(wav_file_path: str) -> Tuple[List[Tuple[int, float, float]], int]:
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

    if not segments:
        logger.warning("No valid segments found")
        return [], 0

    return filter_and_merge_segments(segments, min_duration=0.1), len(speaker_map)

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

def handle_diarize_task(msg: ConsumerRecord) -> None:

    try:
        task = MessageDiarizeTask()
        task.ParseFromString(msg.value)
        logger.info(f"Start diarize-task for task_id={task.task_id}")
        process_diarize_task(task)
        
    except Exception as e:
        logger.exception(f"Error during diarize task {task.task_id}: {e}")
        
def process_diarize_task(task: MessageDiarizeTask) -> None:
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = os.path.join(tmpdir, f"{task.task_id}.wav")

            logger.info(f"Downloading audio from: {task.converted_file_url}")
            response = requests.get(task.converted_file_url)
            response.raise_for_status()

            with open(wav_path, "wb") as f:
                f.write(response.content)

            logger.info("Starting diarization...")
            segments, num_of_speakers = diarize_audio(wav_path)

            callback_data = SegmentsTaskResponse(
                num_of_speakers=num_of_speakers,
                segments = [
                    Segment(speaker=speaker, start_time=start, end_time=end)
                    for speaker, start, end in segments
                ],
            )

            full_callback_url = task.callback_url + task.callback_postfix + f"{task.task_id}"
            send_callback(full_callback_url, callback_data)
    except Exception as e:
        full_callback_url = task.callback_url + task.error_callback_postfix + f"{task.task_id}"
        callback_data = ErrorTaskResponse(error=str(e))
        send_callback(full_callback_url, callback_data)
        logger.exception(f"Error during transcription task {task.task_id}: {e}")