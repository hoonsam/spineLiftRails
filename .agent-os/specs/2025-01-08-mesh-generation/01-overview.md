# SpineLift Rails Week 3-4: Mesh Generation Feature Specification

## Overview

This specification outlines the implementation of the mesh generation functionality for SpineLift Rails, building upon the existing backend API and Python service structure. The feature will port the existing Python mesh processor to a FastAPI service and integrate it with the Rails application through background jobs and real-time progress updates.

## Project Context

- **Current State**: 
  - Rails backend API with authentication and basic endpoints complete
  - Python service structure established with Docker integration
  - Database models for projects, images, and meshes in place
  
- **Goal**: 
  - Implement production-ready mesh generation service
  - Enable users to upload images and generate Spine-compatible meshes
  - Provide real-time progress feedback during processing

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Rails App     │────▶│   Redis Queue   │────▶│  Python Service │
│  (Web/API)      │     │   (Sidekiq)     │     │   (FastAPI)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                         │                        │
        ▼                         ▼                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   PostgreSQL    │     │  Redis PubSub   │     │  File Storage   │
│   (Metadata)    │     │  (Progress)     │     │  (Images/Mesh)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Key Components

### 1. Python Mesh Service (FastAPI)
- Port existing `BatchMeshProcessor` from Python codebase
- RESTful API endpoints for mesh generation
- Asynchronous processing support
- Progress reporting via callbacks

### 2. Rails Service Layer
- `MeshGenerationService` - Main orchestration
- `PythonServiceClient` - HTTP client for Python service
- `MeshParameterValidator` - Input validation
- `ProgressTracker` - Real-time updates

### 3. Background Jobs (Sidekiq)
- `MeshGenerationJob` - Main processing job
- `MeshCleanupJob` - Failed job cleanup
- `NotificationJob` - User notifications

### 4. Real-time Updates
- ActionCable channels for progress
- Redis PubSub for inter-service communication
- WebSocket fallback for compatibility

## Implementation Timeline

### Week 3: Core Implementation
- Days 1-2: Port Python mesh processor to FastAPI
- Days 3-4: Rails service wrappers and job implementation
- Day 5: Integration testing and debugging

### Week 4: Polish and Optimization
- Days 1-2: Real-time progress implementation
- Days 3-4: Performance optimization and caching
- Day 5: Error handling and edge cases

## Success Criteria

1. **Functional Requirements**
   - Users can upload images and generate meshes
   - Mesh generation completes within 30 seconds for typical images
   - Progress updates every 2-3 seconds during processing
   - Generated meshes are Spine-compatible

2. **Non-functional Requirements**
   - 99.9% uptime for mesh service
   - Horizontal scalability support
   - Comprehensive error handling
   - Full audit trail for all operations

## Dependencies

- Python 3.11+ with FastAPI framework
- OpenCV and Triangle libraries for mesh processing
- Redis for queuing and pub/sub
- PostgreSQL for metadata storage
- Active Storage or S3 for file management