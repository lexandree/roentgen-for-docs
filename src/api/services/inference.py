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

    async def perform_inference(self, image_bytes: bytes, caption: str | None) -> str:
        if not self.is_ready or not self.model:
            return "Error: Model is not available. Check worker logs."

        try:
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # This chat format is supported by Llava15ChatHandler
            prompt = {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                            {"type": "text", "content": caption or "Analyze this medical image in detail."}
                        ]
                    }
                ]
            }

            # Using create_chat_completion for multi-modal input
            response = self.model.create_chat_completion(
                messages=prompt["messages"],
                max_tokens=512
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
