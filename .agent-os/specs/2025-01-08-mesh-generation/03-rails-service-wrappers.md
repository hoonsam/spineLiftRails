# Rails Service Wrappers Specification

## Overview

This document specifies the Rails service layer that wraps the Python mesh generation service, providing a clean interface for the Rails application to interact with the FastAPI endpoints.

## Service Architecture

```
app/services/
├── mesh/
│   ├── generation_service.rb      # Main orchestration service
│   ├── parameter_validator.rb     # Input validation
│   ├── python_client.rb          # HTTP client for Python service
│   ├── progress_tracker.rb       # Progress monitoring
│   └── result_processor.rb       # Process and store results
├── storage/
│   ├── image_service.rb          # Image upload/download
│   └── mesh_storage_service.rb   # Mesh file management
└── notifications/
    └── mesh_notification_service.rb  # User notifications
```

## Core Services Implementation

### 1. MeshGenerationService

```ruby
# app/services/mesh/generation_service.rb
module Mesh
  class GenerationService
    include ActiveModel::Model
    
    attr_accessor :project, :image, :parameters, :user
    
    validates :project, :image, :user, presence: true
    
    def initialize(project:, image:, parameters: {}, user:)
      @project = project
      @image = image
      @parameters = parameters
      @user = user
    end
    
    def generate!
      validate!
      
      # Create mesh record
      mesh = create_mesh_record
      
      # Queue background job
      MeshGenerationJob.perform_later(
        mesh_id: mesh.id,
        image_url: image_url,
        parameters: validated_parameters
      )
      
      mesh
    rescue StandardError => e
      handle_generation_error(e)
    end
    
    def generate_sync!
      validate!
      
      mesh = create_mesh_record
      
      # Direct API call for synchronous generation
      result = python_client.generate_mesh(
        image_url: image_url,
        parameters: validated_parameters,
        job_id: mesh.job_id
      )
      
      process_result(mesh, result)
      mesh
    end
    
    private
    
    def create_mesh_record
      project.meshes.create!(
        image: image,
        status: 'pending',
        parameters: validated_parameters,
        job_id: SecureRandom.uuid,
        created_by: user
      )
    end
    
    def validated_parameters
      @validated_parameters ||= ParameterValidator.new(parameters).validate!
    end
    
    def image_url
      @image_url ||= Storage::ImageService.new(image).public_url
    end
    
    def python_client
      @python_client ||= PythonClient.new
    end
    
    def handle_generation_error(error)
      Rails.logger.error "Mesh generation failed: #{error.message}"
      raise GenerationError, "Failed to generate mesh: #{error.message}"
    end
  end
end
```

### 2. ParameterValidator

```ruby
# app/services/mesh/parameter_validator.rb
module Mesh
  class ParameterValidator
    include ActiveModel::Model
    
    PARAMETER_DEFAULTS = {
      detail_factor: 0.01,
      alpha_threshold: 10,
      concave_factor: 0.0,
      internal_vertex_density: 0,
      blur_kernel_size: 1,
      binary_threshold: 128,
      min_contour_area: 10,
      density_scaling_factor: 1000.0,
      min_triangle_area: 1.0
    }.freeze
    
    PARAMETER_RANGES = {
      detail_factor: 0.001..0.050,
      alpha_threshold: 0..255,
      concave_factor: 0.0..100.0,
      internal_vertex_density: 0..100,
      blur_kernel_size: 1..21,
      binary_threshold: 0..255,
      min_contour_area: 1..1000,
      density_scaling_factor: 100..10000,
      min_triangle_area: 0.1..100
    }.freeze
    
    attr_reader :parameters
    
    def initialize(parameters = {})
      @parameters = parameters.symbolize_keys
    end
    
    def validate!
      validated = {}
      
      PARAMETER_DEFAULTS.each do |key, default|
        value = parameters[key] || default
        validated[key] = validate_parameter(key, value)
      end
      
      # Special validation for blur_kernel_size (must be odd)
      if validated[:blur_kernel_size].even?
        validated[:blur_kernel_size] += 1
      end
      
      validated
    end
    
    private
    
    def validate_parameter(key, value)
      range = PARAMETER_RANGES[key]
      
      unless range.include?(value)
        raise ValidationError, "#{key} must be between #{range.min} and #{range.max}"
      end
      
      case value
      when Integer
        value.to_i
      when Float
        value.to_f
      else
        raise ValidationError, "Invalid type for #{key}"
      end
    end
  end
end
```

### 3. PythonClient

