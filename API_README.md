# SpineLift Rails API

This is the backend API for SpineLift, a web-based tool for converting PSD files to Spine 2D animations.

## Setup

1. Copy `.env.example` to `.env` and fill in your configuration:
   ```bash
   cp .env.example .env
   ```

2. Install dependencies:
   ```bash
   bundle install
   ```

3. Setup database:
   ```bash
   rails db:create db:migrate
   ```

4. Start services with Docker Compose:
   ```bash
   docker-compose up
   ```

Or run services individually:
- Rails server: `rails server`
- Sidekiq: `bundle exec sidekiq`
- Python service: `cd python_service && uvicorn main:app --reload`

## API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user

### Projects

- `GET /api/v1/projects` - List all projects
- `POST /api/v1/projects` - Create new project (with PSD file)
- `GET /api/v1/projects/:id` - Get project details
- `PUT /api/v1/projects/:id` - Update project
- `DELETE /api/v1/projects/:id` - Delete project

### Layers

- `GET /api/v1/projects/:project_id/layers` - List project layers
- `GET /api/v1/projects/:project_id/layers/:id` - Get layer details
- `PUT /api/v1/projects/:project_id/layers/:id` - Update layer

### Meshes

- `GET /api/v1/projects/:project_id/layers/:layer_id/mesh` - Get layer mesh
- `PUT /api/v1/projects/:project_id/layers/:layer_id/mesh` - Update mesh parameters

## WebSocket Channels

- `ProjectChannel` - Subscribe to project updates
- `LayerChannel` - Subscribe to layer/mesh updates

## Testing

Run tests with:
```bash
bundle exec rspec
```