# PSD Processing Pipeline - Technical Specification

## Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Browser   │────▶│ Rails API   │────▶│   Sidekiq   │────▶│Python Service│
│             │◀────│             │◀────│   Worker    │◀────│   (FastAPI) │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                            │                    │
                            ▼                    ▼
                    ┌─────────────┐     ┌─────────────┐
                    │ PostgreSQL  │     │    Redis    │
                    └─────────────┘     └─────────────┘
```

## Data Models

### 1. Update Project Model
```ruby
# app/models/project.rb
class Project < ApplicationRecord
  # Existing code...
  
  # Add processing metadata
  # migration: add_processing_metadata_to_projects
  # t.integer :total_layers_count, default: 0
  # t.integer :processed_layers_count, default: 0
  # t.string :error_message
  # t.datetime :processing_started_at
  # t.datetime :processing_completed_at
  
  def processing_progress
    return 0 if total_layers_count.zero?
    (processed_layers_count.to_f / total_layers_count * 100).round
  end
end
```

### 2. Update Layer Model
```ruby
# app/models/layer.rb
class Layer < ApplicationRecord
  # Existing code...
  
  # Add metadata fields
  # migration: add_metadata_to_layers
  # t.integer :width
  # t.integer :height
  # t.integer :x_offset
  # t.integer :y_offset
  # t.float :opacity, default: 1.0
  # t.string :blend_mode
  # t.jsonb :psd_metadata, default: {}
end
```

### 3. Create ProcessingLog Model
```ruby
# app/models/processing_log.rb
class ProcessingLog < ApplicationRecord
  belongs_to :project
  
  # migration: create_processing_logs
  # t.references :project, null: false
  # t.string :step
  # t.string :status
  # t.text :message
  # t.jsonb :metadata, default: {}
  # t.timestamps
  
  enum status: {
    started: 0,
    in_progress: 1,
    completed: 2,
    failed: 3
  }
end
```

## API Endpoints

### 1. Project Processing Status
```ruby
# GET /api/v1/projects/:id/processing_status
{
  "data": {
    "id": "123",
    "type": "processing_status",
    "attributes": {
      "status": "processing",
      "progress": 45,
      "current_step": "Extracting layer 3 of 7",
      "total_layers": 7,
      "processed_layers": 3,
      "started_at": "2025-01-08T10:00:00Z",
      "logs": [
        {
          "step": "validation",
          "status": "completed",
          "message": "PSD file validated successfully",
          "timestamp": "2025-01-08T10:00:01Z"
        }
      ]
    }
  }
}
```

### 2. Cancel Processing
```ruby
# POST /api/v1/projects/:id/cancel_processing
{
  "data": {
    "id": "123",
    "type": "project",
    "attributes": {
      "status": "cancelled"
    }
  }
}
```

## Service Architecture

### 1. Updated PsdProcessingService
```ruby
# app/services/psd_processing_service.rb
class PsdProcessingService
  include HTTParty
  base_uri ENV.fetch('PYTHON_SERVICE_URL', 'http://localhost:8001')
  
  def self.extract_layers(project)
    return [] unless project.psd_file.attached?
    
    # Download file to temporary location
    temp_file = download_to_temp(project.psd_file)
    
    begin
      # Send to Python service with multipart encoding
      response = post('/api/extract_layers',
        multipart: true,
        body: {
          psd_file: File.open(temp_file.path, 'rb'),
          project_id: project.id,
          callback_url: callback_url(project)
        },
        timeout: 120
      )
      
      handle_response(response, project)
    ensure
      temp_file.close
      temp_file.unlink
    end
  end
  
  private
  
  def self.download_to_temp(attachment)
    temp_file = Tempfile.new(['psd', '.psd'])
    attachment.download { |chunk| temp_file.write(chunk) }
    temp_file.rewind
    temp_file
  end
  
  def self.callback_url(project)
    Rails.application.routes.url_helpers.api_v1_project_processing_callback_url(
      project,
      host: ENV.fetch('RAILS_HOST', 'localhost:3000')
    )
  end
  
  def self.handle_response(response, project)
    if response.success?
      response.parsed_response['layers']
    else
      raise PsdProcessingError, response.parsed_response['error'] || 'Unknown error'
    end
  end
end
```

### 2. Updated ProcessPsdJob
```ruby
# app/jobs/process_psd_job.rb
class ProcessPsdJob < ApplicationJob
  queue_as :default
  
  def perform(project_id)
    project = Project.find(project_id)
    processor = PsdProcessor.new(project)
    processor.execute
  rescue StandardError => e
    handle_error(project, e)
  end
  
  private
  
  def handle_error(project, error)
    project.update!(
      status: :failed,
      error_message: error.message
    )
    
    ProcessingLog.create!(
      project: project,
      step: 'processing',
      status: :failed,
      message: error.message,
      metadata: { backtrace: error.backtrace.first(10) }
    )
    
    ProjectChannel.broadcast_to(project, {
      event: 'processing_failed',
      error: error.message
    })
  end
