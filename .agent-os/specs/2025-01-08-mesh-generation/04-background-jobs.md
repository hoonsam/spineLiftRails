# Background Jobs Implementation Specification

## Overview

This document specifies the Sidekiq background jobs that handle asynchronous mesh generation, cleanup, notifications, and related tasks.

## Job Architecture

```
app/jobs/
├── mesh/
│   ├── generation_job.rb         # Main mesh generation job
│   ├── cleanup_job.rb           # Failed job cleanup
│   ├── retry_job.rb             # Retry failed generations
│   └── batch_generation_job.rb  # Batch processing
├── storage/
│   ├── cleanup_job.rb           # Clean orphaned files
│   └── thumbnail_generation_job.rb # Generate mesh previews
└── notifications/
    ├── mesh_completion_job.rb   # Success notifications
    └── mesh_failure_job.rb      # Failure notifications
```

## Core Jobs Implementation

### 1. MeshGenerationJob

```ruby
# app/jobs/mesh/generation_job.rb
module Mesh
  class GenerationJob < ApplicationJob
    queue_as :mesh_generation
    
    # Retry configuration
    retry_on Mesh::ServiceError, wait: :exponentially_longer, attempts: 3
    retry_on Net::ReadTimeout, wait: 30.seconds, attempts: 5
    
    # Ensure cleanup on failure
    discard_on ActiveJob::DeserializationError do |job, error|
      handle_deserialization_error(job, error)
    end
    
    # Performance optimizations
    before_perform :check_resource_availability
    around_perform :track_performance
    after_perform :cleanup_temporary_files
    
    def perform(mesh_id:, image_url:, parameters:)
      @mesh = Mesh.find(mesh_id)
      @progress_tracker = ProgressTracker.new(@mesh)
      
      # Update status
      @progress_tracker.update(
        progress: 0,
        message: 'Starting mesh generation...',
        status: 'processing'
      )
      
      # Call Python service
      result = call_python_service(image_url, parameters)
      
      # Process result
      process_result(result)
      
      # Mark as completed
      @progress_tracker.mark_completed(result_url: @mesh.result_url)
      
    rescue StandardError => e
      handle_error(e)
      raise # Re-raise to trigger retry
    end
    
    private
    
    def call_python_service(image_url, parameters)
      client = PythonClient.new
      
      # Start generation with callback
      response = client.generate_mesh(
        image_url: image_url,
        parameters: parameters,
        job_id: @mesh.job_id,
        callback_url: callback_url
      )
      
      # Poll for completion if needed
      if response[:status] == 'processing'
        poll_for_completion(client)
      else
        response
      end
    end
    
    def poll_for_completion(client)
      timeout = 5.minutes.from_now
      
      loop do
        sleep 2 # Poll every 2 seconds
        
        status = client.get_status(@mesh.job_id)
        
        case status[:status]
        when 'completed'
          return fetch_result(status[:result_url])
        when 'failed'
          raise GenerationError, status[:message]
        when 'processing'
          # Continue polling
          if Time.current > timeout
            raise TimeoutError, 'Mesh generation timed out'
          end
        end
      end
    end
    
    def fetch_result(result_url)
      response = HTTParty.get(result_url)
      JSON.parse(response.body, symbolize_names: true)
    end
    
    def process_result(result)
      ResultProcessor.new(@mesh, result).process!
    end
    
    def handle_error(error)
      ErrorHandler.handle(error, mesh: @mesh)
      
      @progress_tracker.mark_failed(
        error_message: error.message
      )
      
      # Queue cleanup job
      CleanupJob.perform_later(mesh_id: @mesh.id)
      
      # Send failure notification
      Notifications::MeshFailureJob.perform_later(mesh_id: @mesh.id)
    end
    
    def check_resource_availability
      # Check Python service health
      unless PythonClient.new.health_check
        raise ServiceError, 'Python mesh service is unavailable'
      end
      
      # Check Redis availability
      Redis.new.ping
      
    rescue StandardError => e
      Rails.logger.error "Resource check failed: #{e.message}"
      raise ServiceError, 'Required services are unavailable'
    end
    
    def track_performance(&block)
      start_time = Time.current
      
      yield
      
      duration = Time.current - start_time
      
      # Log performance metrics
      Rails.logger.info(
        'Mesh generation completed',
        mesh_id: @mesh.id,
        duration: duration,
        vertex_count: @mesh.vertex_count,
        triangle_count: @mesh.triangle_count
      )
      
      # Send metrics to monitoring
      StatsD.timing('mesh.generation.duration', duration)
      StatsD.increment('mesh.generation.success')
      
    rescue StandardError => e
      StatsD.increment('mesh.generation.failure')
      raise
    end
    
    def cleanup_temporary_files
      # Clean up any temporary files created during processing
      temp_dir = Rails.root.join('tmp', 'mesh_generation', @mesh.job_id)
      FileUtils.rm_rf(temp_dir) if temp_dir.exist?
    end
    
    def callback_url
      Rails.application.routes.url_helpers.api_mesh_callback_url(
        job_id: @mesh.job_id,
        host: ENV['APP_HOST']
      )
    end
  end
end
```

