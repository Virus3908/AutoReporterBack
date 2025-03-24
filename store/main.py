import os
import uvicorn
from fastapi import FastAPI, BackgroundTasks, Depends
from pydantic import BaseModel
from app.services.transcribe import *
from app.services.report import *
import uuid

from sqlalchemy import text
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

os.environ['CURL_CA_BUNDLE'] = ''

app = FastAPI()

Параметры
WAV_FILE = "audio.wav"
TRANSCRIPTION_PREFIX = "transcription_"
REPORT_PREFIX = "report_"
OUTPUT_EXT = ".txt"


results = {}


class FileProcessRequest(BaseModel):
    file_url: str

@app.put("/transcribe/")
async def start_trancribing(request: FileProcessRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    results[task_id] = "Queued"
    background_tasks.add_task(process_transcription, task_id, request.file_url)
    return {"task_id": task_id, "status_url": f"/status/{task_id}"}

@app.get("/status/{task_id}")
async def check_status(task_id: str):
    if task_id not in results:
        return {"error": "Unknown task"}
    return {"task_id": task_id, "status": results[task_id]}

def process_transcription(task_id: str, file_url: str):
    results[task_id] = "Converting to WAV"
    convert_mp4_to_wav(file_url, WAV_FILE)
    
    results[task_id] = "Diarizing audio"
    segments = diarize_audio(WAV_FILE)
    segments = filter_and_merge_segments(segments, 0.1)
    
    results[task_id] = "Transcription audio"
    transcripts = transcribe_segments(WAV_FILE, segments)
    
    results[task_id] = "Writing results"
    output_file = TRANSCRIPTION_PREFIX+str(task_id) + OUTPUT_EXT
    save_transcription(transcripts, output_file)
    results[task_id] = f"{output_file}"
    
@app.put("/report/")
async def start_reporting(request: FileProcessRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    results[task_id] = "Queued"
    background_tasks.add_task(process_report, task_id, request.file_url)
    return {"task_id": task_id, "status_url": f"/status/{task_id}"}

@app.get("/info")
async def info_response():
    return

def process_report(task_id: str, file_url: str):
    results[task_id] = "Calculating parts len"
    parts_len = calculate_parts_len(file_url)
    results[task_id] = "Splitting messages"
    message_to_llm = split_transcribe_to_messages(file_url, parts_len)
    results[task_id] = "Requesting to LLM"
    report = request_to_llm(message_to_llm)
    results[task_id] = "Writing results"
    output_file = REPORT_PREFIX + str(task_id) + OUTPUT_EXT
    write_to_output(output_file ,report)
    results[task_id] = f"{output_file}"

@app.post("/api/convert")
async def test_response(background_tasts: BackgroundTasks):
    return {"uuid": str(uuid.uuid4())}

@app.get("/ping")
async def resp():
    return {"host": "pong"}

