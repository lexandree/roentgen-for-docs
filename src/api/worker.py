# src/api/worker.py
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import base64

# This will be replaced with the actual model loading and inference logic
from src.api.services.inference import MedGemmaModel, get_model

app = FastAPI()

class InferenceRequest(BaseModel):
    # We send bytes as a base64 encoded string to ensure JSON compatibility
    image_bytes_b64: str
    caption: Optional[str] = None

class InferenceResponse(BaseModel):
    report: str

@app.post("/infer", response_model=InferenceResponse)
async def run_inference(
    request: InferenceRequest,
    model: MedGemmaModel = Depends(get_model)
):
    """
    A dedicated endpoint that only runs the model inference on the provided data.
    """
    try:
        # Decode the base64 string back to bytes
        image_bytes = base64.b64decode(request.image_bytes_b64)
        
        # Call the actual inference function
        diagnostic_report = await model.perform_inference(
            image_bytes=image_bytes,
            caption=request.caption
        )
        return InferenceResponse(report=diagnostic_report)
    except Exception as e:
        # It's crucial to log the full error here for debugging on the worker
        print(f"!!! INFERENCE WORKER ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Error during model inference: {e}")

# This allows running the worker directly for testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
