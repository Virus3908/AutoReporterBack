import requests
from app.utils.logger import get_logger

logger = get_logger("response")

def send_callback(callback_url: str, data: dict) -> None:
    logger.info(f"PATCH to {callback_url} with data: {data}")
    try:
        payload = data.SerializeToString()
        response = requests.patch(
            callback_url, 
            data=payload,
            headers={"Content-Type": "application/octet-stream"}
        )
        response.raise_for_status()
        logger.info(f"Callback successful: {response.status_code}")
    except requests.RequestException as e:
        logger.exception(f"Failed to send callback: {e}")
        raise


# def send_callback_with_file(callback_url: str, file_path: str, audio_len: float) -> requests.Response:
#     logger.info(f"PATCH to {callback_url} with file: {file_path} and audio_len: {audio_len}")
#     try: 
#         with open(file_path, 'rb') as f:
#             files = {
#                 'file': ('audio.wav', f, 'audio/wav'),
#                 'audio_len': (None, str(audio_len))
#             }

#             logger.info(f"Sending callback to {callback_url}...")
#             response = requests.patch(callback_url, files=files)
#             response.raise_for_status()
#             logger.info(f"Callback successful: {response.status_code}")
#     except requests.RequestException as e:
#         logger.exception(f"Failed to send callback: {e}")
#         raise