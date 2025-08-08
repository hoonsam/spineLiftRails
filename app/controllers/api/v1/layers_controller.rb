class Api::V1::LayersController < Api::V1::BaseController
  before_action :set_project
  before_action :set_layer, only: [:show, :update]
  
  def index
    @layers = @project.layers.includes(:mesh)
    render json: LayerSerializer.new(@layers, include: [:mesh]).serializable_hash
  end
  
  def show
    render json: LayerSerializer.new(@layer, include: [:mesh]).serializable_hash
  end
  
  def update
    if @layer.update(layer_params)
      # Regenerate mesh if parameters changed
      if params[:regenerate_mesh]
        GenerateMeshJob.perform_later(@layer.id)
      end
      
      render json: LayerSerializer.new(@layer).serializable_hash
    else
      render json: { errors: @layer.errors.full_messages }, status: :unprocessable_entity
    end
  end
  
  private
  
  def set_project
    @project = current_user.projects.find(params[:project_id])
  end
  
  def set_layer
    @layer = @project.layers.find(params[:id])
  end
  
  def layer_params
    params.permit(:name, :position)
  end
end