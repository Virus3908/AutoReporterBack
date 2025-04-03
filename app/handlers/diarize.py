from pyannote.audio.pipelines import SpeakerDiarization
from app.config.settings import settings
from app.utils.logger import logger
import gc
import torch

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
