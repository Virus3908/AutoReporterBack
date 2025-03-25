from app.services.convert import convert_mp4_to_wav, get_audio_duration
from app.core.db_transaction import transaction
from app.models.task_models import Convert, Diarize, Task, Transcribe
from app.core.logger import logger
from sqlalchemy import select, update
from app.core.database import AsyncSessionLocal
from app.core.s3_client import s3_client
from app.services.diarize import diarize_audio
from app.services.transcribe import transcribe_segment
import asyncio
import aiohttp
import os
import uuid

async def download_file(url: str, save_path: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                with open(save_path, "wb") as f:
                    f.write(await resp.read())
            else:
                raise Exception(f"Failed to download file from {url}, status: {resp.status}")

async def handle_convert(task: Task, db):
    result = await db.execute(
        select(Convert).where(Convert.task_id == task.id)
    )
    convert = result.scalar_one()

    input_path = f"/tmp/{uuid.uuid4()}.mp4"
    output_path = f"/tmp/{uuid.uuid4()}.wav"

    try:
        await download_file(convert.file_url, input_path)
        convert_mp4_to_wav(input_path, output_path)
        audio_len = get_audio_duration(output_path)
        output_url = s3_client.upload_file(output_path, 'uploads/'+str(task.id)+'.wav')
        
        response_data = {
            "file_url": output_url,
            "audio_len": audio_len
        }
        
        async with transaction(db):
            await db.execute(
                update(Convert)
                .where(Convert.task_id == task.id)
                .values(converted_file_url=output_url, audio_len=audio_len)
                )
        async with aiohttp.ClientSession() as session:
            await session.put(
                task.callback_url + '/api/update/convert/' + str(task.id),
                json=response_data
            )
        logger.info(f"Convert complete for task {task.id}")
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)

async def handle_diarize(task: Task, db):
    result = await db.execute(
        select(Diarize).where(Diarize.task_id == task.id)
    )
    
    diarize = result.scalar_one()
    tmp_path = f"/tmp/{uuid.uuid4()}.wav"

    try:
        await download_file(diarize.file_url, tmp_path)
        segments = diarize_audio(tmp_path)
        
        response_data = {
            "segments": [
                {
                    "start_time": round(start, 3),
                    "end_time": round(end, 3),
                    "speaker": int(speaker)
                }
                for speaker, start, end in segments
            ]
        }
                
        async with transaction(db):
            await db.execute(
                update(Diarize)
                .where(Diarize.task_id == task.id)
                .values(segments=str(segments))
                )
        
        async with aiohttp.ClientSession() as session:
            await session.post(
                task.callback_url + '/api/update/diarize/' + str(task.id),
                json=response_data
            )
        
        logger.info(f"Diarize complete for task {task.id}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    

async def handle_transcribe(task: Task, db):
    result = await db.execute(
        select(Transcribe).where(Transcribe.task_id == task.id)
    )
    
    transcribe = result.scalar_one()
    tmp_path = f"/tmp/{uuid.uuid4()}.wav"

    try:
        await download_file(transcribe.file_url, tmp_path)
        transcription = transcribe_segment(tmp_path, transcribe.start_time, transcribe.end_time)
        
        response_data = {
            "message": transcription
        }
        
        async with transaction(db):
            await db.execute(
                update(Transcribe)
                .where(Transcribe.task_id == task.id)
                .values(transcription=transcription)
                )
        async with aiohttp.ClientSession() as session:
            await session.put(
                task.callback_url + '/api/update/transctibe/' + str(task.id),
                json=response_data
            )
        
        logger.info(f"Transcription complete for task {task.id}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        

async def process_task(task: Task, db):
    logger.info(f"Processing task {task.id} of type {task.type}")
    try:
        if task.type == 1:
            await handle_convert(task, db)
        elif task.type == 2:
            await handle_diarize(task, db)
        elif task.type == 3:
            await handle_transcribe(task, db)
        else:
            logger.warning(f"Unknown task type: {task.type}")
            return
        
        async with transaction(db):
            await db.execute(
                update(Task)
                .where(Task.id == task.id)
                .values(status=2)
            )

    except Exception as e:
        logger.error(f"Error while processing task {task.id}: {e}")
        async with transaction(db):
            await db.execute(
                update(Task)
                .where(Task.id == task.id)
                .values(status=3)
            )

async def task_worker():
    logger.info("Background task worker started")
    while True:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Task).where(Task.status == 1).order_by(Task.created_at.asc()).limit(1)
            )
            task = result.scalar_one_or_none()
            if task:
                await process_task(task, db)
                continue

            result = await db.execute(
                select(Task).where(Task.status == 0).order_by(Task.created_at.asc()).limit(1)
            )
            task = result.scalar_one_or_none()
            if task:
                async with transaction(db):
                    await db.execute(
                        update(Task)
                        .where(Task.id == task.id)
                        .values(status=1)
                    )
                await process_task(task, db)
            else:
                await asyncio.sleep(10)