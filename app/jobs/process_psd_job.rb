class ProcessPsdJob < ApplicationJob
  queue_as :default
  
  # Retry configuration
  retry_on StandardError, wait: :exponentially_longer, attempts: 3 do |job, error|
    project_id = job.arguments.first
    if project_id && Project.exists?(project_id)
      project = Project.find(project_id)
      project.fail_processing!("Job failed after 3 attempts: #{error.message}")
      project.broadcast_status_update
    end
  end
  
  # Ensure project status is updated even if job fails
  discard_on ActiveJob::DeserializationError do |job, error|
    project_id = job.arguments.first
    if project_id && Project.exists?(project_id)
      project = Project.find(project_id)
      project.fail_processing!("Job deserialization failed: #{error.message}")
      project.broadcast_status_update
    end
  end
  
  def perform(project_id)
    project = Project.find(project_id)
    
    # Skip if project is not in pending state
    return unless project.pending?
    
    # Log job start
    Rails.logger.info "Starting PSD processing for project #{project_id}"
    
    # Use PsdProcessingService to handle the processing
    service = PsdProcessingService.new(project)
    result = service.call
    
    if result[:success]
      Rails.logger.info "Successfully processed PSD for project #{project_id}"
      # Success notification is handled by the service
    else
      Rails.logger.error "Failed to process PSD for project #{project_id}: #{result[:error]}"
      # Error handling is done in the service
    end
    
    result
  rescue ActiveRecord::RecordNotFound => e
    Rails.logger.error "Project #{project_id} not found: #{e.message}"
    raise
  rescue StandardError => e
    Rails.logger.error "Unexpected error processing project #{project_id}: #{e.class} - #{e.message}"
    Rails.logger.error e.backtrace.join("\n")
    
    # Update project status if possible
    begin
      project = Project.find(project_id)
      project.fail_processing!("Unexpected error: #{e.message}")
      project.broadcast_status_update
    rescue
      # If we can't update the project, just log it
      Rails.logger.error "Could not update project status for #{project_id}"
    end
    
    # Re-raise for ActiveJob retry mechanism
    raise
  end
end