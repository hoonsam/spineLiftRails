# SpineLift API Documentation

## Overview

The SpineLift API provides programmatic access to PSD processing and mesh generation capabilities. All API endpoints require authentication via JWT tokens.

## Base URL
```
Production: https://api.spinelift.com/v1
Development: http://localhost:3000/api/v1
```

## Authentication

### Obtain Token
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

### Using Token
Include the JWT token in the Authorization header:
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## API Endpoints

### Authentication

#### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password",
  "name": "John Doe"
}
```

**Response:** Same as login endpoint

### Projects

#### List Projects
```http
GET /projects
```

**Query Parameters:**
- `page` (integer): Page number for pagination
- `per_page` (integer): Items per page (default: 20)
- `status` (string): Filter by status (pending, processing, completed, failed)

**Response:**
```json
{
  "projects": [
    {
      "id": 1,
      "name": "Character Sprite",
      "status": "completed",
      "created_at": "2024-12-10T10:00:00Z",
      "updated_at": "2024-12-10T10:05:00Z",
      "total_layers_count": 15,
      "processed_layers_count": 15,
      "processing_progress": 100
    }
  ],
  "meta": {
    "current_page": 1,
    "total_pages": 5,
    "total_count": 100
  }
}
```

#### Create Project
```http
POST /projects
Content-Type: multipart/form-data

{
  "name": "Character Sprite",
  "psd_file": <binary data>
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Character Sprite",
  "status": "pending",
  "created_at": "2024-12-10T10:00:00Z"
}
```

#### Get Project Details
```http
GET /projects/:id
```

**Response:**
```json
{
  "id": 1,
  "name": "Character Sprite",
  "status": "completed",
  "created_at": "2024-12-10T10:00:00Z",
  "updated_at": "2024-12-10T10:05:00Z",
  "total_layers_count": 15,
  "processed_layers_count": 15,
  "processing_progress": 100,
  "processing_duration": 300,
  "psd_file_url": "https://storage.spinelift.com/projects/1/original.psd"
}
```

#### Get Processing Status
```http
GET /projects/:id/processing_status
```

**Response:**
```json
{
  "status": "processing",
  "progress": 67,
  "current_step": "Generating mesh for layer 10 of 15",
  "processing_logs": [
    {
      "step": "psd_upload",
      "status": "completed",
      "message": "PSD file uploaded successfully",
      "created_at": "2024-12-10T10:00:00Z"
    },
    {
      "step": "layer_extraction",
      "status": "completed",
      "message": "Extracted 15 layers",
      "created_at": "2024-12-10T10:01:00Z"
    }
  ]
}
```

#### Cancel Processing
```http
POST /projects/:id/cancel_processing
```

**Response:**
```json
{
  "message": "Processing cancelled successfully",
  "status": "cancelled"
}
```

### Layers

#### List Project Layers
```http
GET /projects/:project_id/layers
```

**Response:**
```json
{
  "layers": [
    {
      "id": 1,
      "name": "Head",
      "position": 0,
      "status": "completed",
      "width": 512,
      "height": 512,
      "x_offset": 0,
      "y_offset": 0,
      "opacity": 1.0,
      "blend_mode": "normal",
      "image_url": "https://storage.spinelift.com/layers/1/image.png",
      "has_mesh": true
    }
  ]
}
```

#### Get Layer Details
```http
GET /projects/:project_id/layers/:id
```

**Response:** Single layer object with full details

#### Update Layer
```http
PATCH /projects/:project_id/layers/:id
Content-Type: application/json

{
  "name": "Head (Updated)",
  "opacity": 0.8
}
```

### Meshes

#### Get Layer Mesh
```http
GET /projects/:project_id/layers/:layer_id/mesh
```

**Response:**
```json
{
  "id": 1,
  "layer_id": 1,
  "vertices": [
    [0.0, 0.0],
    [1.0, 0.0],
    [0.5, 1.0]
  ],
  "triangles": [
    [0, 1, 2]
  ],
  "uvs": [
    [0.0, 0.0],
    [1.0, 0.0],
    [0.5, 1.0]
  ],
  "parameters": {
    "detail_factor": 0.01,
    "alpha_threshold": 10,
    "edge_threshold": 5,
    "max_triangles": 5000
  },
  "statistics": {
    "vertex_count": 150,
    "triangle_count": 280,
    "generation_time": 1.23
  }
}
```

#### Update Mesh Parameters
```http
PATCH /projects/:project_id/layers/:layer_id/mesh
Content-Type: application/json

