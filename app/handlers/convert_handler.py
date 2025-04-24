import os
import tempfile
import requests
import wave
import contextlib
import ffmpeg

from app.utils.logger import get_logger
from app.generated.messages_pb2 import MessageConvertTask, ErrorTaskResponse, ConvertTaskResponse, WrapperResponse
from app.kafka.producer import callback_producer
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
        
def download_convert_upload(task_id: str, file_url: str, tmpdir: str) -> tuple[str, float]:
    mp4_path = os.path.join(tmpdir, f"{task_id}.mp4")
    wav_path = os.path.join(tmpdir, f"{task_id}.wav")

    logger.info(f"[{task_id}] Downloading file from: {file_url}")
    response = requests.get(file_url)
    response.raise_for_status()
    with open(mp4_path, 'wb') as f:
        f.write(response.content)

    convert_mp4_to_wav(mp4_path, wav_path)

    duration = get_audio_duration(wav_path)
    logger.info(f"[{task_id}] Audio duration: {duration} seconds")

    s3_path = f"{task_id}.wav"
    s3_url = s3_client.upload_file(wav_path, s3_path)
    logger.info(f"[{task_id}] Uploaded to S3: {s3_url}")

    return s3_url, duration        

def process_convert_task(task_id: str, task: MessageConvertTask) -> None:
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            s3_url, duration = download_convert_upload(task_id, task.file_url, tmpdir)

            callback_data = WrapperResponse(
                task_id = task_id,
                convert = ConvertTaskResponse(
                    audio_len=duration,
                    converted_file_url=s3_url
                )
            )
            logger.info(f"[{task_id}] Sending callback to Kafka")
            callback_producer.send_callback(callback_data, key=task_id)

    except Exception as e:
        try:
            error_data = WrapperResponse(
                task_id = task_id,
                error = ErrorTaskResponse(error=str(e))
            )
            logger.info(f"[{task_id}] Sending error callback to Kafka")
            callback_producer.send_callback(error_data, key=task_id)
        except Exception as cb_err:
            logger.error(f"[{task_id}] Failed to send error callback: {cb_err}")
        logger.exception(f"[{task_id}] Error during diarize task: {e}")