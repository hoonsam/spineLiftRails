class Api::V1::MeshesController < Api::V1::BaseController
  before_action :set_layer
  before_action :set_mesh, only: [:show, :update]
  
  def show
    render json: MeshSerializer.new(@mesh).serializable_hash
  end
  
  def update
    # Update mesh parameters and regenerate
    if mesh_params[:parameters].present?
      # Validate parameters
      validated_params = validate_mesh_parameters(mesh_params[:parameters])
      
      @mesh.parameters = (@mesh.parameters || {}).merge(validated_params)
      
      if @mesh.save
        # Broadcast update via WebSocket
        broadcast_mesh_update(@mesh, 'parameter_update')
        
        # Queue regeneration job
        RegenerateMeshJob.perform_later(@layer.id, @mesh.parameters)
        
        render json: MeshSerializer.new(@mesh).serializable_hash
      else
        render json: { errors: @mesh.errors.full_messages }, status: :unprocessable_entity
      end
    else
      render json: { error: 'No parameters provided' }, status: :bad_request
    end
  end
  
  def update_parameters
    # Dedicated endpoint for parameter updates with debouncing support
    if mesh_params[:parameters].present?
      validated_params = validate_mesh_parameters(mesh_params[:parameters])
      
      @mesh.parameters = (@mesh.parameters || {}).merge(validated_params)
      @mesh.save!
      
      # Only regenerate if explicitly requested
      if params[:regenerate] != 'false'
        RegenerateMeshJob.perform_later(@layer.id, @mesh.parameters)
        broadcast_mesh_update(@mesh, 'regenerating')
      else
        broadcast_mesh_update(@mesh, 'parameters_updated')
      end
      
      render json: {
        data: MeshSerializer.new(@mesh).serializable_hash,
        status: params[:regenerate] != 'false' ? 'regenerating' : 'updated'
      }
    else
      render json: { error: 'No parameters provided' }, status: :bad_request
    end
  rescue StandardError => e
    render json: { error: e.message }, status: :unprocessable_entity
  end
  
  private
  
  def set_layer
    project = current_user.projects.find(params[:project_id])
    @layer = project.layers.find(params[:layer_id])
  end
  
  def set_mesh
    @mesh = @layer.mesh || raise(ActiveRecord::RecordNotFound, 'Mesh not found')
  end
  
  def mesh_params
    params.permit(
      :regenerate,
      parameters: [
        :max_vertices, :quality, :simplification,
        :boundary_accuracy, :interior_accuracy,
        :smoothing, :edge_threshold,
        # Legacy parameters for compatibility
        :detail_factor, :alpha_threshold, :max_triangles
      ]
    )
  end
  
  def validate_mesh_parameters(params)
    validated = {}
    
    # Define parameter constraints
    constraints = {
      max_vertices: { min: 100, max: 5000, type: :integer },
      quality: { min: 0.1, max: 1.0, type: :float },
      simplification: { min: 0.0, max: 0.5, type: :float },
      boundary_accuracy: { min: 0.5, max: 1.0, type: :float },
      interior_accuracy: { min: 0.5, max: 1.0, type: :float },
      smoothing: { min: 0.0, max: 1.0, type: :float },
      edge_threshold: { min: 10, max: 200, type: :integer },
      # Legacy parameters
      detail_factor: { min: 0.001, max: 0.1, type: :float },
      alpha_threshold: { min: 0, max: 255, type: :integer },
      max_triangles: { min: 100, max: 10000, type: :integer }
    }
    
    params.each do |key, value|
      key_sym = key.to_sym
      next unless constraints[key_sym]
      
      constraint = constraints[key_sym]
      
      # Type conversion
      converted_value = case constraint[:type]
                       when :integer
                         value.to_i
                       when :float
                         value.to_f
                       else
                         value
                       end
      
      # Range validation
      if constraint[:min] && converted_value < constraint[:min]
        converted_value = constraint[:min]
      elsif constraint[:max] && converted_value > constraint[:max]
        converted_value = constraint[:max]
      end
      
      validated[key_sym] = converted_value
    end
    
    validated
  end
  
  def broadcast_mesh_update(mesh, action)
    ProjectChannel.broadcast_to(
      @layer.project,
      {
        type: 'mesh_update',
        action: action,
        layer_id: @layer.id,
        mesh_id: mesh.id,
        parameters: mesh.parameters,
        timestamp: Time.current.iso8601
      }
    )
  end
end