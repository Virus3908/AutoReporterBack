from typing import List
from ollama import chat, ChatResponse
from app.utils.logger import get_logger
from app.config.settings import Settings
from app.kafka.producer import callback_producer
from app.generated.messages_pb2 import ReportTaskResponse, MessageReportTask, WrapperResponse, ErrorTaskResponse

logger = get_logger("report")

settings = Settings()

def request_to_llm(message: str, prompt: str) -> str:
    if not message:
        logger.error("No messages to send to LLM.")
        return ""
    if not prompt.strip():
        logger.error("Prompt is empty or whitespace.")
        return ""

    logger.info(f"Sending messages to LLM")
    logger.debug(f"Prompt: {prompt}")

    message_payload = [
        {'role': 'system', 'content': prompt},
        {'role': 'user', 'content': message}
    ]

    try:
        response: ChatResponse = chat(
            model=settings.ollama_model,
            messages=message_payload,
            options={'num_ctx': settings.ollama_num_context}
        )
        content = response.message.content.strip()
        logger.info(f"LLM response:\n{content}")
        return content

    except Exception as e:
        logger.exception(f"Error while querying LLM: {e}")
        return ""

def process_report_task(is_semi: bool, task_id: str, task: MessageReportTask) -> str:
    try:
        response = request_to_llm(task.message, task.prompt)
        if is_semi:
            callback_data = WrapperResponse(
                task_id=task_id,
                semi_report=ReportTaskResponse(text=response)
            )
        else:
            callback_data = WrapperResponse(
                task_id=task_id,
                report=ReportTaskResponse(text=response)
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
        
