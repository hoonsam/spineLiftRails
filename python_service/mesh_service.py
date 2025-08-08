"""
Mesh generation service using the imported BatchMeshProcessor
"""
import logging
import tempfile
import os
from typing import Dict, Any, Optional, Tuple
import numpy as np
import cv2
from pathlib import Path
import aiofiles
import httpx

from core.batch.batch_mesh_processor import BatchMeshProcessor
from progress_callback import ProgressCallback

logger = logging.getLogger(__name__)

class MeshService:
    """Service for generating meshes from images"""
    
    def __init__(self):
        self.processor = None
        
    async def generate_mesh_from_url(
        self, 
        image_url: str, 
        parameters: Dict[str, Any],
        callback_url: Optional[str] = None,
        job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate mesh from image URL
        
        Args:
            image_url: URL to download image from
            parameters: Mesh generation parameters
            callback_url: Optional URL for progress callbacks
            job_id: Optional job ID for tracking
            
        Returns:
            Dict containing mesh data
        """
        progress = ProgressCallback(callback_url, job_id)
        
        try:
            # Initialize processor with parameters
            self.processor = BatchMeshProcessor(parameters)
            await progress.update(10, "Initialized mesh processor")
            
            # Download image
            await progress.update(20, "Downloading image")
            image_path = await self._download_image(image_url)
            
            # Generate mesh
            await progress.update(30, "Loading image")
            image, height, width = self.processor.load_image(str(image_path))
            if image is None:
                raise ValueError("Failed to load image")
                
            await progress.update(40, "Creating mask")
            mask = self.processor.create_initial_mask(image, height, width)
            
            await progress.update(50, "Finding contours")
            contour = self.processor.find_main_contour(mask)
            if contour is None:
                raise ValueError("No contours found in image")
                
            await progress.update(60, "Simplifying contour")
            simplified_contour, _ = self.processor.simplify_contour(
                contour, 
                width, 
                height,
                parameters.get("detail_factor", 0.01),
                parameters.get("concave_factor", 0.0)
            )
            
            await progress.update(70, "Generating triangulation")
            mesh_data = self.processor.triangulate_mesh(
                simplified_contour,
                width,
                height,
                parameters.get("internal_vertex_density", 0)
            )
            
            if mesh_data is None:
                raise ValueError("Failed to generate mesh")
                
            await progress.update(90, "Finalizing mesh data")
            
            # Generate UV coordinates
            from core.utils.mesh_utils import generate_standard_uvs
            vertices_flat = mesh_data["vertices"].flatten().tolist()
            uvs = generate_standard_uvs(vertices_flat, width, height)
            
            # Format mesh data for response
            result = {
                "vertices": mesh_data["vertices"].tolist(),
                "triangles": mesh_data["triangles"].tolist(),
                "uvs": uvs,
                "bounds": {
                    "x": 0,
                    "y": 0,
                    "width": width,
                    "height": height
                },
                "metadata": {
                    "vertex_count": len(mesh_data["vertices"]),
                    "triangle_count": len(mesh_data["triangles"]),
                    "parameters": parameters
                }
            }
            
            await progress.complete({"mesh_generated": True})
            
            # Clean up
            os.unlink(image_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating mesh: {e}")
            await progress.error(str(e))
            raise
            
    async def generate_mesh_from_file(
        self,
        image_data: bytes,
        parameters: Dict[str, Any],
        callback_url: Optional[str] = None,
        job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate mesh from uploaded file data
        
        Args:
            image_data: Image file bytes
            parameters: Mesh generation parameters
            callback_url: Optional URL for progress callbacks
            job_id: Optional job ID for tracking
            
        Returns:
            Dict containing mesh data
        """
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            tmp_file.write(image_data)
            tmp_path = tmp_file.name
            
        try:
            # Use file path to generate mesh
            progress = ProgressCallback(callback_url, job_id)
            self.processor = BatchMeshProcessor(parameters)
            
            await progress.update(30, "Loading image")
            image, height, width = self.processor.load_image(tmp_path)
            if image is None:
                raise ValueError("Failed to load image")
                
            # Rest of the mesh generation process
            await progress.update(40, "Creating mask")
            mask = self.processor.create_initial_mask(image, height, width)
            
            await progress.update(50, "Finding contours")
            contour = self.processor.find_main_contour(mask)
            if contour is None:
                raise ValueError("No contours found in image")
                
            await progress.update(60, "Simplifying contour")
            simplified_contour, _ = self.processor.simplify_contour(
                contour, 
                width, 
                height,
                parameters.get("detail_factor", 0.01),
                parameters.get("concave_factor", 0.0)
            )
            
            await progress.update(70, "Generating triangulation")
            mesh_data = self.processor.triangulate_mesh(
                simplified_contour,
                width,
                height,
                parameters.get("internal_vertex_density", 0)
            )
            
            if mesh_data is None:
                raise ValueError("Failed to generate mesh")
                
            await progress.update(90, "Finalizing mesh data")
            
            # Generate UV coordinates
            from core.utils.mesh_utils import generate_standard_uvs
            vertices_flat = mesh_data["vertices"].flatten().tolist()
            uvs = generate_standard_uvs(vertices_flat, width, height)
            
            # Format mesh data
            result = {
                "vertices": mesh_data["vertices"].tolist(),
                "triangles": mesh_data["triangles"].tolist(),
                "uvs": uvs,
                "bounds": {
                    "x": 0,
                    "y": 0,
                    "width": width,
                    "height": height
                },
                "metadata": {
                    "vertex_count": len(mesh_data["vertices"]),
                    "triangle_count": len(mesh_data["triangles"]),
                    "parameters": parameters
                }
            }
            
            await progress.complete({"mesh_generated": True})
            return result
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    async def _download_image(self, url: str) -> Path:
        """Download image from URL to temporary file"""
        async with httpx.AsyncClient() as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            tmp_file.write(response.content)
            return Path(tmp_file.name)