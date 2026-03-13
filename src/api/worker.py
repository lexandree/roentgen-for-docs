# src/api/worker.py
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import base64

# This will be replaced with the actual model loading and inference logic
from src.api.services.inference import MedGemmaModel, get_model

app = FastAPI()

class InferenceRequest(BaseModel):
    # Standard OpenAI-style messages array
    messages: List[Dict[str, Any]]


class InferenceResponse(BaseModel):
    report: str
    telemetry: Optional[Dict[str, Any]] = None

@app.post("/infer", response_model=InferenceResponse)
async def run_inference(
    request: InferenceRequest,
    model: MedGemmaModel = Depends(get_model)
):
    """
    A dedicated endpoint that only runs the model inference on the provided data.
    """
    try:
        # Call the actual inference function
        result = await model.perform_inference(messages=request.messages)
        return InferenceResponse(
            report=result.get("report", "Error"),
            telemetry=result.get("telemetry")
        )
    except Exception as e:
        # It's crucial to log the full error here for debugging on the worker
        print(f"!!! INFERENCE WORKER ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Error during model inference: {e}")

@app.post("/clear")
async def clear_vram(model: MedGemmaModel = Depends(get_model)):
    """
    Explicitly resets the model's KV cache to free up VRAM for security and performance.
    """
    try:
        if model.is_ready and model.model:
            model.model.reset()
        return {"status": "success", "message": "VRAM KV-cache cleared."}
    except Exception as e:
        print(f"!!! WORKER ERROR CLEARING VRAM: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing VRAM: {e}")

# This allows running the worker directly for testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
