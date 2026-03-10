from llama_cpp.llama_chat_format import Llava15ChatHandler
from typing import Optional, List

class CustomGemma3ChatHandler(Llava15ChatHandler):
    """Полноценная замена Gemma3ChatHandler для старых версий llama-cpp-python (0.2.x / 118)"""
    
    DEFAULT_SYSTEM_MESSAGE = None  # MedGemma не любит дефолтный системный промпт

    # Это и есть вся магия — правильный Gemma-3 шаблон
    CHAT_FORMAT = (
        "{% for message in messages %}"
        "{% if message['role'] == 'user' %}"
        "<start_of_turn>user\n"
        "{% if message['content'] is string %}"
        "{{ message['content'] }}"
        "{% else %}"
        "{% for part in message['content'] %}"
        "{% if part['type'] == 'text' %}{{ part['text'] }}{% endif %}"
        "{% if part.get('type') == 'image_url' %}<image>\n{% endif %}"
        "{% endfor %}"
        "{% endif %}"
        "<end_of_turn>\n"
        "{% elif message['role'] == 'assistant' %}"
        "<start_of_turn>model\n"
        "{{ message.get('content', '') }}"
        "<end_of_turn>\n"
        "{% endif %}"
        "{% endfor %}"
        "{% if add_generation_prompt %}<start_of_turn>model\n{% endif %}"
    )

# ====================== ИСПОЛЬЗОВАНИЕ ======================

chat_handler = CustomGemma3ChatHandler(
    clip_model_path="path/to/mmproj-model-f16.gguf"
)

llm = Llama(
    model_path="medgemma-1.5-4b-it-Q6_K.gguf",
    chat_handler=chat_handler,
    chat_format=None,           # обязательно отключить старый шаблон!
    n_gpu_layers=24,            # подбери под свою 1060 (обычно 22-27)
    n_ctx=4096,
    n_batch=512,
    verbose=False               # поставь True на первый тест
)

# современный стиль:

import base64

with open("rentgen.jpg", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

messages = [{
    "role": "user",
    "content": [
        {
            "type": "text",
            "text": "Ты рентгенолог высшей категории. Проанализируй снимок максимально подробно..."
        },
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
        }
    ]
}]

response = llm.create_chat_completion(
    messages=messages,
    temperature=0.0,
    max_tokens=1500,
    stop=["<end_of_turn>", "<eos>"]
)

print(response['choices'][0]['message']['content'])