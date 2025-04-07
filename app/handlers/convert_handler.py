import os
import tempfile
import requests

import ffmpeg
from app.utils.logger import get_logger
import wave
import contextlib
from app.models.tasks import Task

logger = get_logger("convert")

def get_audio_duration(file_path: str) -> float:
    with contextlib.closing(wave.open(file_path, 'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        return frames / float(rate)

def convert_mp4_to_wav(mp4_file, wav_file):
    (
        ffmpeg
        .input(mp4_file)
        .filter("anlmdn")
        .filter("silenceremove")
        .output(wav_file, format='wav', acodec='pcm_s16le', ac=1, ar='16k')
        .run(overwrite_output=True)
    )
    logger.info(f"[+] Конвертировано: {mp4_file} → {wav_file}")
    
    
def send_callback(callback_url: str, file_path: str, audio_len: float):
    with open(file_path, 'rb') as f:
        files = {
            'file': ('audio.wav', f, 'audio/wav'),
            'audio_len': (None, str(audio_len))
        }

        response = requests.patch(callback_url, files=files)
        response.raise_for_status()
        return response


def handle_convert_task(task: Task, callback_url: str):
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            mp4_path = os.path.join(tmpdir, f"{task.task_id}.mp4")
            wav_path = os.path.join(tmpdir, f"{task.task_id}.wav")

            logger.info(f"Download file fron {task.file_url}")
            r = requests.get(task.file_url)
            r.raise_for_status()

            with open(mp4_path, 'wb') as f:
                f.write(r.content)

            convert_mp4_to_wav(mp4_path, wav_path)

            duration = get_audio_duration(wav_path)
            logger.info(f"Audio len: {duration:.2f} s")

            full_callback_url = callback_url.rstrip("/") + task.callback_postfix + str(task.task_id)
            logger.info(f"Callback to {full_callback_url}")

            send_callback(full_callback_url, wav_path, duration)

            logger.info("Callback success")

    except Exception as e:
        logger.exception(f"Error during convert-task: {e}")