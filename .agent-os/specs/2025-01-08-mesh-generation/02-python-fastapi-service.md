# Python FastAPI Mesh Service Specification

## Overview

Port the existing `BatchMeshProcessor` from the SpineLift Python codebase to a production-ready FastAPI service that can handle concurrent mesh generation requests with proper error handling and progress reporting.

## Service Structure

```
python_service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management
│   ├── models/              # Pydantic models
│   │   ├── __init__.py
│   │   ├── mesh.py          # Mesh request/response models
│   │   └── progress.py      # Progress update models
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   ├── mesh_processor.py # Ported BatchMeshProcessor
│   │   └── storage.py       # File storage abstraction
│   ├── api/                 # API endpoints
│   │   ├── __init__.py
│   │   ├── health.py        # Health check endpoints
│   │   └── mesh.py          # Mesh generation endpoints
│   └── utils/               # Utility functions
│       ├── __init__.py
│       ├── validation.py    # Parameter validation
│       └── callbacks.py     # Progress callbacks
├── tests/
├── requirements.txt
└── Dockerfile
```

## API Endpoints

### 1. Health Check
```
GET /health
Response: {
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-01-08T10:00:00Z"
}
```

### 2. Generate Mesh
```
POST /api/v1/mesh/generate
Request: {
  "image_url": "https://storage.example.com/image.png",
  "parameters": {
    "detail_factor": 0.01,
    "alpha_threshold": 10,
    "concave_factor": 0.0,
    "internal_vertex_density": 0,
    "blur_kernel_size": 1,
    "binary_threshold": 128,
    "min_contour_area": 10,
    "density_scaling_factor": 1000.0,
    "min_triangle_area": 1.0
  },
  "callback_url": "https://rails-app.com/api/mesh/callback",
  "job_id": "unique-job-identifier"
}

Response: {
  "job_id": "unique-job-identifier",
  "status": "processing",
  "estimated_time": 15
}
```

### 3. Get Mesh Status
```
GET /api/v1/mesh/{job_id}/status
Response: {
  "job_id": "unique-job-identifier",
  "status": "completed|processing|failed",
  "progress": 75,
  "message": "Triangulating mesh...",
  "result_url": "https://storage.example.com/mesh.json" // if completed
}
```

## Mesh Processor Implementation

### Core Processing Steps

```python
class MeshProcessor:
    def __init__(self, params: MeshParameters):
        self.params = params
        self.progress_callback = None
        
    async def process_image(self, image_path: str) -> MeshResult:
        """Main processing pipeline with progress updates"""
        
        # Step 1: Load and validate image (10%)
        await self._update_progress(10, "Loading image...")
        img, height, width = self._load_image(image_path)
        
        # Step 2: Create initial mask (20%)
        await self._update_progress(20, "Creating mask...")
        mask = self._create_initial_mask(img, height, width)
        
        # Step 3: Process mask for contours (30%)
        await self._update_progress(30, "Processing contours...")
        binary_mask = self._process_mask_for_contours(mask)
        
        # Step 4: Find main contour (40%)
        await self._update_progress(40, "Finding main contour...")
        contour = self._find_main_contour(binary_mask)
        
        # Step 5: Simplify contour (50%)
        await self._update_progress(50, "Simplifying contour...")
        pts_simplified = self._simplify_contour(contour, width, height)
        
        # Step 6: Triangulate mesh (70%)
        await self._update_progress(70, "Triangulating mesh...")
        mesh_data = self._triangulate_mesh(pts_simplified, width, height)
        
        # Step 7: Generate UV coordinates (85%)
        await self._update_progress(85, "Generating UV coordinates...")
        uvs = self._generate_uvs(mesh_data['vertices'], width, height)
        
        # Step 8: Calculate edges (95%)
        await self._update_progress(95, "Calculating edges...")
        boundary_edges, internal_edges = self._calculate_edges(
            mesh_data['triangles'], 
            len(mesh_data['vertices'])
        )
        
        # Step 9: Finalize result (100%)
        await self._update_progress(100, "Mesh generation complete")
        
        return MeshResult(
            vertices=mesh_data['vertices'],
            triangles=mesh_data['triangles'],
            uvs=uvs,
            boundary_edges=boundary_edges,
            internal_edges=internal_edges,
            metadata={
                'width': width,
                'height': height,
                'vertex_count': len(mesh_data['vertices']),
                'triangle_count': len(mesh_data['triangles'])
            }
        )
```

