# Rails-Python Service Communication Architecture

## Overview

SpineLift uses a microservice architecture where Rails serves as the main web application and Python handles computationally intensive mesh generation tasks. This document details how these services communicate.

## Communication Flow

### 1. Service Architecture
```
┌─────────────────┐     HTTP/REST      ┌──────────────────┐
│                 │ ◄─────────────────► │                  │
│   Rails App     │                     │  Python Service  │
│   (Port 3000)   │     Callbacks       │   (Port 8000)    │
│                 │ ◄─────────────────  │                  │
└─────────────────┘                     └──────────────────┘
         │                                        │
         └──────────── Redis Queue ──────────────┘
                    (Async Jobs)
```

## Communication Methods

### 1. Direct HTTP Communication

#### Rails → Python: PSD Processing
```ruby
# app/services/psd_processing_service.rb
class PsdProcessingService
  def self.extract_layers(project)
    url = URI.parse("#{base_url}/api/extract_layers")
    
    File.open(temp_file.path, 'rb') do |file|
      req = Net::HTTP::Post::Multipart.new(url.path,
        'psd_file' => UploadIO.new(file, 'image/vnd.adobe.photoshop'),
        'project_id' => project.id.to_s,
        'callback_url' => callback_url(project)
      )
      
      response = Net::HTTP.start(url.host, url.port) do |http|
        http.read_timeout = 120
        http.request(req)
      end
    end
  end
end
```

#### Python Response Format
```python
# Python service response
{
    "layers": [
        {
            "name": "Layer 1",
            "image_data": "base64_encoded_png",
            "position": 0,
            "bounds": {"x": 0, "y": 0, "width": 512, "height": 512},
            "opacity": 1.0,
            "blend_mode": "normal",
            "metadata": {
                "visible": true,
                "has_mask": false
            }
        }
    ]
}
```

### 2. Mesh Generation Communication

#### Rails Request
```ruby
# app/services/mesh_generation_service.rb
class MeshGenerationService
  include HTTParty
  base_uri ENV.fetch('PYTHON_SERVICE_URL', 'http://localhost:8000')
  
  def self.generate_for_layer(layer, parameters = nil, job_id = nil)
    callback_url = Rails.application.routes.url_helpers.api_v1_mesh_progress_url(
      host: ENV['APP_HOST'] || 'localhost:3000'
    )
    
    response = post('/api/generate_mesh',
      body: {
        image_url: layer.image_url,
        parameters: parameters,
        callback_url: callback_url,
        job_id: job_id
      }.to_json,
      headers: { 'Content-Type' => 'application/json' },
      timeout: 60
    )
  end
end
```

#### Python Processing
```python
# main.py
@app.post("/api/generate_mesh")
async def generate_mesh(request: MeshGenerationRequest):
    # Extract parameters
    params = request.parameters.dict()
    
    # Generate mesh
    mesh_data = await mesh_service.generate_mesh_from_url(
        image_url=request.image_url,
        parameters=params,
        callback_url=request.callback_url,
        job_id=request.job_id
    )
    
    return {"mesh": mesh_data}
```

### 3. Progress Callbacks

#### Python → Rails: Progress Updates
```python
# Python service sending progress
async def send_progress_callback(callback_url: str, project_id: int, current: int, total: int):
    async with httpx.AsyncClient() as client:
        await client.post(callback_url, json={
            "project_id": project_id,
            "event": "progress",
            "current": current,
            "total": total,
            "progress": round((current / total) * 100)
        })
```

#### Rails Receiving Callbacks
```ruby
# app/controllers/api/v1/mesh_progress_controller.rb
class Api::V1::MeshProgressController < Api::V1::BaseController
  skip_before_action :authenticate_user!
  
  def create
    project = Project.find(params[:project_id])
    
    # Broadcast progress via ActionCable
    ActionCable.server.broadcast(
      "project_#{project.id}",
      {
        event: params[:event],
        progress: params[:progress],
        message: params[:message]
      }
    )
    
    head :ok
  end
end
```

## Background Job Integration

### 1. Sidekiq Job Processing
```ruby
# app/jobs/process_psd_job.rb
class ProcessPsdJob < ApplicationJob
  queue_as :default
  
  def perform(project_id)
    project = Project.find(project_id)
    
    begin
      # Update status
      project.update!(
        status: :processing,
        processing_started_at: Time.current
      )
      
      # Call Python service
      layers_data = PsdProcessingService.extract_layers(project)
      
      # Process each layer
      layers_data.each_with_index do |layer_data, index|
        layer = create_layer(project, layer_data, index)
        
        # Queue mesh generation
        GenerateMeshJob.perform_later(layer.id)
      end
      
      project.update!(status: :completed)
      
    rescue => e
      project.update!(
        status: :failed,
        error_message: e.message
      )
      raise
    end
  end
end
```

### 2. Mesh Generation Job
```ruby
# app/jobs/generate_mesh_job.rb
class GenerateMeshJob < ApplicationJob
  queue_as :mesh_generation
  
  def perform(layer_id)
    layer = Layer.find(layer_id)
    
    begin
      layer.update!(status: :processing)
      
      # Generate unique job ID for tracking
      job_id = "mesh_#{layer.id}_#{SecureRandom.hex(8)}"
      
      # Call Python service
      mesh_data = MeshGenerationService.generate_for_layer(
        layer,
        layer.mesh_parameters,
        job_id
      )
      
      # Create or update mesh record
      mesh = layer.mesh || layer.build_mesh
      mesh.update!(
        data: mesh_data,
        parameters: layer.mesh_parameters
      )
      
      layer.update!(status: :completed)
      
    rescue => e
      layer.update!(
        status: :failed,
        error_message: e.message
      )
      raise
    end
  end
end
```

