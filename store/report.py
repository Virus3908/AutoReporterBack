from ollama import ChatResponse
from ollama import chat
import os
import re

os.environ['CURL_CA_BUNDLE'] = ''
CONTEXT_LEN = 10000
MODEL = 'llama3.3:70b'#'mistral-large'
PROMT_REPORT = \
"""
**ЗАДАЧА:**  
Проанализируй текст совещания и **выдели основные моменты** в следующей структуре.
### **1. Сводка обсуждённых вопросов**  
Краткое изложение главных тем и ключевых моментов дискуссии.  
### **2. Ключевые идеи и решения**  
-Перечисли основные тезисы и принятые решения.  
-Если обсуждались **альтернативные варианты** – **перечисли их**.  
### **3. Перечень приказов и поручений**  
**Внимание!** Все распоряжения записывай **в отдельный список**, строго в формате:  
**[Кто] – [Что сделать] – [Срок (если есть)]**  
**‼️ ОБЯЗАТЕЛЬНО:**
- **Особое внимание к приказам** – ВСЕГДА выделяй их
- **Обращай внимание на слова:** **"Сделай", "Рассмотрите", "Укажите", "Направьте", "Штаб"** – они указывают на приказы и поручения.   
---
**ФОРМАТ ОТВЕТА:**  
Ответ должен быть **чётко структурированным**, в **коротких списках**.  
**ВАЖНО:**  
- **Не пропускай приказы
"""

def calculate_parts_len(text_file):
  char_count = 0
  parts_count = 1
  with open(text_file, "r", encoding="utf-8") as f:
    content = f.read()
    last_line = content.strip().split('\n')[-1]
    match  = re.search(r"\[\d+\.+\d+\s*-\s*(\d+\.\d+)\]", last_line)
    if match:
      end_time = float(match.group(1))/600
      parts_count = max(round(end_time), 1)
    else:
      print("Can't find end_time")  
    cleaned_content = re.sub(r"\[.*?\]\s*", "", content)
    char_count = len(cleaned_content)
  return char_count / parts_count


def split_transcribe_to_messages(text_file, parts_len):
  result = []       
  with open(text_file, "r", encoding="utf-8") as f:
    part = ""
    i = 0
    for line in f.readlines():
      cleaned_line = re.sub(r"\[.*?\]\s*", "", line)
      part = part + cleaned_line
      if len(part) > parts_len:
        result.append(part)
        part = ""
    result.append(part)
  print(f"Общая транскрипция разбита на {len(result)} parts")
  return result
  
def request_to_llm(msgs):
  sub_results = ""
  for message in msgs:
    messages = [
      {'role':'system', 'content': PROMT_REPORT},
      {'role':'user', 'content': message}
    ]
    response: ChatResponse = chat(
      model=MODEL, 
      messages=messages,    
      options={'num_ctx': CONTEXT_LEN})
    print("Протокол части совещания:\n", response.message.content)
    sub_results = sub_results + "\n" + response.message.content
  return sub_results

def write_to_output(output_txt, report):
  with open(output_txt, "w", encoding="utf-8") as f:
    f.write(report)

# if __name__ == "__main__":
#   text_file = find_file_by_ext(EXT)
#   parts_len = calculate_parts_len(text_file)
#   message_to_llm = split_transcribe_to_messages(text_file, parts_len)
#   report = request_to_llm(message_to_llm)
#   write_to_output(os.path.join(REPORT_PATH ,FILE_PREFIX+os.path.basename(text_file)) ,report)
  