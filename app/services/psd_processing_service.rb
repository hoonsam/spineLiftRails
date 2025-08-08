require 'net/http/post/multipart'
require 'tempfile'

class PsdProcessingService
  class PsdProcessingError < StandardError; end
  
  def initialize(project)
    @project = project
  end
  
  def call
    return { success: false, error: 'No PSD file attached' } unless @project.psd_file.attached?
    
    @project.start_processing!
    @project.add_processing_log('psd_extraction', 'started', 'Starting PSD layer extraction')
    
    begin
      layers_data = extract_layers
      process_layers(layers_data)
      
      @project.complete_processing!
      @project.add_processing_log('psd_extraction', 'completed', 'Successfully extracted all layers')
      @project.broadcast_status_update
      
      { success: true, layers: @project.layers }
    rescue PsdProcessingError => e
      @project.fail_processing!(e.message)
      @project.add_processing_log('psd_extraction', 'failed', e.message)
      @project.broadcast_status_update
      
      { success: false, error: e.message }
    rescue StandardError => e
      Rails.logger.error "PSD Processing Error: #{e.class} - #{e.message}"
      Rails.logger.error e.backtrace.join("\n")
      
      @project.fail_processing!("Unexpected error: #{e.message}")
      @project.add_processing_log('psd_extraction', 'failed', "Unexpected error: #{e.message}")
      @project.broadcast_status_update
      
      { success: false, error: "Unexpected error: #{e.message}" }
    end
  end
  
  private
  
  def extract_layers
    # Create a temporary file for the PSD
    temp_file = Tempfile.new(['psd', '.psd'], binmode: true)
    
    begin
      # Download PSD to temporary file
      @project.psd_file.download { |chunk| temp_file.write(chunk) }
      temp_file.rewind
      
      # Send to Python service
      send_to_python_service(temp_file)
    ensure
      temp_file.close
      temp_file.unlink if temp_file
    end
  end
  
  def send_to_python_service(temp_file)
    url = URI.parse("#{python_service_url}/api/extract_layers")
    
    File.open(temp_file.path, 'rb') do |file|
      req = Net::HTTP::Post::Multipart.new(url.path,
        'psd_file' => UploadIO.new(file, 'image/vnd.adobe.photoshop', 'upload.psd'),
        'project_id' => @project.id.to_s,
        'callback_url' => callback_url
      )
      
      response = Net::HTTP.start(url.host, url.port, use_ssl: url.scheme == 'https') do |http|
        http.read_timeout = 300 # 5 minutes timeout for large files
        http.open_timeout = 10
        http.request(req)
      end
      
      handle_response(response)
    end
  rescue Net::ReadTimeout => e
    raise PsdProcessingError, "Request timeout after 5 minutes. The PSD file may be too large."
  rescue Net::OpenTimeout => e
    raise PsdProcessingError, "Could not connect to Python service. Please ensure it's running."
  rescue Errno::ECONNREFUSED => e
    raise PsdProcessingError, "Python service is not responding. Please check if it's running on #{python_service_url}"
  rescue StandardError => e
    raise PsdProcessingError, "Network error: #{e.message}"
  end
  
  def handle_response(response)
    case response
    when Net::HTTPSuccess
      begin
        data = JSON.parse(response.body)
        
        # Update total layers count
        @project.update!(total_layers_count: data['total_layers']) if data['total_layers']
        
        data['layers'] || []
      rescue JSON::ParserError => e
        raise PsdProcessingError, "Invalid response from Python service: #{e.message}"
      end
    when Net::HTTPClientError
      error_data = JSON.parse(response.body) rescue {}
      error_message = error_data['detail'] || error_data['error'] || 'Client error'
      raise PsdProcessingError, "PSD processing failed: #{error_message}"
    when Net::HTTPServerError
      raise PsdProcessingError, "Python service error (#{response.code}): #{response.message}"
    else
      raise PsdProcessingError, "Unexpected response (#{response.code}): #{response.message}"
    end
  end
  
  def process_layers(layers_data)
    layers_data.each_with_index do |layer_data, index|
      process_single_layer(layer_data, index)
    end
  end
  
  def process_single_layer(layer_data, position)
    layer = @project.layers.create!(
      name: layer_data['name'] || "Layer #{position + 1}",
      position: position,
      status: :pending
    )
    
    # Update layer with PSD metadata
    layer.update_from_psd_data(layer_data) if layer_data.is_a?(Hash)
    
    # Attach image if present
    if layer_data['image_data'].present?
      attach_layer_image(layer, layer_data['image_data'])
    end
    
    # Queue mesh generation
    GenerateMeshJob.perform_later(layer.id)
    
    @project.add_processing_log(
      'layer_extracted',
      'completed',
      "Extracted layer: #{layer.name}",
      { layer_id: layer.id, position: position }
    )
    
    layer
  rescue StandardError => e
    Rails.logger.error "Failed to process layer #{position}: #{e.message}"
    @project.add_processing_log(
      'layer_extraction',
      'failed',
      "Failed to process layer #{position}: #{e.message}"
    )
  end
  
  def attach_layer_image(layer, image_data)
    # Handle base64 encoded image (with or without data URI prefix)
    if image_data.start_with?('data:image')
      # Extract base64 data from data URI
      base64_data = image_data.split(',')[1]
    else
      # Assume it's raw base64
      base64_data = image_data
    end
    
    begin
      decoded_image = Base64.decode64(base64_data)
      
      # Create temp file
      temp_file = Tempfile.new(['layer', '.png'])
      temp_file.binmode
      temp_file.write(decoded_image)
      temp_file.rewind
      
      # Attach to layer
      layer.image.attach(
        io: temp_file,
        filename: "#{layer.name.parameterize}.png",
        content_type: 'image/png'
      )
      
      temp_file.close
      temp_file.unlink
    rescue StandardError => e
      Rails.logger.error "Failed to attach image to layer #{layer.id}: #{e.message}"
      raise
    end
  rescue StandardError => e
    if image_data.is_a?(String) && image_data.start_with?('http')
      # Handle URL
      downloaded_image = URI.open(image_data)
      layer.image.attach(
        io: downloaded_image,
        filename: "#{layer.name.parameterize}.png",
        content_type: 'image/png'
      )
    end
  rescue StandardError => e
    Rails.logger.error "Failed to attach image to layer #{layer.id}: #{e.message}"
  end
  
  def python_service_url
    ENV.fetch('PYTHON_SERVICE_URL', 'http://localhost:8001')
  end
  
  def callback_url
    # Generate callback URL for progress updates
    host = ENV.fetch('RAILS_HOST', 'localhost:3000')
    protocol = Rails.env.production? ? 'https' : 'http'
    "#{protocol}://#{host}/api/v1/projects/#{@project.id}/processing_callback"
  end
end