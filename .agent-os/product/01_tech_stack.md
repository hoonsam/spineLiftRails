# SpineLift Tech Stack Analysis

## Overview
SpineLift is a hybrid web application that converts PSD layers into Spine-compatible 2D mesh animations. It combines a Rails backend with a Python microservice for mesh generation.

## Technology Stack

### Backend Technologies

#### Rails Application (Main Backend)
- **Framework**: Rails 8.0.2
- **Language**: Ruby 3.x
- **Database**: PostgreSQL
- **Background Jobs**: Sidekiq with Redis
- **Authentication**: Devise + JWT for API auth
- **File Storage**: Active Storage with AWS S3
- **WebSocket**: ActionCable for real-time updates
- **Caching**: Solid Cache (database-backed)
- **Queue**: Solid Queue (database-backed)

#### Python Microservice (Mesh Processing)
- **Framework**: FastAPI
- **Language**: Python 3.x
- **Key Libraries**:
  - `psd-tools`: PSD file parsing
  - `opencv-python`: Image processing
  - `numpy`: Numerical computations
  - `triangle`: Delaunay triangulation for mesh generation
  - `Pillow`: Image manipulation
- **Server**: Uvicorn (ASGI)

### Frontend Technologies

#### React Application
- **Framework**: React 19.1.1
- **Build Tool**: Vite
- **Language**: TypeScript
- **State Management**: Zustand
- **API Client**: Axios + React Query
- **Styling**: Tailwind CSS 4.x
- **UI Components**: Custom components with Lucide icons
- **Real-time**: Rails ActionCable integration

### Infrastructure & DevOps

#### Development Environment
- **Container**: Docker & Docker Compose
- **Version Control**: Git
- **Testing**: 
  - Rails: RSpec, Factory Bot, Faker
  - Frontend: Jest (planned)

#### Production Deployment
- **Platform**: Railway (recommended) or Docker
- **CDN**: Cloudflare (optional)
- **Monitoring**: Planned for New Relic/DataDog
- **Error Tracking**: Planned for Sentry

### External Services
- **File Storage**: AWS S3 or compatible (R2, MinIO)
- **Redis**: For caching and Sidekiq
- **SMTP**: For email notifications (optional)

## API Architecture

### RESTful API Endpoints
```
POST   /api/v1/auth/login
POST   /api/v1/auth/register
GET    /api/v1/projects
POST   /api/v1/projects
GET    /api/v1/projects/:id
GET    /api/v1/projects/:id/processing_status
POST   /api/v1/projects/:id/cancel_processing
GET    /api/v1/projects/:id/layers
GET    /api/v1/projects/:id/layers/:id
PATCH  /api/v1/projects/:id/layers/:id
GET    /api/v1/projects/:id/layers/:id/mesh
PATCH  /api/v1/projects/:id/layers/:id/mesh
POST   /api/v1/mesh_progress
```

### WebSocket Channels
- **ProjectChannel**: Real-time project processing updates
- **LayerChannel**: Layer-specific mesh generation progress

## Database Schema

### Core Models
1. **Users**: Authentication and authorization
2. **Projects**: PSD file uploads and processing status
3. **Layers**: Individual PSD layers with metadata
4. **Meshes**: Generated mesh data (vertices, triangles, UVs)
5. **ProcessingLogs**: Audit trail for processing steps

### Storage Strategy
- **Files**: Active Storage with S3 backend
- **Mesh Data**: JSONB fields in PostgreSQL for efficient storage
- **Metadata**: JSONB fields for flexible schema

## Security Features
- JWT-based API authentication
- CORS configuration for API access
- File upload validation (size, type)
- SQL injection protection via ActiveRecord
- XSS protection via React

## Performance Optimizations
- Database-backed caching (Solid Cache)
- Background job processing (Sidekiq)
- Efficient JSONB storage for mesh data
- CDN integration for static assets
- WebSocket for real-time updates (reduces polling)

## Development Tools
- **Code Quality**: Rubocop, ESLint
- **Security**: Brakeman for Rails
- **API Testing**: Postman/Insomnia compatible
- **Database Management**: Rails migrations