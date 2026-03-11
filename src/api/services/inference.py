# src/api/services/inference.py
import logging
import base64
from llama_cpp import Llama
from llama_cpp.llama_chat_format import Llava15ChatHandler
from PIL import Image
import io
import os
import time
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
            raise FileNotFoundError(error_msg)

        try:
            # We must use the base Llava15ChatHandler to prevent internal state corruption,
            # BUT we will bypass its chat formatting by using the low-level model() call
            # or by sending exactly ONE user message to prevent the broadcast error on multi-turn.
            self.chat_handler = Llava15ChatHandler(clip_model_path=clip_model_path)

            kwargs = {
                "model_path": model_path,
                "chat_handler": self.chat_handler,
                "n_gpu_layers": settings.llama_n_gpu_layers,
                "n_ctx": settings.llama_n_ctx,
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

    async def perform_inference(self, messages: list) -> dict:
        if not self.is_ready or not self.model:
            return {"report": "Error: Model is not available. Check worker logs.", "telemetry": {}}

        start_time = time.time()
        try:
            # HACK FOR MEDGEMMA + LLAVA15:
            # Llava15ChatHandler crashes on multi-turn history with images due to tensor shape mismatches.
            # It also hardcodes the Vicuna prompt format.
            # To fix this, we will squash the ENTIRE history into a SINGLE "user" message.
            # This forces the handler to process it as one prompt, avoiding the broadcast error,
            # and allows us to inject Gemma's native formatting manually within that single message.
            
            squashed_prompt = ""
            image_b64 = None
            
            # 1. Extract the image if it exists anywhere in the history
            for msg in messages:
                if isinstance(msg["content"], list):
                    for part in msg["content"]:
                        if part["type"] == "image_url":
                            # Extract base64 data (strip prefix "data:image/jpeg;base64,")
                            url_data = part["image_url"]["url"]
                            if "," in url_data:
                                image_b64 = url_data.split(",")[1]

            # 2. Build the Gemma-formatted prompt manually
            for i, msg in enumerate(messages):
                role = msg["role"]
                squashed_prompt += f"<start_of_turn>{role}\n"
                
                content = msg["content"]
                if isinstance(content, str):
                    squashed_prompt += content
                elif isinstance(content, list):
                    for part in content:
                        if part["type"] == "text":
                            squashed_prompt += part["text"]
                
                squashed_prompt += "<end_of_turn>\n"
            
            # The final prompt for the model to answer
            squashed_prompt += "<start_of_turn>model\n"
            
            # 3. Create the SINGLE message for Llava15ChatHandler
            final_content = []
            if image_b64:
                # We put the image first
                final_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                })
            
            # Then we put our manually squashed Gemma prompt
            final_content.append({
                "type": "text",
                "text": squashed_prompt
            })
            
            single_message = [{"role": "user", "content": final_content}]

            # 4. Run inference using the standard API, but with our squashed single message
            response = self.model.create_chat_completion(
                messages=single_message,
                max_tokens=settings.llama_max_tokens,
                stop=["<end_of_turn>", "<eos>", "USER:", "ASSISTANT:"] 
            )
            
            response_text = response['choices'][0]['message']['content'].strip()
            
            # The handler might echo back parts of our prompt due to the Vicuna wrapper.
            # Clean up any bleeding tags just in case.
            for tag in ["ASSISTANT:", "<start_of_turn>model\n"]:
                if response_text.startswith(tag):
                    response_text = response_text[len(tag):].strip()
            
            latency = time.time() - start_time
            usage = response.get("usage", {})
            
            logger.info(f"Inference complete. Latency: {latency:.2f}s")
            
            return {
                "report": response_text,
                "telemetry": {
                    "latency": latency,
                    "input_tokens": usage.get("prompt_tokens"),
                    "output_tokens": usage.get("completion_tokens")
                }
            }

        except Exception as e:
            logger.error(f"!!! INFERENCE FAILED: {e}")
            return {"report": f"An error occurred during inference: {e}", "telemetry": {"latency": time.time() - start_time}}

# --- Singleton instance ---
model_instance = None

def get_model() -> MedGemmaModel:
    global model_instance
    if model_instance is None:
        model_instance = MedGemmaModel()
    return model_instance
