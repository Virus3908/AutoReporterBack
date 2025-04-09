from typing import List
from ollama import chat, ChatResponse
from app.utils.logger import get_logger
from app.config.settings import Settings

logger = get_logger("report")

settings = Settings()

def split_transcribe_to_messages(message: str, audio_len: float) -> List[str]:
    if audio_len <= 0:
        logger.error("Audio length is zero or negative.")
        return []
    if not message.strip():
        logger.error("Empty or whitespace-only message provided.")
        return []

    num_chunks = max(1, int(audio_len // 600))
    part_length = len(message) / num_chunks

    parts = []
    current = ""

    for line in message.splitlines():
        current += line + "\n"
        if len(current) >= part_length:
            parts.append(current.strip())
            current = ""

    if current.strip():
        parts.append(current.strip())

    logger.info(f"Transcription divided into {len(parts)} parts")
    return parts

def request_to_llm(messages_to_llm: List[str], prompt: str) -> str:
    if not messages_to_llm:
        logger.error("No messages to send to LLM.")
        return ""
    if not prompt.strip():
        logger.error("Prompt is empty or whitespace.")
        return ""

    logger.info(f"Sending {len(messages_to_llm)} messages to LLM")
    logger.debug(f"Prompt: {prompt}")

    final_response = []

    for index, msg in enumerate(messages_to_llm, start=1):
        message_payload = [
            {'role': 'system', 'content': prompt},
            {'role': 'user', 'content': msg}
        ]

        try:
            response: ChatResponse = chat(
                model=settings.ollama_model,
                messages=message_payload,
                options={'num_ctx': settings.ollama_num_context}
            )
            content = response.message.content.strip()
            logger.info(f"Part {index}] LLM response:\n{content}")
            final_response.append(content)

        except Exception as e:
            logger.exception(f"Error while querying LLM for part {index}: {e}")
            final_response.append(f"Generate error {index}]")

    return final_response