## Real-time Updates via ActionCable

### 1. Channel Setup
```ruby
# app/channels/project_channel.rb
class ProjectChannel < ApplicationCable::Channel
  def subscribed
    project = Project.find(params[:project_id])
    stream_for project
  end
  
  def unsubscribed
    stop_all_streams
  end
end
```

### 2. Broadcasting Updates
```ruby
# app/models/project.rb
class Project < ApplicationRecord
  after_update_commit :broadcast_update
  
  private
  
  def broadcast_update
    ProjectChannel.broadcast_to(
      self,
      {
        event: 'project_updated',
        project: ProjectSerializer.new(self).serializable_hash
      }
    )
  end
end
```

## Error Handling

### 1. Network Errors
```ruby
class MeshGenerationService
  def self.generate_for_layer(layer, parameters = nil, job_id = nil)
    # ... request setup ...
    
  rescue HTTParty::Error => e
    Rails.logger.error "Network error calling Python service: #{e.message}"
    raise MeshGenerationError, "Network error: #{e.message}"
  rescue StandardError => e
    Rails.logger.error "Unexpected error: #{e.message}"
    raise MeshGenerationError, "Unexpected error: #{e.message}"
  end
end
```

### 2. Python Service Errors
```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )
```

## Service Discovery & Configuration

### 1. Environment Configuration
```yaml
# config/application.yml
development:
  PYTHON_SERVICE_URL: "http://localhost:8000"
  APP_HOST: "localhost:3000"

production:
  PYTHON_SERVICE_URL: "http://python-service:8000"
  APP_HOST: "api.spinelift.com"
```

### 2. Docker Compose Setup
```yaml
# docker-compose.yml
version: '3.8'

services:
  rails:
    build: .
    environment:
      - PYTHON_SERVICE_URL=http://python:8000
    depends_on:
      - python
      - redis
      - postgres
    
  python:
    build: ./python_service
    environment:
      - RAILS_CALLBACK_URL=http://rails:3000/api/v1
    ports:
      - "8000:8000"
```

## Performance Optimizations

### 1. Connection Pooling
```ruby
# config/initializers/httparty.rb
HTTParty::Basement.default_options.update(
  timeout: 30,
  maintain_method_across_redirects: true,
  headers: {
    'User-Agent' => 'SpineLift Rails Client/1.0'
  }
)
```

### 2. Retry Logic
```ruby
class PythonServiceClient
  include Retriable
  
  def call_service(endpoint, payload)
    retriable(
      on: [Net::ReadTimeout, HTTParty::Error],
      tries: 3,
      base_interval: 1,
      multiplier: 2
    ) do
      HTTParty.post("#{base_url}#{endpoint}", 
        body: payload.to_json,
        headers: headers
      )
    end
  end
end
```

## Monitoring & Logging

### 1. Request Logging
```ruby
# app/services/base_service.rb
class BaseService
  def log_request(url, payload)
    Rails.logger.info({
      service: 'python_mesh_service',
      action: 'request',
      url: url,
      payload_size: payload.to_json.bytesize,
      timestamp: Time.current
    }.to_json)
  end
  
  def log_response(url, response, duration)
    Rails.logger.info({
      service: 'python_mesh_service',
      action: 'response',
      url: url,
      status: response.code,
      duration: duration,
      timestamp: Time.current
    }.to_json)
  end
end
```

### 2. Health Checks
```ruby
# app/controllers/health_controller.rb
class HealthController < ApplicationController
  def show
    checks = {
      database: check_database,
      redis: check_redis,
      python_service: check_python_service
    }
    
    if checks.values.all?
      render json: { status: 'healthy', checks: checks }
    else
      render json: { status: 'unhealthy', checks: checks }, status: :service_unavailable
    end
  end
  
  private
  
  def check_python_service
    response = HTTParty.get("#{ENV['PYTHON_SERVICE_URL']}/health", timeout: 5)
    response.success?
  rescue
    false
  end
end
```

## Security Considerations

### 1. API Key Authentication
```ruby
# Inter-service authentication
class PythonServiceClient
  def headers
    {
      'Content-Type' => 'application/json',
      'X-Service-Token' => ENV['INTER_SERVICE_TOKEN']
    }
  end
end
```

### 2. Request Validation
```python
# Python service validation
async def validate_service_token(request: Request):
    token = request.headers.get("X-Service-Token")
    if token != os.getenv("INTER_SERVICE_TOKEN"):
        raise HTTPException(status_code=401, detail="Invalid service token")
```

## Best Practices

1. **Idempotency**: Make operations idempotent using job IDs
2. **Timeouts**: Set appropriate timeouts for different operations
3. **Circuit Breakers**: Implement circuit breakers for service failures
4. **Async Processing**: Use background jobs for long-running tasks
5. **Logging**: Comprehensive logging for debugging
6. **Monitoring**: Track service health and performance metrics