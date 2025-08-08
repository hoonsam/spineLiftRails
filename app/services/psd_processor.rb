# Service class for processing PSD files
class PsdProcessor
  attr_reader :project
  
  def initialize(project)
    @project = project
  end
  
  def execute
    log_step('validation', :started, 'Starting PSD validation')
    validate_psd_file
    log_step('validation', :completed, 'PSD validation successful')
    
    log_step('processing', :started, 'Starting PSD processing')
    project.update!(
      status: :processing,
      processing_started_at: Time.current,
      error_message: nil
    )
    
    broadcast_status('Processing started')
    
    # Extract layers from PSD
    log_step('extraction', :started, 'Extracting layers from PSD')
    layers_data = PsdProcessingService.extract_layers(project)
    
    project.update!(total_layers_count: layers_data.count)
    log_step('extraction', :completed, "Found #{layers_data.count} layers")
    
    # Process each layer
    layers_data.each_with_index do |layer_data, index|
      process_layer(layer_data, index)
      project.increment!(:processed_layers_count)
      broadcast_progress
    end
    
    # Mark as completed
    complete_processing
    
  rescue StandardError => e
    handle_error(e)
    raise
  end
  
  private
  
  def validate_psd_file
    raise "No PSD file attached" unless project.psd_file.attached?
    
    # Validate content type
    acceptable_types = ['image/vnd.adobe.photoshop', 'application/octet-stream']
    unless acceptable_types.include?(project.psd_file.content_type)
      raise "Invalid file type: #{project.psd_file.content_type}"
    end
    
    # Validate file size
    max_size = 500.megabytes
    if project.psd_file.byte_size > max_size
      raise "File too large: #{project.psd_file.byte_size / 1.megabyte}MB (max: #{max_size / 1.megabyte}MB)"
    end
  end
  
  def process_layer(layer_data, position)
    layer = project.layers.create!(
      name: layer_data['name'],
      position: position,
      status: :pending,
      width: layer_data['width'],
      height: layer_data['height'],
      x_offset: layer_data['bounds']&.dig('x') || 0,
      y_offset: layer_data['bounds']&.dig('y') || 0,
      opacity: layer_data['opacity'] || 1.0,
      blend_mode: layer_data['blend_mode'] || 'normal',
      psd_metadata: layer_data['metadata'] || {}
    )
    
    # Attach layer image if provided
    if layer_data['image_data'].present?
      attach_layer_image(layer, layer_data['image_data'])
    elsif layer_data['image_path'].present?
      attach_layer_from_path(layer, layer_data['image_path'])
    end
    
    # Queue mesh generation for this layer
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
      filename: "#{layer.name.parameterize}.png",
      content_type: 'image/png'
    )
    
    temp_file.close
    temp_file.unlink
  end
  
  def attach_layer_from_path(layer, image_path)
    # Attach image from file path
    if File.exist?(image_path)
      layer.image.attach(
        io: File.open(image_path),
        filename: "#{layer.name.parameterize}.png",
        content_type: 'image/png'
      )
      
      # Clean up temporary file
      File.delete(image_path) if image_path.include?('/tmp/')
    else
      Rails.logger.warn "Layer image not found: #{image_path}"
    end
  end
  
  def complete_processing
    project.update!(
      status: :completed,
      processing_completed_at: Time.current
    )
    
    log_step('processing', :completed, 'PSD processing completed successfully')
    broadcast_status('Processing completed')
  end
  
  def handle_error(error)
    project.update!(
      status: :failed,
      error_message: error.message,
      processing_completed_at: Time.current
    )
    
    log_step('processing', :failed, "Error: #{error.message}")
    
    Rails.logger.error "PSD processing failed for project #{project.id}: #{error.message}"
    Rails.logger.error error.backtrace.join("\n")
    
    broadcast_status('Processing failed', error: error.message)
  end
  
  def log_step(step, status, message = nil)
    ProcessingLog.create!(
      project: project,
      step: step,
      status: status,
      message: message || "#{step.humanize} #{status}",
      metadata: {
        timestamp: Time.current.iso8601,
        project_id: project.id
      }
    )
  end
  
  def broadcast_status(message, error: nil)
    data = {
      event: 'status_update',
      status: project.status,
      message: message,
      timestamp: Time.current.iso8601
    }
    
    data[:error] = error if error.present?
    
    ProjectChannel.broadcast_to(project, data)
  end
  
  def broadcast_progress
    ProjectChannel.broadcast_to(project, {
      event: 'progress_update',
      progress: project.processing_progress,
      processed: project.processed_layers_count,
      total: project.total_layers_count,
      current_step: "Processing layer #{project.processed_layers_count} of #{project.total_layers_count}",
      timestamp: Time.current.iso8601
    })
  end
end