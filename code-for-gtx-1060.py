#1.unsloth/medgemma-1.5-4b-it-GGUF
# !pip install llama-cpp-python

from llama_cpp import Llama

llm = Llama.from_pretrained(
  repo_id="unsloth/medgemma-1.5-4b-it-GGUF",
  filename="medgemma-1.5-4b-it-Q6_K.gguf",
)
llm.create_chat_completion(
  messages = [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Describe this image in one sentence."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "https://cdn.britannica.com/61/93061-050-99147DCE/Statue-of-Liberty-Island-New-York-Bay.jpg"
          }
        }
      ]
    }
  ]
)




#2.

from llama_cpp import Llama
from llama_cpp.llama_chat_format import Llava15ChatHandler

# 1. Создаем обработчик картинок (скармливаем ему твой mmproj-model-f16.gguf)
chat_handler = Llava15ChatHandler(clip_model_path="path/to/mmproj-model-f16.gguf")

# 2. Инициализируем саму MedGemma
llm = Llama(
    model_path="medgemma-1.5-4b-it-Q6_K.gguf", # Твой основной файл
    chat_handler=chat_handler,
    n_gpu_layers=-1,  # Пытаемся засунуть ВСЁ в 1060
    n_ctx=2048,       # Для медицины 2048 токенов хватит на диалог и 1-2 фото
    logits_all=True
)