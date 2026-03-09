# src/api/services/inference.py
import logging
import base64
from llama_cpp import Llama
from llama_cpp.llama_chat_format import Llava15ChatHandler
from PIL import Image
import io
import os
from src.api.config import settings

logger = logging.getLogger(__name__)

# --- Model Singleton ---
class MedGemmaModel:
    def __init__(self):
        self.model = None
        self.is_ready = False
        
        models_dir = os.path.join(os.getcwd(), "models")
        model_path = os.path.join(models_dir, settings.llama_model_filename)
        clip_model_path = os.path.join(models_dir, settings.llama_clip_filename)
        
        logger.info(f"--- MedGemmaModel Initializing with Llama.cpp and Llava15ChatHandler ---")
        
        if not os.path.exists(model_path) or not os.path.exists(clip_model_path):
            error_msg = f"Model files not found. Expected {model_path} and {clip_model_path}"
            logger.error(f"!!! FATAL: {error_msg}")
            logger.error("!!! Please download both the GGUF model and the mmproj projector and place them in the `models/` directory.")
            # Fail fast so the worker crashes immediately on startup if misconfigured
            raise FileNotFoundError(error_msg)

        try:
            # Initialize the multimodal vision handler
            chat_handler = Llava15ChatHandler(clip_model_path=clip_model_path)

            kwargs = {
                "model_path": model_path,
                "chat_handler": chat_handler,
                "n_gpu_layers": settings.llama_n_gpu_layers,
                "n_ctx": settings.llama_n_ctx, # Context window for dialogue and image
                "chat_format": "gemma", # Enforce Gemma prompt formatting instead of Llava/Vicuna
                "verbose": True,
                "logits_all": True
            }
            if settings.llama_n_threads is not None:
                kwargs["n_threads"] = settings.llama_n_threads

            self.model = Llama(**kwargs)
            
            self.is_ready = True
            logger.info(f"--- Model and Vision Projector loaded successfully and offloaded to GPU ---")

        except Exception as e:
            logger.error(f"!!! FATAL: Failed to load GGUF multimodal model. Error: {e}")
            raise

    async def perform_inference(self, image_bytes: bytes | None, caption: str | None, history: list = None) -> str:
        if not self.is_ready or not self.model:
            return "Error: Model is not available. Check worker logs."

        if history is None:
            history = []

        try:
            # Build the message structure for the model
            messages = []
            
            # Append history first
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})

            # Construct the current prompt
            current_content = []
            if image_bytes:
                image_b64 = base64.b64encode(image_bytes).decode('utf-8')
                current_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}})
            
            if caption:
                current_content.append({"type": "text", "text": caption})
            elif not image_bytes:
                # If there's no image and no caption, just send a default text to avoid empty content
                current_content.append({"type": "text", "text": "Please continue."})
                
            messages.append({
                "role": "user",
                "content": current_content
            })

            # Using create_chat_completion for multi-modal/text input
            response = self.model.create_chat_completion(
                messages=messages,
                max_tokens=settings.llama_max_tokens,
                stop=["<end_of_turn>", "<eos>"] # Use Gemma specific stop tokens
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
