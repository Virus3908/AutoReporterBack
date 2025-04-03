import ffmpeg
from app.utils.logger import get_logger
import wave
import contextlib

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
    
    
def handle_convert_task(task, callback_url):
    print(f"Would process task: {task}, callback: {callback_url}")