```ruby
# app/services/mesh/python_client.rb
module Mesh
  class PythonClient
    include HTTParty
    
    base_uri ENV.fetch('PYTHON_SERVICE_URL', 'http://localhost:8000')
    default_timeout 300 # 5 minutes
    
    def generate_mesh(image_url:, parameters:, job_id:, callback_url: nil)
      response = self.class.post(
        '/api/v1/mesh/generate',
        body: {
          image_url: image_url,
          parameters: parameters,
          job_id: job_id,
          callback_url: callback_url || default_callback_url(job_id)
        }.to_json,
        headers: {
          'Content-Type' => 'application/json',
          'X-Request-ID' => RequestStore[:request_id]
        }
      )
      
      handle_response(response)
    end
    
    def get_status(job_id)
      response = self.class.get(
        "/api/v1/mesh/#{job_id}/status",
        headers: {
          'X-Request-ID' => RequestStore[:request_id]
        }
      )
      
      handle_response(response)
    end
    
    def health_check
      response = self.class.get('/health', timeout: 5)
      response.success?
    rescue StandardError
      false
    end
    
    private
    
    def handle_response(response)
      case response.code
      when 200..299
        JSON.parse(response.body, symbolize_names: true)
      when 400
        raise ValidationError, parse_error_message(response)
      when 404
        raise NotFoundError, parse_error_message(response)
      when 500..599
        raise ServiceError, parse_error_message(response)
      else
        raise UnknownError, "Unexpected response: #{response.code}"
      end
    end
    
    def parse_error_message(response)
      error = JSON.parse(response.body)['error']
      "#{error['code']}: #{error['message']}"
    rescue StandardError
      response.body
    end
    
    def default_callback_url(job_id)
      Rails.application.routes.url_helpers.api_mesh_callback_url(
        job_id: job_id,
        host: ENV['APP_HOST']
      )
    end
  end
end
```

### 4. ProgressTracker

```ruby
# app/services/mesh/progress_tracker.rb
module Mesh
  class ProgressTracker
    attr_reader :mesh, :redis
    
    def initialize(mesh)
      @mesh = mesh
      @redis = Redis.new(url: ENV['REDIS_URL'])
    end
    
    def update(progress:, message:, status: nil)
      data = {
        progress: progress,
        message: message,
        status: status || mesh.status,
        updated_at: Time.current.iso8601
      }
      
      # Update mesh record
      mesh.update!(
        progress: progress,
        status: status || mesh.status,
        last_progress_message: message
      )
      
      # Store in Redis for quick access
      redis.setex(
        progress_key,
        300, # 5 minutes TTL
        data.to_json
      )
      
      # Broadcast to ActionCable
      broadcast_progress(data)
      
      data
    end
    
    def current_progress
      cached = redis.get(progress_key)
      return JSON.parse(cached, symbolize_names: true) if cached
      
      {
        progress: mesh.progress || 0,
        message: mesh.last_progress_message || 'Initializing...',
        status: mesh.status,
        updated_at: mesh.updated_at.iso8601
      }
    end
    
    def mark_completed(result_url:)
      update(
        progress: 100,
        message: 'Mesh generation completed',
        status: 'completed'
      )
      
      mesh.update!(
        result_url: result_url,
        completed_at: Time.current
      )
    end
    
    def mark_failed(error_message:)
      update(
        progress: mesh.progress || 0,
        message: error_message,
        status: 'failed'
      )
      
      mesh.update!(
        error_message: error_message,
        failed_at: Time.current
      )
    end
    
    private
    
    def progress_key
      "mesh_progress:#{mesh.job_id}"
    end
    
    def broadcast_progress(data)
      ActionCable.server.broadcast(
        "mesh_progress_#{mesh.id}",
        data.merge(mesh_id: mesh.id)
      )
    end
  end
end
```

### 5. ResultProcessor

