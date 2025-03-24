import os
import gc
import ffmpeg
import whisper
from pyannote.audio.pipelines import SpeakerDiarization
from pyannote.core import Segment
import torchaudio
import torch
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
MODEL_PATH_WISPER = "whisper"
device = "cuda" if torch.cuda.is_available() else "cpu"
prompt = "планеркаР"

# === Шаг 1: Конвертация MP4 в WAV ===
def convert_mp4_to_wav(mp4_file, wav_file):
    """Конвертирует mp4 в wav с частотой 16kHz, mono (одноканальный звук)."""
    (
        ffmpeg
        .input(mp4_file)
        .filter("anlmdn")
        .filter("silenceremove")
        .output(wav_file, format='wav', acodec='pcm_s16le', ac=1, ar='16k')
        .run(overwrite_output=True)
    )
    print(f"[+] Конвертировано: {mp4_file} → {wav_file}")

# === Шаг 2: Диаризация ===
def diarize_audio(wav_file):
    """Определяет говорящих и возвращает список сегментов (speaker, start, end)."""
    pipeline = SpeakerDiarization.from_pretrained("pyannote/speaker-diarization-3.1",cache_dir="D:/trans/my_cache" , use_auth_token=HF_TOKEN)
    pipeline.to(torch.device(device))
    diarization = pipeline(wav_file)
    segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        if turn.end - turn.start < 0.2:
            continue 
        segments.append((speaker, turn.start, turn.end))
    
    print(f"[+] Диаризация завершена: найдено {len(set(s[0] for s in segments))} говорящих")
    del pipeline, diarization
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return segments

def filter_and_merge_segments(segments, min_duration=0.1):

    # Сортируем по времени начала
    segments = sorted(segments, key=lambda x: x[1])

    # 1) Убираем слишком короткие
    filtered = []
    for (speaker, start, end) in segments:
        duration = end - start
        if duration >= min_duration:
            filtered.append((speaker, start, end))

    # 2) Склеиваем смежные сегменты одного спикера
    merged = []
    for seg in filtered:
        speaker, start, end = seg
        if not merged:
            merged.append(seg)
        else:
            last_speaker, last_start, last_end = merged[-1]
            # Проверяем, если тот же спикер и пауза между сегментами <= merge_gap
            if speaker == last_speaker:
                # "Склеиваем" сегменты: расширяем предыдущий до нового end
                merged[-1] = (last_speaker, last_start, end)
            else:
                merged.append(seg)

    return merged

# === Шаг 3: Вырезка сегментов и транскрипция Whisper ===
def transcribe_segment(wav_file, start, end):
    """Разбивает аудиофайл по диаризации и транскрибирует с Whisper (русский язык)."""
    whisper_model = whisper.load_model("turbo", download_root=MODEL_PATH_WISPER, device=device)  # Можно "small" или "large"
    waveform, sample_rate = torchaudio.load(wav_file)

    # Вырезаем сегмент
    start_sample = int(start * sample_rate)
    end_sample = int(end * sample_rate)
    segment_audio = waveform[:, start_sample:end_sample]

    # Сохраняем временный файл
    segment_file = f"segment_{start:.2f}_{end:.2f}.wav"
    torchaudio.save(segment_file, segment_audio, sample_rate)

    cycle_count = 0
    # Распознаем текст
    while True:
        text = whisper_model.transcribe(segment_file, 
                                        language="ru",
                                        beam_size= 10,
                                        temperature= cycle_count * 2/10,
                                        initial_prompt= prompt)["text"]
        
        # Проверяем, не артефакт ли транскрибции, если нет, го дальше
        if ((len(text) == 0 or (len(text) > 0 and text.split()[0] != "Субтитры") or cycle_count > 2) and not is_repeatable(text)):
            break
        print(text, cycle_count)
        cycle_count+= 1
    # Проверка, мы получили артефакт, или Продолжение следует, тогда меняем на пустую строку.
    if (cycle_count > 2 and len(text.split()) == 3) or text == "Продолжение следует...":
        text = ""
    # Удаляем временный файл
    os.remove(segment_file)

    print("[+] Транскрипция завершена")
    os.remove(wav_file)
    return text

def is_repeatable(text):
    slised = text.split()
    set_slised = set(slised)
    if len(slised) > 0 and len(set_slised)/len(slised) < 0.2:
        return True
    return False

# === Шаг 4: Сохранение результата ===
def save_transcription(transcripts, output_txt):
    """Сохраняет результат в файл."""
    with open(output_txt, "w", encoding="utf-8") as f:
        for (start, end, speaker, text) in transcripts:
            f.write(f"[{start:.1f} - {end:.1f}]\t{speaker}:\t{text}\n")


    print(f"[+] Транскрипция сохранена в {output_txt}")