end
```

### 3. New PsdProcessor Service
```ruby
# app/services/psd_processor.rb
class PsdProcessor
  attr_reader :project
  
  def initialize(project)
    @project = project
  end
  
  def execute
    log_step('validation', :started)
    validate_psd_file
    
    log_step('processing', :started)
    project.update!(
      status: :processing,
      processing_started_at: Time.current
    )
    
    broadcast_status('Processing started')
    
    # Extract layers from PSD
    log_step('extraction', :started)
    layers_data = PsdProcessingService.extract_layers(project)
    
    project.update!(total_layers_count: layers_data.count)
    
    # Process each layer
    layers_data.each_with_index do |layer_data, index|
      process_layer(layer_data, index)
      project.increment!(:processed_layers_count)
      broadcast_progress
    end
    
    # Mark as completed
    complete_processing
  end
  
  private
  
  def validate_psd_file
    raise "No PSD file attached" unless project.psd_file.attached?
    raise "Invalid file type" unless project.psd_file.content_type == 'image/vnd.adobe.photoshop'
    raise "File too large" if project.psd_file.byte_size > 500.megabytes
  end
  
  def process_layer(layer_data, position)
    layer = project.layers.create!(
      name: layer_data['name'],
      position: position,
      status: :pending,
      width: layer_data['width'],
      height: layer_data['height'],
      x_offset: layer_data['bounds']['x'],
      y_offset: layer_data['bounds']['y'],
      psd_metadata: layer_data['metadata'] || {}
    )
    
    # Attach layer image
    if layer_data['image_data'].present?
      attach_layer_image(layer, layer_data['image_data'])
    end
    
    # Queue mesh generation
    GenerateMeshJob.perform_later(layer.id)
    
    log_step("layer_#{position}", :completed, "Processed layer: #{layer.name}")
  end
  
  def attach_layer_image(layer, image_data)
    # Decode base64 image data
    decoded = Base64.decode64(image_data)
    
    # Create temp file
    temp_file = Tempfile.new(['layer', '.png'])
    temp_file.binmode
    temp_file.write(decoded)
    temp_file.rewind
    
    # Attach to layer
    layer.image.attach(
      io: temp_file,
      filename: "#{layer.name}.png",
      content_type: 'image/png'
    )
    
    temp_file.close
    temp_file.unlink
  end
  
  def complete_processing
    project.update!(
      status: :completed,
      processing_completed_at: Time.current
    )
    
    log_step('processing', :completed)
    broadcast_status('Processing completed')
  end
  
  def log_step(step, status, message = nil)
    ProcessingLog.create!(
      project: project,
      step: step,
      status: status,
      message: message || "#{step} #{status}"
    )
  end
  
  def broadcast_status(message)
    ProjectChannel.broadcast_to(project, {
      event: 'status_update',
      status: project.status,
      message: message
    })
  end
  
  def broadcast_progress
    ProjectChannel.broadcast_to(project, {
      event: 'progress_update',
      progress: project.processing_progress,
      processed: project.processed_layers_count,
      total: project.total_layers_count
    })
  end
end
```

## Frontend Components

### 1. ProcessingStatus Component
```typescript
// frontend/src/components/ProcessingStatus.tsx
import React, { useEffect, useState } from 'react';
import { projectsApi } from '../lib/api';
import { useWebSocket } from '../hooks/useWebSocket';

interface ProcessingStatusProps {
  projectId: string;
}