### 2. CleanupJob

```ruby
# app/jobs/mesh/cleanup_job.rb
module Mesh
  class CleanupJob < ApplicationJob
    queue_as :low_priority
    
    def perform(mesh_id: nil, older_than: nil)
      if mesh_id
        cleanup_single_mesh(mesh_id)
      elsif older_than
        cleanup_old_meshes(older_than)
      else
        cleanup_orphaned_files
      end
    end
    
    private
    
    def cleanup_single_mesh(mesh_id)
      mesh = Mesh.find_by(id: mesh_id)
      return unless mesh&.failed?
      
      # Remove associated files
      Storage::MeshStorageService.new(mesh).delete_all
      
      # Remove temporary processing files
      cleanup_temp_files(mesh.job_id)
      
      # Mark as cleaned
      mesh.update(cleaned_up: true)
      
      Rails.logger.info "Cleaned up failed mesh: #{mesh_id}"
    end
    
    def cleanup_old_meshes(older_than)
      cutoff_date = older_than.ago
      
      Mesh.failed
          .where('created_at < ?', cutoff_date)
          .where(cleaned_up: false)
          .find_each do |mesh|
        
        CleanupJob.perform_later(mesh_id: mesh.id)
      end
    end
    
    def cleanup_orphaned_files
      storage_service = Storage::MeshStorageService.new
      
      # Get all files in storage
      all_files = storage_service.list_all_files
      
      # Get all referenced files
      referenced_files = Mesh.pluck(:result_url).compact
      
      # Find orphaned files
      orphaned_files = all_files - referenced_files
      
      Rails.logger.info "Found #{orphaned_files.count} orphaned files"
      
      # Delete orphaned files
      orphaned_files.each do |file_url|
        storage_service.delete(file_url)
      end
    end
    
    def cleanup_temp_files(job_id)
      temp_dir = Rails.root.join('tmp', 'mesh_generation', job_id)
      FileUtils.rm_rf(temp_dir) if temp_dir.exist?
    end
  end
end
```

### 3. BatchGenerationJob

```ruby
# app/jobs/mesh/batch_generation_job.rb
module Mesh
  class BatchGenerationJob < ApplicationJob
    queue_as :batch_processing
    
    # Limit concurrent batch jobs
    include ActiveJob::Uniqueness
    unique :until_executed, on_conflict: :log
    
    def perform(project_id:, image_ids:, parameters:, user_id:)
      @project = Project.find(project_id)
      @user = User.find(user_id)
      @batch_id = SecureRandom.uuid
      
      # Create batch record
      batch = create_batch_record(image_ids)
      
      # Process images in parallel
      process_images_in_parallel(image_ids, parameters, batch)
      
      # Send completion notification
      notify_batch_completion(batch)
      
    rescue StandardError => e
      handle_batch_error(e, batch)
    end
    
    private
    
    def create_batch_record(image_ids)
      MeshBatch.create!(
        project: @project,
        user: @user,
        batch_id: @batch_id,
        total_images: image_ids.count,
        status: 'processing'
      )
    end
    
    def process_images_in_parallel(image_ids, parameters, batch)
      # Use thread pool for parallel processing
      pool = Concurrent::FixedThreadPool.new(
        ENV.fetch('BATCH_CONCURRENCY', 5).to_i
      )
      
      futures = image_ids.map do |image_id|
        Concurrent::Future.execute(executor: pool) do
          process_single_image(image_id, parameters, batch)
        end
      end
      
      # Wait for all futures to complete
      futures.each(&:wait)
      
      # Update batch status
      successful_count = futures.count { |f| f.fulfilled? }
      batch.update!(
        completed_count: successful_count,
        failed_count: futures.count { |f| f.rejected? },
        status: 'completed',
        completed_at: Time.current
      )
    ensure
      pool.shutdown
      pool.wait_for_termination
    end
    
    def process_single_image(image_id, parameters, batch)
      image = @project.images.find(image_id)
      
      mesh = GenerationService.new(
        project: @project,
        image: image,
        parameters: parameters,
        user: @user
      ).generate_sync!
      
      # Update batch progress
      batch.increment(:completed_count)
      broadcast_batch_progress(batch)
      
      mesh
    rescue StandardError => e
      Rails.logger.error "Batch processing failed for image #{image_id}: #{e.message}"
      batch.increment(:failed_count)
      raise
    end
    
    def broadcast_batch_progress(batch)
      progress = (batch.completed_count.to_f / batch.total_images * 100).round
      
      ActionCable.server.broadcast(
        "batch_progress_#{batch.id}",
        {
          batch_id: batch.batch_id,
          progress: progress,
          completed: batch.completed_count,
          failed: batch.failed_count,
          total: batch.total_images
        }
      )
    end
    
    def notify_batch_completion(batch)
      Notifications::BatchCompletionJob.perform_later(
        batch_id: batch.id,
        user_id: @user.id
      )
    end
    
    def handle_batch_error(error, batch)
      batch&.update!(
        status: 'failed',
        error_message: error.message,
        failed_at: Time.current
      )
      
      Rails.logger.error(
        'Batch generation failed',
        batch_id: batch&.id,
        error: error.message,
        backtrace: error.backtrace.first(10)
      )
    end
  end
end
```

