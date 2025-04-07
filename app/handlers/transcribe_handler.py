import torchaudio
import whisper
import torch
import os
import tempfile
import requests
from app.utils.logger import get_logger
from app.models.tasks import Task

logger = get_logger("convert")

device = "cuda" if torch.cuda.is_available() else "cpu"

def transcribe_segment(wav_file, start, end):
    whisper_model = whisper.load_model("turbo", device=device)
    waveform, sample_rate = torchaudio.load(wav_file)

    start_sample = int(start * sample_rate)
    end_sample = int(end * sample_rate)
    segment_audio = waveform[:, start_sample:end_sample]

    segment_file = f"/tmp/segment_{start:.2f}_{end:.2f}.wav"
    torchaudio.save(segment_file, segment_audio, sample_rate)

    cycle_count = 0
    while True:
        text = whisper_model.transcribe(segment_file, 
                                        language="ru",
                                        beam_size= 10,
                                        temperature= cycle_count * 2/10,)["text"]
        
        if ((len(text) == 0 or (len(text) > 0 and text.split()[0] != "Субтитры") or cycle_count > 2) and not is_repeatable(text)):
            break
        print(text, cycle_count)
        cycle_count+= 1
    if (cycle_count > 2 and len(text.split()) == 3) or text == "Продолжение следует...":
        text = ""
    os.remove(segment_file)
    return text

def is_repeatable(text):
    slised = text.split()
    set_slised = set(slised)
    if len(slised) > 0 and len(set_slised)/len(slised) < 0.2:
        return True
    return False

def send_callback(callback_url: str, data: dict) -> requests.Response:
    logger.info(f"Отправка PATCH на {callback_url} с данными: {data}")
    response = requests.patch(callback_url, json=data)
    response.raise_for_status()
    return response

def handle_transcribe_task(task: Task, callback_url: str):
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = os.path.join(tmpdir, f"{task.task_id}.wav")

            logger.info(f"Скачиваем аудиофайл из {task.file_url}")
            r = requests.get(task.file_url)
            r.raise_for_status()

            with open(wav_path, "wb") as f:
                f.write(r.content)

            logger.info("Начинается транскрибация...")
            transctiption = transcribe_segment(wav_path, task.start_time, task.end_time)
            callback_data = {
                "text": transctiption
            }

            full_callback_url = callback_url.rstrip("/") + task.callback_postfix.rstrip("/") + f"/{task.task_id}"
            send_callback(full_callback_url, callback_data)

            logger.info("Callback успешно отправлен")

    except Exception as e:
        logger.exception(f"Ошибка при обработке diarize-задачи: {e}")