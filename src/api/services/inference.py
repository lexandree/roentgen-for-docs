# src/api/services/inference.py
import logging
import base64
from llama_cpp import Llama
from PIL import Image
import io
import os

logger = logging.getLogger(__name__)

# --- Model Singleton ---
class MedGemmaModel:
    def __init__(self):
        self.model = None
        self.is_ready = False
        
        model_path = os.path.join(os.getcwd(), "models", "medgemma-1.5.gguf") 
        logger.info(f"--- MedGemmaModel Initializing with Llama.cpp ---")
        
        if not os.path.exists(model_path):
            logger.error(f"!!! FATAL: Model file not found at {model_path}")
            logger.error("!!! Please download the GGUF version of the model and place it in the `models/` directory.")
            return

        try:
            # n_gpu_layers=-1 attempts to offload all layers to the GPU
            # This is the key to using your GTX 1060
            self.model = Llama(
                model_path=model_path,
                n_gpu_layers=-1,
                verbose=True,
                n_ctx=2048, # Context window
            )
            self.is_ready = True
            logger.info(f"--- Model loaded successfully from {model_path} and offloaded to GPU ---")

        except Exception as e:
            logger.error(f"!!! FATAL: Failed to load GGUF model. Error: {e}")

    async def perform_inference(self, image_bytes: bytes, caption: str | None) -> str:
        if not self.is_ready or not self.model:
            return "Error: Model is not available. Check worker logs."

        try:
            # --- CRITICAL NOTE ON MULTIMODALITY ---
            # The following part is highly dependent on whether the MedGemma GGUF model
            # was compiled with LLaVA-like multi-modal support for Llama.cpp.
            # If not, this will fail. We are proceeding assuming it is compatible.
            
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # This chat format is based on LLaVA's implementation in Llama.cpp
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