{
  "parameters": {
    "detail_factor": 0.02,
    "alpha_threshold": 20
  },
  "regenerate": true
}
```

**Response:** Updated mesh object

### Progress Callbacks

#### Mesh Generation Progress
```http
POST /mesh_progress
Content-Type: application/json

{
  "project_id": 1,
  "layer_id": 1,
  "event": "progress",
  "progress": 50,
  "message": "Generating triangulation..."
}
```

## WebSocket Channels

### Project Channel
```javascript
// Subscribe to project updates
const cable = ActionCable.createConsumer('wss://api.spinelift.com/cable');
const subscription = cable.subscriptions.create(
  { 
    channel: 'ProjectChannel',
    project_id: 1
  },
  {
    received(data) {
      console.log('Project update:', data);
      // data: { event: 'processing_complete', project: {...} }
    }
  }
);
```

### Layer Channel
```javascript
// Subscribe to layer updates
const subscription = cable.subscriptions.create(
  { 
    channel: 'LayerChannel',
    layer_id: 1
  },
  {
    received(data) {
      console.log('Layer update:', data);
      // data: { event: 'mesh_generated', layer: {...}, mesh: {...} }
    }
  }
);
```

## Error Responses

### Standard Error Format
```json
{
  "error": "Validation failed",
  "details": {
    "name": ["can't be blank"],
    "psd_file": ["must be a PSD file", "is too large (max 500MB)"]
  }
}
```

### HTTP Status Codes
- `200 OK`: Success
- `201 Created`: Resource created
- `400 Bad Request`: Invalid request
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Access denied
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation errors
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Rate Limiting

API requests are limited to:
- **Authenticated users**: 1000 requests per hour
- **Unauthenticated requests**: 60 requests per hour

Rate limit headers:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1670000000
```

## Pagination

List endpoints support pagination:
```http
GET /projects?page=2&per_page=50
```

Pagination metadata in response:
```json
{
  "data": [...],
  "meta": {
    "current_page": 2,
    "total_pages": 10,
    "total_count": 500,
    "per_page": 50
  }
}
```

## Webhooks (Coming Soon)

Configure webhooks for async notifications:
```json
{
  "url": "https://your-app.com/webhooks/spinelift",
  "events": ["project.completed", "mesh.generated"],
  "secret": "your_webhook_secret"
}
```

## SDK Examples

### JavaScript/TypeScript
```typescript
import { SpineLiftClient } from '@spinelift/sdk';

const client = new SpineLiftClient({
  apiKey: 'your_api_key',
  baseUrl: 'https://api.spinelift.com/v1'
});

// Create project
const project = await client.projects.create({
  name: 'My Character',
  psdFile: fileBlob
});

// Get layers
const layers = await client.projects.layers(project.id).list();

// Generate mesh
const mesh = await client.layers.mesh(layers[0].id).generate({
  detailFactor: 0.01,
  alphaThreshold: 10
});
```

### Python
```python
from spinelift import SpineLiftClient

client = SpineLiftClient(
    api_key='your_api_key',
    base_url='https://api.spinelift.com/v1'
)

# Create project
with open('character.psd', 'rb') as f:
    project = client.projects.create(
        name='My Character',
        psd_file=f
    )

# Get layers
layers = client.projects.layers(project.id).list()

# Generate mesh
mesh = client.layers.mesh(layers[0].id).generate(
    detail_factor=0.01,
    alpha_threshold=10
)
```

## Best Practices

1. **Caching**: Cache project and layer data locally
2. **Polling**: For status updates, use WebSockets when possible
3. **Error Handling**: Implement exponential backoff for retries
4. **File Uploads**: Use multipart/form-data for large files
5. **Batch Operations**: Group multiple operations when possible

## Support

- **Documentation**: https://docs.spinelift.com
- **API Status**: https://status.spinelift.com
- **Support Email**: api-support@spinelift.com
- **Community Forum**: https://community.spinelift.com