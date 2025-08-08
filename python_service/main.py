from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import numpy as np
import cv2
from PIL import Image
import psd_tools
import io
import base64
import tempfile
import os
import logging
import httpx
from mesh_service import MeshService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_progress_callback(callback_url: str, project_id: int, current: int, total: int):
    """Send progress update to Rails"""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(callback_url, json={
                "project_id": project_id,
                "event": "progress",
                "current": current,
                "total": total,
                "progress": round((current / total) * 100)
            })
    except Exception as e:
        logger.error(f"Failed to send callback: {e}")

app = FastAPI(title="SpineLift Python Service")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
mesh_service = MeshService()

class MeshGenerationParams(BaseModel):
    detail_factor: float = 0.01
    alpha_threshold: int = 10
    edge_threshold: int = 5
    max_triangles: int = 5000

class MeshGenerationRequest(BaseModel):
    image_url: str
    parameters: MeshGenerationParams
    callback_url: Optional[str] = None
    job_id: Optional[str] = None

class LayerInfo(BaseModel):
    name: str
    image_path: str
    position: int
    bounds: Dict[str, int]

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/extract_layers")
async def extract_layers(
    psd_file: UploadFile = File(...),
    project_id: int = Form(None),
    callback_url: str = Form(None)
):
    """Extract layers from a PSD file with progress callbacks"""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.psd') as tmp_file:
            content = await psd_file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Open PSD file
        psd = psd_tools.PSDImage.open(tmp_file_path)
        
        # Count total visible layers
        visible_layers = [layer for layer in psd.descendants() if layer.is_visible() and hasattr(layer, 'topil')]
        total_layers = len(visible_layers)
        
        layers = []
        layer_index = 0
        
        # Extract each layer
        for i, layer in enumerate(visible_layers):
            try:
                # Convert layer to PIL Image
                pil_image = layer.topil()
                if pil_image is None:
                    continue
                
                # Convert to base64 instead of saving to file
                img_buffer = io.BytesIO()
                pil_image.save(img_buffer, 'PNG')
                img_buffer.seek(0)
                image_data = base64.b64encode(img_buffer.read()).decode('utf-8')
                
                # Get layer metadata
                opacity = getattr(layer, 'opacity', 255) / 255.0
                blend_mode = str(getattr(layer, 'blend_mode', 'normal'))
                
                # Get layer bounds
                bounds = {
                    'x': layer.left,
                    'y': layer.top,
                    'width': layer.width,
                    'height': layer.height
                }
                
                layers.append({
                    'name': str(layer.name),
                    'image_data': image_data,
                    'position': layer_index,
                    'bounds': bounds,
                    'width': int(layer.width),
                    'height': int(layer.height),
                    'opacity': float(opacity),
                    'blend_mode': blend_mode,
                    'metadata': {
                        'visible': bool(layer.is_visible()),
                        'has_mask': bool(hasattr(layer, 'mask') and layer.mask is not None)
                    }
                })
                
                layer_index += 1
                
                # Send progress callback
                if callback_url and project_id:
                    await send_progress_callback(
                        callback_url, 
                        project_id, 
                        i + 1, 
                        total_layers
                    )
                
            except Exception as e:
                logger.error(f"Error processing layer {layer.name}: {str(e)}")
                continue
        
        # Clean up PSD file
        os.unlink(tmp_file_path)
        
        return {"layers": layers}
        
    except Exception as e:
        logger.error(f"Error extracting layers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate_mesh")
async def generate_mesh(request: MeshGenerationRequest, background_tasks: BackgroundTasks):
    """Generate mesh from image using triangulation"""
    try:
        # Convert Pydantic model to dict for mesh service
        params = request.parameters.dict()
        
        # Generate mesh using the service
        mesh_data = await mesh_service.generate_mesh_from_url(
            image_url=request.image_url,
            parameters=params,
            callback_url=request.callback_url,
            job_id=request.job_id
        )
        
        return {"mesh": mesh_data}
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating mesh: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate_mesh_from_file")
async def generate_mesh_from_file(
    file: UploadFile = File(...),
    detail_factor: float = 0.01,
    alpha_threshold: int = 10,
    callback_url: Optional[str] = None,
    job_id: Optional[str] = None
):
    """Generate mesh from uploaded image file"""
    try:
        # Read file content
        content = await file.read()
        
        # Prepare parameters
        params = {
            "detail_factor": detail_factor,
            "alpha_threshold": alpha_threshold
        }
        
        # Generate mesh
        mesh_data = await mesh_service.generate_mesh_from_file(
            image_data=content,
            parameters=params,
            callback_url=callback_url,
            job_id=job_id
        )
        
        return {"mesh": mesh_data}
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating mesh: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)