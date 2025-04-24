import os
import tempfile
import requests
import wave
import contextlib
import ffmpeg

from app.utils.logger import get_logger
from app.generated.messages_pb2 import MessageConvertTask, ErrorTaskResponse, ConvertTaskResponse
from kafka.consumer.fetcher import ConsumerRecord
from app.handlers.response import send_callback
from app.client.s3_client import s3_client

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

def handle_convert_task(msg: ConsumerRecord) -> None:
    try:
        task = MessageConvertTask()
        task.ParseFromString(msg.value)
        logger.info(f"Start convert-task for task_id={task.task_id}")
        process_convert_task(task)

    except Exception as e:
        logger.exception(f"Error during convert-task: {e}")
        
def download_convert_upload(task_id: str, file_url: str, tmpdir: str) -> tuple[str, float]:
    mp4_path = os.path.join(tmpdir, f"{task_id}.mp4")
    wav_path = os.path.join(tmpdir, f"{task_id}.wav")

    logger.info(f"Downloading file from: {file_url}")
    response = requests.get(file_url)
    response.raise_for_status()
    with open(mp4_path, 'wb') as f:
        f.write(response.content)

    convert_mp4_to_wav(mp4_path, wav_path)

    duration = get_audio_duration(wav_path)
    logger.info(f"Audio duration: {duration} seconds")

    s3_path = f"{task_id}.wav"
    s3_url = s3_client.upload_file(wav_path, s3_path)
    logger.info(f"Uploaded to S3: {s3_url}")

    return s3_url, duration        
        
def process_convert_task(task: MessageConvertTask) -> None:
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            s3_url, duration = download_convert_upload(task.task_id, task.file_url, tmpdir)

            callback_data = ConvertTaskResponse(
                audio_len=duration,
                converted_file_url=s3_url
            )

            full_callback_url = task.callback_url + task.callback_postfix + f"{task.task_id}"
            logger.info(f"Callback URL: {full_callback_url}")
            send_callback(full_callback_url, callback_data)

    except Exception as e:
        try:
            full_callback_url = task.callback_url + task.error_callback_postfix + f"{task.task_id}"
            callback_data = ErrorTaskResponse(error=str(e))
            send_callback(full_callback_url, callback_data)
        except Exception as cb_err:
            logger.error(f"Failed to send error callback: {cb_err}")
        logger.exception(f"Error during convert task: {e}")