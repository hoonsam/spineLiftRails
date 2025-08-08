class MeshGenerationService
  include HTTParty
  base_uri ENV.fetch('PYTHON_SERVICE_URL', 'http://localhost:8000')
  
  class MeshGenerationError < StandardError; end
  
  def self.generate_for_layer(layer, custom_parameters = nil, job_id = nil)
    parameters = custom_parameters || layer.mesh_parameters || default_parameters
    
    # Build callback URL for progress updates
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
      timeout: 60 # Increased timeout for mesh generation
    )
    
    if response.success?
      mesh_data = response.parsed_response['mesh']
      
      # Store mesh data if we have a mesh record
      if layer.mesh
        layer.mesh.update!(
          data: {
            vertices: mesh_data['vertices'],
            triangles: mesh_data['triangles'],
            uvs: mesh_data['uvs']
          },
          parameters: parameters,
          metadata: mesh_data['metadata']
        )
      end
      
      mesh_data
    else
      error_message = response.parsed_response['detail'] || response.parsed_response['error'] || 'Unknown error'
      raise MeshGenerationError, "Mesh generation failed: #{error_message}"
    end
  rescue HTTParty::Error => e
    raise MeshGenerationError, "Network error: #{e.message}"
  rescue StandardError => e
    raise MeshGenerationError, "Unexpected error: #{e.message}"
  end
  
  def self.generate_from_file(file_path, parameters = nil, job_id = nil)
    parameters ||= default_parameters
    
    callback_url = Rails.application.routes.url_helpers.api_v1_mesh_progress_url(
      host: ENV['APP_HOST'] || 'localhost:3000'
    )
    
    File.open(file_path, 'rb') do |file|
      response = post('/api/generate_mesh_from_file',
        body: {
          file: file,
          detail_factor: parameters[:detail_factor],
          alpha_threshold: parameters[:alpha_threshold],
          callback_url: callback_url,
          job_id: job_id
        },
        headers: { 'Content-Type' => 'multipart/form-data' },
        timeout: 60
      )
      
      if response.success?
        response.parsed_response['mesh']
      else
        error_message = response.parsed_response['detail'] || 'Unknown error'
        raise MeshGenerationError, "Mesh generation failed: #{error_message}"
      end
    end
  rescue HTTParty::Error => e
    raise MeshGenerationError, "Network error: #{e.message}"
  rescue StandardError => e
    raise MeshGenerationError, "Unexpected error: #{e.message}"
  end
  
  private
  
  def self.default_parameters
    {
      detail_factor: 0.01,
      alpha_threshold: 10,
      concave_factor: 0.0,
      internal_vertex_density: 0,
      blur_kernel_size: 1,
      binary_threshold: 128,
      min_contour_area: 10
    }
  end
end