import os
import tempfile
import requests
from pyannote.audio.pipelines import SpeakerDiarization
from app.config.settings import settings
from app.utils.logger import get_logger
from app.models.tasks import TaskWithFile
import gc
import torch

logger = get_logger("convert")

device = "cuda" if torch.cuda.is_available() else "cpu"

def diarize_audio(wav_file):
    pipeline = SpeakerDiarization.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=settings.hf_token)
    pipeline.to(torch.device(device))
    diarization = pipeline(wav_file)
    
    speaker_map = {}
    next_speaker_id = 0
    segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        if turn.end - turn.start < 0.2:
            continue 
        if speaker not in speaker_map:
            speaker_map[speaker] = next_speaker_id
            next_speaker_id += 1

        speaker_id = speaker_map[speaker]
        segments.append((speaker_id, turn.start, turn.end))
    
    logger.info(f"Diarize done: {len(set(s[0] for s in segments))} speakers")
    del pipeline, diarization
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        
    segments = filter_and_merge_segments(segments, 0.1)
    return segments

def filter_and_merge_segments(segments, min_duration=0.1):

    segments = sorted(segments, key=lambda x: x[1])

    filtered = []
    for (speaker, start, end) in segments:
        duration = end - start
        if duration >= min_duration:
            filtered.append((speaker, start, end))

    merged = []
    for seg in filtered:
        speaker, start, end = seg
        if not merged:
            merged.append(seg)
        else:
            last_speaker, last_start, _ = merged[-1]
            if speaker == last_speaker:
                merged[-1] = (last_speaker, last_start, end)
            else:
                merged.append(seg)

    return merged

def send_callback(callback_url: str, data: dict) -> requests.Response:
    logger.info(f"Отправка PATCH на {callback_url} с данными: {data}")
    response = requests.patch(callback_url, json=data)
    response.raise_for_status()
    return response

def handle_diarize_task(task: TaskWithFile, callback_url: str):
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = os.path.join(tmpdir, f"{task.task_id}.wav")

            logger.info(f"Скачиваем аудиофайл из {task.file_url}")
            r = requests.get(task.file_url)
            r.raise_for_status()

            with open(wav_path, "wb") as f:
                f.write(r.content)

            logger.info("Начинается диаризация...")
            segments = diarize_audio(wav_path)

            callback_data = {
                "segments": [
                    {"speaker": speaker, "start": start, "end": end}
                    for speaker, start, end in segments
                ]
            }

            full_callback_url = callback_url.rstrip("/") + task.callback_postfix.rstrip("/") + f"/{task.task_id}"
            send_callback(full_callback_url, callback_data)

            logger.info("Callback успешно отправлен")

    except Exception as e:
        logger.exception(f"Ошибка при обработке diarize-задачи: {e}")