import os
import tempfile
import requests
import wave
import contextlib

import ffmpeg

from app.utils.logger import get_logger
from app.models.tasks import Task

logger = get_logger("convert")


def get_audio_duration(file_path: str) -> float:
    try:
        with contextlib.closing(wave.open(file_path, 'rb')) as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            duration = frames / float(rate)
            return round(duration, 2)
    except wave.Error as e:
        logger.error(f"Failed to read WAV file duration: {e}")
        return 0.0


def convert_mp4_to_wav(mp4_file: str, wav_file: str) -> None:
    try:
        (
            ffmpeg
            .input(mp4_file)
            .filter("anlmdn")
            .filter("silenceremove")
            .output(wav_file, format='wav', acodec='pcm_s16le', ac=1, ar='16k')
            .run(quiet=True, overwrite_output=True)
        )
        logger.info(f"Converted: {mp4_file} → {wav_file}")
    except ffmpeg.Error as e:
        logger.exception(f"FFmpeg conversion failed: {e.stderr.decode() if e.stderr else e}")
        raise


def send_callback(callback_url: str, file_path: str, audio_len: float) -> requests.Response:
    with open(file_path, 'rb') as f:
        files = {
            'file': ('audio.wav', f, 'audio/wav'),
            'audio_len': (None, str(audio_len))
        }

        logger.info(f"Sending callback to {callback_url}...")
        response = requests.patch(callback_url, files=files)
        response.raise_for_status()
        return response


def handle_convert_task(task: Task, callback_url: str):
    logger.info(f"Start convert-task for task_id={task.task_id}")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            mp4_path = os.path.join(tmpdir, f"{task.task_id}.mp4")
            wav_path = os.path.join(tmpdir, f"{task.task_id}.wav")

            logger.info(f"Downloading file from: {task.file_url}")
            response = requests.get(task.file_url)
            response.raise_for_status()
            with open(mp4_path, 'wb') as f:
                f.write(response.content)

            convert_mp4_to_wav(mp4_path, wav_path)

            duration = get_audio_duration(wav_path)
            logger.info(f"Audio duration: {duration} seconds")

            full_callback_url = callback_url.rstrip("/") + task.callback_postfix.rstrip("/") + f"/{task.task_id}"
            logger.info(f"Callback URL: {full_callback_url}")

            send_callback(full_callback_url, wav_path, duration)
            logger.info("Callback sent successfully")

    except Exception as e:
        logger.exception(f"Error during convert-task (task_id={task.task_id}): {e}")