export const ProcessingStatus: React.FC<ProcessingStatusProps> = ({ projectId }) => {
  const [status, setStatus] = useState<any>(null);
  const [progress, setProgress] = useState(0);
  
  // Subscribe to WebSocket updates
  useWebSocket(`projects:${projectId}`, (message) => {
    if (message.event === 'progress_update') {
      setProgress(message.progress);
    } else if (message.event === 'status_update') {
      setStatus(message);
    }
  });
  
  useEffect(() => {
    // Fetch initial status
    projectsApi.getProcessingStatus(projectId).then(setStatus);
  }, [projectId]);
  
  if (!status) return null;
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-medium mb-4">Processing Status</h3>
      
      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>{status.current_step}</span>
          <span>{progress}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
      
      {/* Status Logs */}
      <div className="space-y-2 max-h-48 overflow-y-auto">
        {status.logs?.map((log, index) => (
          <div key={index} className="flex items-center text-sm">
            <StatusIcon status={log.status} />
            <span className="ml-2">{log.message}</span>
            <span className="ml-auto text-gray-500">
              {new Date(log.timestamp).toLocaleTimeString()}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
```

### 2. WebSocket Hook
```typescript
// frontend/src/hooks/useWebSocket.ts
import { useEffect, useRef } from 'react';
import { createConsumer } from '@rails/actioncable';

export function useWebSocket(channel: string, onMessage: (data: any) => void) {
  const cable = useRef(null);
  const subscription = useRef(null);
  
  useEffect(() => {
    // Create cable connection
    cable.current = createConsumer(
      `${import.meta.env.VITE_WS_URL}/cable`
    );
    
    // Subscribe to channel
    subscription.current = cable.current.subscriptions.create(
      { channel: 'ProjectChannel', project_id: channel.split(':')[1] },
      {
        received: onMessage,
        connected: () => console.log('WebSocket connected'),
        disconnected: () => console.log('WebSocket disconnected')
      }
    );
    
    return () => {
      subscription.current?.unsubscribe();
      cable.current?.disconnect();
    };
  }, [channel]);
}
```

## Python Service Updates

### 1. Updated Extract Layers Endpoint
```python
# python_service/main.py
@app.post("/api/extract_layers")
async def extract_layers(
    psd_file: UploadFile = File(...),
    project_id: int = Form(...),
    callback_url: str = Form(None)
):
    """Extract layers with progress callbacks"""
    try:
        # Save uploaded file
        temp_path = save_temp_file(psd_file)
        
        # Open PSD
        psd = psd_tools.PSDImage.open(temp_path)
        total_layers = len(list(psd.descendants()))
        
        layers = []
        
        # Extract each layer
        for index, layer in enumerate(psd.descendants()):
            if layer.is_visible() and hasattr(layer, 'topil'):
                layer_data = extract_layer(layer, index)
                layers.append(layer_data)
                
                # Send progress callback
                if callback_url:
                    await send_progress_callback(
                        callback_url,
                        project_id,
                        index + 1,
                        total_layers
                    )
        
        # Cleanup
        os.unlink(temp_path)
        
        return {"layers": layers}
        
    except Exception as e:
        logger.error(f"Error extracting layers: {str(e)}")
        if callback_url:
            await send_error_callback(callback_url, project_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))

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
```

## Database Migrations

### 1. Add Processing Metadata to Projects
```ruby
class AddProcessingMetadataToProjects < ActiveRecord::Migration[7.0]
  def change
    add_column :projects, :total_layers_count, :integer, default: 0
    add_column :projects, :processed_layers_count, :integer, default: 0
    add_column :projects, :error_message, :string
    add_column :projects, :processing_started_at, :datetime
    add_column :projects, :processing_completed_at, :datetime
    
    add_index :projects, :status
  end
end
```

### 2. Add Metadata to Layers
```ruby
class AddMetadataToLayers < ActiveRecord::Migration[7.0]
  def change
    add_column :layers, :width, :integer
    add_column :layers, :height, :integer
    add_column :layers, :x_offset, :integer
    add_column :layers, :y_offset, :integer
    add_column :layers, :opacity, :float, default: 1.0
    add_column :layers, :blend_mode, :string
    add_column :layers, :psd_metadata, :jsonb, default: {}
    
    add_index :layers, :position
  end
end
```

### 3. Create Processing Logs
```ruby
class CreateProcessingLogs < ActiveRecord::Migration[7.0]
  def change
    create_table :processing_logs do |t|
      t.references :project, null: false, foreign_key: true
      t.string :step
      t.string :status
      t.text :message
      t.jsonb :metadata, default: {}
      t.timestamps
    end
    
    add_index :processing_logs, [:project_id, :created_at]
  end
end
```

## Configuration Updates

### 1. Redis Configuration
```ruby
# config/initializers/sidekiq.rb
Sidekiq.configure_server do |config|
  config.redis = { url: ENV.fetch('REDIS_URL', 'redis://localhost:6379/0') }
end

Sidekiq.configure_client do |config|
  config.redis = { url: ENV.fetch('REDIS_URL', 'redis://localhost:6379/0') }
end
```

### 2. ActionCable Configuration
```ruby
# config/cable.yml
development:
  adapter: redis
  url: <%= ENV.fetch("REDIS_URL") { "redis://localhost:6379/1" } %>

production:
  adapter: redis
  url: <%= ENV.fetch("REDIS_URL") { "redis://localhost:6379/1" } %>
  channel_prefix: spinelift_production
```

### 3. Environment Variables
```bash
# .env
PYTHON_SERVICE_URL=http://localhost:8001
REDIS_URL=redis://localhost:6379
RAILS_HOST=localhost:3000
```