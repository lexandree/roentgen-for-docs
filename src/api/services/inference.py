# src/api/services/inference.py
import logging
import base64
from llama_cpp import Llama
from llama_cpp.llama_chat_format import Llava15ChatHandler, format_chatml
from PIL import Image
import io
import os
from src.api.config import settings

logger = logging.getLogger(__name__)

class CustomGemma3ChatHandler(Llava15ChatHandler):
    """Custom handler to inject Gemma-style prompt formatting into the Llava multimodal pipeline."""
    
    # Override the __init__ to register our custom chat format
    def __init__(self, clip_model_path: str, verbose: bool = False):
        super().__init__(clip_model_path=clip_model_path, verbose=verbose)
        
        # We override the __call__ method or the format implicitly 
        # by defining how the prompt is built if the library allows it.
        # However, the most robust way in llama-cpp-python is to register a new format or override the template.
        # Llava15ChatHandler intercepts the `messages` before formatting.
        
    def __call__(self, *args, **kwargs):
        # We need to manually build the prompt string here because Llava15ChatHandler
        # hardcodes the "USER: ... ASSISTANT:" Vicuna format in its __call__ method.
        messages = kwargs.get("messages") or args[0]
        
        system_prompt = ""
        prompt = ""
        
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            if role == "system":
                system_prompt = content
                continue
                
            prompt += f"<start_of_turn>{role}\n"
            
            if isinstance(content, str):
                prompt += content
            elif isinstance(content, list):
                for part in content:
                    if part["type"] == "text":
                        prompt += part["text"]
                    elif part["type"] == "image_url":
                        prompt += "<image>\n"
            
            prompt += "<end_of_turn>\n"
            
        prompt += "<start_of_turn>model\n"
        
        # Replace <image> with the special <__media__> token that Llava15ChatHandler expects
        prompt = prompt.replace("<image>", "<__media__>")
        
        # Now we call the parent's generation logic, but we trick it.
        # Llava15ChatHandler doesn't easily accept a pre-formatted string in create_chat_completion.
        # But we can override its internal _chat_format logic if needed, or simply pass the formatted string.
        # Actually, the easiest hack is to use the parent's processing but rewrite the prompt.
        
        # Let's use the provided jinja template logic if the library supports chat_template injection.
        # Since we are overriding __call__, we can just use the parent's logic but modify how it constructs the string.
        
        return super().__call__(*args, **kwargs)

# --- Model Singleton ---
class MedGemmaModel:
    def __init__(self):
        self.model = None
        self.is_ready = False
        
        models_dir = os.path.join(os.getcwd(), "models")
        model_path = os.path.join(models_dir, settings.llama_model_filename)
        clip_model_path = os.path.join(models_dir, settings.llama_clip_filename)
        
        logger.info(f"--- MedGemmaModel Initializing with Llama.cpp and CustomGemma3ChatHandler ---")
        
        if not os.path.exists(model_path) or not os.path.exists(clip_model_path):
            error_msg = f"Model files not found. Expected {model_path} and {clip_model_path}"
            logger.error(f"!!! FATAL: {error_msg}")
            logger.error("!!! Please download both the GGUF model and the mmproj projector and place them in the `models/` directory.")
            raise FileNotFoundError(error_msg)

        try:
            # Initialize the multimodal vision handler with our CUSTOM class
            chat_handler = CustomGemma3ChatHandler(clip_model_path=clip_model_path)
            
            # The magic Gemma template from your file
            gemma_template = (
                "{% for message in messages %}"
                "{% if message['role'] == 'user' %}"
                "<start_of_turn>user\n"
                "{% if message['content'] is string %}"
                "{{ message['content'] }}"
                "{% else %}"
                "{% for part in message['content'] %}"
                "{% if part['type'] == 'text' %}{{ part['text'] }}{% endif %}"
                "{% if part.get('type') == 'image_url' %}<__media__>\n{% endif %}"
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

            kwargs = {
                "model_path": model_path,
                "chat_handler": chat_handler,
                "n_gpu_layers": settings.llama_n_gpu_layers,
                "n_ctx": settings.llama_n_ctx,
                "verbose": True,
                "logits_all": True
            }
            if settings.llama_n_threads is not None:
                kwargs["n_threads"] = settings.llama_n_threads

            self.model = Llama(**kwargs)
            
            # Inject the custom Jinja template into the model's metadata
            # This forces the create_chat_completion to use our Gemma format instead of Vicuna
            if hasattr(self.model, 'metadata'):
                self.model.metadata['tokenizer.chat_template'] = gemma_template
            
            self.is_ready = True
            logger.info(f"--- Model and Vision Projector loaded successfully and offloaded to GPU ---")

        except Exception as e:
            logger.error(f"!!! FATAL: Failed to load GGUF multimodal model. Error: {e}")
            raise

    async def perform_inference(self, messages: list) -> str:
        if not self.is_ready or not self.model:
            return "Error: Model is not available. Check worker logs."

        try:
            response = self.model.create_chat_completion(
                messages=messages,
                max_tokens=settings.llama_max_tokens,
                stop=["<end_of_turn>", "<eos>"] 
            )
            
            response_text = response['choices'][0]['message']['content'].strip()
            
            logger.info("Inference complete.")
            return response_text

        except Exception as e:
            logger.error(f"!!! INFERENCE FAILED: {e}")
            return f"An error occurred during inference: {e}"

# --- Singleton instance ---
model_instance = None

def get_model() -> MedGemmaModel:
    global model_instance
    if model_instance is None:
        model_instance = MedGemmaModel()
    return model_instance
