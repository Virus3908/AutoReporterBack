import torchaudio
import whisper
import torch
import os

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