```ruby
# app/services/mesh/result_processor.rb
module Mesh
  class ResultProcessor
    attr_reader :mesh, :result_data
    
    def initialize(mesh, result_data)
      @mesh = mesh
      @result_data = result_data
    end
    
    def process!
      ActiveRecord::Base.transaction do
        # Store mesh data
        store_mesh_file
        
        # Update mesh metadata
        update_mesh_metadata
        
        # Create mesh details record
        create_mesh_details
        
        # Trigger post-processing
        trigger_post_processing
      end
      
      mesh
    end
    
    private
    
    def store_mesh_file
      mesh_json = build_spine_json
      
      storage_service = Storage::MeshStorageService.new(mesh)
      mesh.result_url = storage_service.store(mesh_json)
      mesh.save!
    end
    
    def build_spine_json
      {
        skeleton: {
          hash: mesh.job_id,
          spine: "4.1",
          width: result_data[:metadata][:width],
          height: result_data[:metadata][:height]
        },
        bones: build_bones_data,
        slots: build_slots_data,
        skins: {
          default: {
            "mesh_#{mesh.id}": build_mesh_attachment
          }
        }
      }
    end
    
    def build_bones_data
      [
        {
          name: "root"
        },
        {
          name: "mesh_bone",
          parent: "root",
          x: result_data[:metadata][:width] / 2.0,
          y: result_data[:metadata][:height] / 2.0
        }
      ]
    end
    
    def build_slots_data
      [
        {
          name: "mesh_slot",
          bone: "mesh_bone",
          attachment: "mesh_#{mesh.id}"
        }
      ]
    end
    
    def build_mesh_attachment
      {
        type: "mesh",
        uvs: result_data[:uvs],
        triangles: result_data[:triangles].flatten,
        vertices: offset_vertices,
        hull: result_data[:boundary_indices].size
      }
    end
    
    def offset_vertices
      # Convert to Spine coordinate system (centered)
      width = result_data[:metadata][:width]
      height = result_data[:metadata][:height]
      
      result_data[:vertices].flatten.each_with_index.map do |coord, index|
        if index.even? # X coordinate
          coord - width / 2.0
        else # Y coordinate
          coord - height / 2.0
        end
      end
    end
    
    def update_mesh_metadata
      mesh.update!(
        vertex_count: result_data[:metadata][:vertex_count],
        triangle_count: result_data[:metadata][:triangle_count],
        processing_time: calculate_processing_time
      )
    end
    
    def create_mesh_details
      mesh.create_mesh_detail!(
        vertices: result_data[:vertices],
        triangles: result_data[:triangles],
        uvs: result_data[:uvs],
        boundary_edges: result_data[:boundary_edges],
        internal_edges: result_data[:internal_edges],
        metadata: result_data[:metadata]
      )
    end
    
    def trigger_post_processing
      # Queue thumbnail generation
      ThumbnailGenerationJob.perform_later(mesh.id)
      
      # Send completion notification
      Notifications::MeshNotificationService.new(mesh).send_completion
    end
    
    def calculate_processing_time
      return 0 unless mesh.created_at
      
      (Time.current - mesh.created_at).to_i
    end
  end
end
```

## Error Handling

```ruby
# app/services/mesh/errors.rb
module Mesh
  class Error < StandardError; end
  class ValidationError < Error; end
  class GenerationError < Error; end
  class ServiceError < Error; end
  class NotFoundError < Error; end
  class UnknownError < Error; end
  
  class ErrorHandler
    def self.handle(error, mesh: nil)
      case error
      when ValidationError
        log_validation_error(error, mesh)
      when ServiceError
        log_service_error(error, mesh)
      else
        log_unknown_error(error, mesh)
      end
      
      notify_error(error, mesh) if mesh
    end
    
    private
    
    def self.log_validation_error(error, mesh)
      Rails.logger.error(
        "Mesh validation failed",
        error: error.message,
        mesh_id: mesh&.id,
        backtrace: error.backtrace.first(5)
      )
    end
    
    def self.log_service_error(error, mesh)
      Rails.logger.error(
        "Python service error",
        error: error.message,
        mesh_id: mesh&.id,
        service: 'python_mesh_service'
      )
    end
    
    def self.notify_error(error, mesh)
      ProgressTracker.new(mesh).mark_failed(
        error_message: user_friendly_message(error)
      )
    end
    
    def self.user_friendly_message(error)
      case error
      when ValidationError
        "Invalid parameters: #{error.message}"
      when ServiceError
        "Mesh generation service is temporarily unavailable"
      else
        "An unexpected error occurred during mesh generation"
      end
    end
  end
end
```

## Service Configuration

```ruby
# config/initializers/mesh_services.rb
Rails.application.config.to_prepare do
  # Configure Python service client
  Mesh::PythonClient.configure do |config|
    config.base_uri = ENV.fetch('PYTHON_SERVICE_URL', 'http://localhost:8000')
    config.timeout = ENV.fetch('MESH_GENERATION_TIMEOUT', 300).to_i
    config.retry_count = ENV.fetch('MESH_RETRY_COUNT', 3).to_i
    config.retry_delay = ENV.fetch('MESH_RETRY_DELAY', 1).to_i
  end
  
  # Configure storage services
  Storage::ImageService.configure do |config|
    config.storage_backend = ENV.fetch('STORAGE_BACKEND', 'local')
    config.bucket_name = ENV.fetch('STORAGE_BUCKET', 'spinelift-assets')
  end
end
```

## Testing Approach

```ruby
# spec/services/mesh/generation_service_spec.rb
RSpec.describe Mesh::GenerationService do
  describe '#generate!' do
    it 'creates mesh record and queues job' do
      service = described_class.new(
        project: project,
        image: image,
        parameters: { detail_factor: 0.02 },
        user: user
      )
      
      expect {
        mesh = service.generate!
      }.to change(Mesh, :count).by(1)
        .and have_enqueued_job(MeshGenerationJob)
    end
    
    it 'validates parameters before processing' do
      service = described_class.new(
        project: project,
        image: image,
        parameters: { detail_factor: 999 },
        user: user
      )
      
      expect {
        service.generate!
      }.to raise_error(Mesh::ValidationError)
    end
  end
end
```