## Parameter Validation

```python
class MeshParameters(BaseModel):
    detail_factor: float = Field(0.01, ge=0.001, le=0.050)
    alpha_threshold: int = Field(10, ge=0, le=255)
    concave_factor: float = Field(0.0, ge=0.0, le=100.0)
    internal_vertex_density: int = Field(0, ge=0, le=100)
    blur_kernel_size: int = Field(1, ge=1, le=21)
    binary_threshold: int = Field(128, ge=0, le=255)
    min_contour_area: float = Field(10, ge=1, le=1000)
    density_scaling_factor: float = Field(1000.0, ge=100, le=10000)
    min_triangle_area: float = Field(1.0, ge=0.1, le=100)
    
    @validator('blur_kernel_size')
    def validate_odd_kernel(cls, v):
        if v % 2 == 0:
            return v + 1
        return v
```

## Error Handling

```python
class MeshGenerationError(Exception):
    """Base exception for mesh generation errors"""
    pass

class ImageLoadError(MeshGenerationError):
    """Failed to load or validate image"""
    pass

class ContourExtractionError(MeshGenerationError):
    """Failed to extract valid contours"""
    pass

class TriangulationError(MeshGenerationError):
    """Failed to triangulate mesh"""
    pass

# Error response format
{
    "error": {
        "code": "TRIANGULATION_FAILED",
        "message": "Failed to triangulate mesh: insufficient vertices",
        "details": {
            "vertex_count": 2,
            "minimum_required": 3
        }
    }
}
```

## Progress Callback Implementation

```python
async def send_progress_update(
    callback_url: str, 
    job_id: str, 
    progress: int, 
    message: str
):
    """Send progress update to Rails callback URL"""
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                callback_url,
                json={
                    "job_id": job_id,
                    "progress": progress,
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat()
                },
                timeout=5.0
            )
        except Exception as e:
            logger.error(f"Failed to send progress update: {e}")
```

## Configuration

```python
class Settings(BaseSettings):
    # Service configuration
    service_name: str = "spinelift-mesh-service"
    version: str = "1.0.0"
    debug: bool = False
    
    # API configuration
    api_prefix: str = "/api/v1"
    max_request_size: int = 100 * 1024 * 1024  # 100MB
    request_timeout: int = 300  # 5 minutes
    
    # Processing configuration
    max_image_dimension: int = 4096
    max_concurrent_jobs: int = 10
    job_timeout: int = 600  # 10 minutes
    
    # Storage configuration
    storage_backend: str = "local"  # or "s3"
    storage_path: str = "/app/storage"
    
    # Redis configuration (for distributed locking)
    redis_url: str = "redis://localhost:6379/0"
    
    class Config:
        env_file = ".env"
```

## Docker Configuration

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create storage directory
RUN mkdir -p /app/storage

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Performance Considerations

1. **Async Processing**: Use FastAPI's async capabilities for I/O operations
2. **Connection Pooling**: Implement HTTP client connection pooling for callbacks
3. **Resource Limits**: Set memory and CPU limits per job
4. **Caching**: Cache processed results for identical parameters
5. **Monitoring**: Implement Prometheus metrics for performance tracking

## Testing Strategy

1. **Unit Tests**: Test individual mesh processing functions
2. **Integration Tests**: Test full processing pipeline
3. **Load Tests**: Verify concurrent request handling
4. **Error Tests**: Validate error handling for edge cases
5. **Performance Tests**: Ensure processing time requirements are met