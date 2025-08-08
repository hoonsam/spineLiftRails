# SpineLift Python Service

This FastAPI service handles mesh generation and PSD processing for SpineLift Rails.

## Features

- **PSD Layer Extraction**: Extract layers from PSD files with metadata
- **Mesh Generation**: Generate triangulated meshes from images using the Triangle library
- **Progress Tracking**: Real-time progress updates sent back to Rails
- **Parameter Customization**: Fine-tune mesh generation with various parameters

## Setup

1. Run the setup script (creates virtual environment and installs dependencies):
```bash
./setup.sh
```

2. Run the service:
```bash
./run.sh
```

Or manually:
```bash
source venv/bin/activate
python main.py
```

The service will start on http://localhost:8000

## API Endpoints

### Health Check
- `GET /health` - Check if service is running

### PSD Processing
- `POST /api/extract_layers` - Extract layers from uploaded PSD file
  - Body: multipart/form-data with `psd_file` field

### Mesh Generation
- `POST /api/generate_mesh` - Generate mesh from image URL
  - Body: JSON with `image_url`, `parameters`, optional `callback_url` and `job_id`
  
- `POST /api/generate_mesh_from_file` - Generate mesh from uploaded file
  - Body: multipart/form-data with `file` and parameter fields

## Mesh Generation Parameters

- `detail_factor` (0.001-0.05): Controls contour simplification detail
- `alpha_threshold` (0-255): Minimum alpha value for mask creation
- `concave_factor` (0-100): How much to preserve concave regions
- `internal_vertex_density` (0+): Density of internal vertices
- `blur_kernel_size` (odd number): Blur kernel for mask smoothing
- `binary_threshold` (0-255): Threshold for binary mask
- `min_contour_area` (0+): Minimum contour area to consider

## Progress Callbacks

When `callback_url` is provided, the service sends progress updates:

```json
{
  "job_id": "unique-job-id",
  "progress": 50,
  "message": "Processing contours",
  "elapsed_time": 2.5,
  "data": {}
}
```

## Development

### Running Tests
```bash
cd ..
python test_mesh_generation.py
```

### Docker
```bash
docker build -t spinelift-python .
docker run -p 8000:8000 spinelift-python
```

## Architecture

The service uses:
- **FastAPI** for the web framework
- **Triangle** for Delaunay triangulation
- **OpenCV** for image processing
- **Pillow** for image I/O
- **psd-tools** for PSD file handling

The mesh generation follows these steps:
1. Load image and extract alpha channel
2. Create binary mask from alpha
3. Find and simplify contours
4. Generate triangulation using Triangle
5. Calculate UV coordinates
6. Return mesh data