### 4. Progress Callback Job

```ruby
# app/jobs/mesh/progress_callback_job.rb
module Mesh
  class ProgressCallbackJob < ApplicationJob
    queue_as :critical
    
    # Process callbacks immediately
    self.priority = 10
    
    def perform(job_id:, progress:, message:, status: nil)
      mesh = Mesh.find_by!(job_id: job_id)
      progress_tracker = ProgressTracker.new(mesh)
      
      # Update progress
      progress_tracker.update(
        progress: progress,
        message: message,
        status: status
      )
      
      # Handle completion
      if status == 'completed' && progress == 100
        handle_completion(mesh)
      elsif status == 'failed'
        handle_failure(mesh, message)
      end
    end
    
    private
    
    def handle_completion(mesh)
      # Fetch and process result
      result = fetch_result_from_python(mesh.job_id)
      ResultProcessor.new(mesh, result).process!
      
      # Send notification
      Notifications::MeshCompletionJob.perform_later(mesh_id: mesh.id)
    end
    
    def handle_failure(mesh, error_message)
      mesh.update!(
        status: 'failed',
        error_message: error_message,
        failed_at: Time.current
      )
      
      # Queue cleanup
      CleanupJob.set(wait: 1.hour).perform_later(mesh_id: mesh.id)
      
      # Send notification
      Notifications::MeshFailureJob.perform_later(mesh_id: mesh.id)
    end
    
    def fetch_result_from_python(job_id)
      client = PythonClient.new
      status = client.get_status(job_id)
      
      if status[:result_url]
        response = HTTParty.get(status[:result_url])
        JSON.parse(response.body, symbolize_names: true)
      else
        raise GenerationError, 'No result URL provided'
      end
    end
  end
end
```

## Job Configuration

```ruby
# config/sidekiq.yml
:verbose: false
:concurrency: 25
:timeout: 300

:queues:
  - [critical, 10]
  - [mesh_generation, 5]
  - [batch_processing, 3]
  - [default, 2]
  - [low_priority, 1]

:limits:
  mesh_generation: 10  # Max 10 concurrent mesh generations
  batch_processing: 2  # Max 2 concurrent batch jobs

# Cron jobs
:schedule:
  cleanup_old_meshes:
    cron: "0 2 * * *"  # Daily at 2 AM
    class: "Mesh::CleanupJob"
    args:
      older_than: 604800  # 7 days in seconds
  
  cleanup_orphaned_files:
    cron: "0 3 * * 0"  # Weekly on Sunday at 3 AM
    class: "Storage::CleanupJob"
  
  generate_usage_report:
    cron: "0 0 1 * *"  # Monthly on the 1st
    class: "Reports::UsageReportJob"
```

## Monitoring and Alerting

```ruby
# app/jobs/concerns/job_monitoring.rb
module JobMonitoring
  extend ActiveSupport::Concern
  
  included do
    around_perform :monitor_job_execution
  end
  
  private
  
  def monitor_job_execution
    job_name = self.class.name
    start_time = Time.current
    
    StatsD.increment("jobs.#{job_name}.started")
    
    yield
    
    duration = Time.current - start_time
    StatsD.timing("jobs.#{job_name}.duration", duration)
    StatsD.increment("jobs.#{job_name}.success")
    
  rescue StandardError => e
    StatsD.increment("jobs.#{job_name}.failure")
    StatsD.increment("jobs.#{job_name}.error.#{e.class.name}")
    
    # Send alert for critical failures
    if critical_job?
      ErrorReporter.report(e, job: job_name, arguments: arguments)
    end
    
    raise
  end
  
  def critical_job?
    queue_name == 'critical' || self.class.name.include?('Critical')
  end
end
```

## Testing Strategy

```ruby
# spec/jobs/mesh/generation_job_spec.rb
RSpec.describe Mesh::GenerationJob do
  include ActiveJob::TestHelper
  
  describe '#perform' do
    let(:mesh) { create(:mesh, status: 'pending') }
    let(:job_args) do
      {
        mesh_id: mesh.id,
        image_url: 'https://example.com/image.png',
        parameters: { detail_factor: 0.02 }
      }
    end
    
    context 'successful generation' do
      before do
        stub_python_service_success
      end
      
      it 'updates mesh status and processes result' do
        perform_enqueued_jobs do
          described_class.perform_later(**job_args)
        end
        
        mesh.reload
        expect(mesh.status).to eq('completed')
        expect(mesh.result_url).to be_present
      end
    end
    
    context 'when Python service fails' do
      before do
        stub_python_service_failure
      end
      
      it 'retries and eventually marks mesh as failed' do
        perform_enqueued_jobs do
          expect {
            described_class.perform_later(**job_args)
          }.to raise_error(Mesh::ServiceError)
        end
        
        mesh.reload
        expect(mesh.status).to eq('failed')
        expect(mesh.error_message).to be_present
      end
    end
  end
end
```