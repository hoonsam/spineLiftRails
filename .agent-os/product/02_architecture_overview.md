# SpineLift Architecture Overview

## System Architecture

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                        Client (Browser)                          │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │   React     │  │   Tailwind   │  │   ActionCable         │  │
│  │   SPA       │  │   UI         │  │   WebSocket           │  │
│  └─────────────┘  └──────────────┘  └───────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS/WSS
┌────────────────────────────┴────────────────────────────────────┐
│                     Rails Application Server                     │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │   API       │  │   Active     │  │   Background          │  │
│  │   Controllers│  │   Storage    │  │   Jobs (Sidekiq)      │  │
│  └─────────────┘  └──────────────┘  └───────────────────────┘  │
│         │                  │                     │               │
│  ┌──────┴──────┐  ┌───────┴──────┐  ┌──────────┴────────────┐  │
│  │   Service   │  │    AWS S3    │  │   Service Objects     │  │
│  │   Objects   │  │   Storage    │  │   (Python Connector)  │  │
│  └─────────────┘  └──────────────┘  └───────────────────────┘  │
└─────────────────────────────────────────────┬───────────────────┘
                                              │ HTTP
┌─────────────────────────────────────────────┴───────────────────┐
│                  Python Mesh Processing Service                  │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │   FastAPI   │  │   Image      │  │   Mesh                │  │
│  │   Server    │  │   Processing │  │   Generation          │  │
│  └─────────────┘  └──────────────┘  └───────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Frontend Layer (React SPA)

#### Component Structure
```
src/
├── components/
│   ├── FileUpload.tsx       # PSD file upload
│   ├── LayerList.tsx        # Layer management
│   ├── MeshPreview.tsx      # Mesh visualization
│   ├── ProcessingStatus.tsx # Real-time progress
│   └── ui/                  # Reusable UI components
├── lib/
│   └── api.ts              # API client
├── store/
│   └── useStore.ts         # Zustand state management
└── types/
    └── index.ts            # TypeScript definitions
```

#### Key Features
- Single Page Application with React Router
- Real-time updates via ActionCable WebSocket
- Responsive design with Tailwind CSS
- Type-safe development with TypeScript

### 2. Rails Backend

#### Service Architecture
```
app/
├── controllers/
│   └── api/v1/
│       ├── auth_controller.rb
│       ├── projects_controller.rb
│       ├── layers_controller.rb
│       ├── meshes_controller.rb
│       └── mesh_progress_controller.rb
├── models/
│   ├── user.rb
│   ├── project.rb
│   ├── layer.rb
│   ├── mesh.rb
│   └── processing_log.rb
├── services/
│   ├── psd_processing_service.rb
│   ├── mesh_generation_service.rb
│   └── psd_processor.rb
├── jobs/
│   ├── process_psd_job.rb
│   ├── generate_mesh_job.rb
│   └── regenerate_mesh_job.rb
└── channels/
    ├── project_channel.rb
    └── layer_channel.rb
```

#### Request Flow
1. **Upload PSD** → Controller → Active Storage → Background Job
2. **Process PSD** → PsdProcessingService → Python Service
3. **Generate Mesh** → MeshGenerationService → Python Service
4. **Real-time Updates** → ActionCable → WebSocket → React

### 3. Python Mesh Service

#### Core Modules
```
python_service/
├── main.py                  # FastAPI application
├── mesh_service.py          # Mesh generation service
├── core/
│   ├── batch/
│   │   └── batch_mesh_processor.py
│   └── utils/
│       ├── image_utils.py
│       ├── mesh_utils.py
│       └── coordinate_converter.py
```

#### Processing Pipeline
1. **PSD Extraction**: Parse PSD layers using psd-tools
2. **Image Processing**: Apply filters and transformations
3. **Mesh Generation**: Create triangulated mesh using Delaunay
4. **Data Export**: Return vertices, triangles, and UV coordinates

## Data Flow

### 1. PSD Upload Flow
```
User uploads PSD
    ↓
Rails receives file
    ↓
Store in Active Storage (S3)
    ↓
Create Project record
    ↓
Queue ProcessPsdJob
    ↓
Job calls Python service
    ↓
Python extracts layers
    ↓
Create Layer records
    ↓
Store layer images
    ↓
Broadcast completion
```

### 2. Mesh Generation Flow
```
User selects layer
    ↓
Rails receives request
    ↓
Queue GenerateMeshJob
    ↓
Job calls Python service
    ↓
Python generates mesh
    ↓
Store mesh data
    ↓
Broadcast update
    ↓
Frontend renders mesh
```

## Communication Patterns

### 1. Synchronous Communication
- RESTful API for CRUD operations
- JWT authentication for API access
- JSON responses with consistent format

### 2. Asynchronous Communication
- Sidekiq for background job processing
- ActionCable for real-time updates
- Progress callbacks from Python service

### 3. Inter-Service Communication
```ruby
# Rails → Python Service
class MeshGenerationService
  include HTTParty
  base_uri ENV['PYTHON_SERVICE_URL']
  
  def generate_mesh(layer, parameters)
    post('/api/generate_mesh', 
      body: { 
        image_url: layer.image_url,
        parameters: parameters,
        callback_url: callback_url
      }.to_json
    )
  end
end
```

## Scalability Considerations

### Horizontal Scaling
- Rails: Multiple application servers behind load balancer
- Python: Multiple service instances
- Redis: Sentinel for high availability
- PostgreSQL: Read replicas for scaling

### Performance Optimizations
- Database indexing on foreign keys and JSONB fields
- Redis caching for frequently accessed data
- CDN for static assets and processed images
- Background processing for heavy operations

### Monitoring & Observability
- Application Performance Monitoring (APM)
- Structured logging with correlation IDs
- Health check endpoints for all services
- Error tracking and alerting

## Security Architecture

### Authentication & Authorization
- Devise for user authentication
- JWT tokens for API access
- Role-based access control (planned)

### Data Protection
- HTTPS/TLS for all communications
- Encrypted passwords (bcrypt)
- Secure file upload validation
- CORS configuration for API

### Input Validation
- Strong parameters in Rails
- Pydantic models in Python
- File type and size validation
- SQL injection protection via ORM