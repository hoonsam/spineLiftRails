class Api::V1::ProjectsController < Api::V1::BaseController
  skip_before_action :authenticate_user!, only: [:processing_callback]
  before_action :set_project, only: [:show, :update, :destroy, :processing_status, :cancel_processing]
  before_action :set_project_by_id, only: [:processing_callback]
  
  def index
    @projects = current_user.projects.includes(:layers)
    render json: ProjectSerializer.new(@projects).serializable_hash
  end
  
  def show
    render json: ProjectSerializer.new(@project, include: [:layers]).serializable_hash
  end
  
  def create
    @project = current_user.projects.build(project_params)
    @project.status = :pending
    
    if @project.save
      ProcessPsdJob.perform_later(@project.id)
      render json: ProjectSerializer.new(@project).serializable_hash, status: :created
    else
      render json: { errors: @project.errors.full_messages }, status: :unprocessable_entity
    end
  end
  
  def update
    if @project.update(project_params)
      render json: ProjectSerializer.new(@project).serializable_hash
    else
      render json: { errors: @project.errors.full_messages }, status: :unprocessable_entity
    end
  end
  
  def destroy
    @project.destroy
    head :no_content
  end
  
  def processing_status
    logs = @project.processing_logs.recent.limit(20)
    
    render json: {
      data: {
        id: @project.id.to_s,
        type: 'processing_status',
        attributes: {
          status: @project.status,
          progress: @project.processing_progress,
          current_step: current_step_message,
          total_layers: @project.total_layers_count,
          processed_layers: @project.processed_layers_count,
          started_at: @project.processing_started_at,
          completed_at: @project.processing_completed_at,
          error_message: @project.error_message,
          duration: @project.processing_duration,
          logs: logs.map { |log| serialize_log(log) }
        }
      }
    }
  end
  
  def cancel_processing
    if @project.cancel_processing!
      render json: ProjectSerializer.new(@project).serializable_hash
    else
      render json: { error: 'Cannot cancel processing in current state' }, status: :unprocessable_entity
    end
  end
  
  def processing_callback
    # This endpoint is called by the Python service to report progress
    case params[:event]
    when 'progress'
      @project.update!(processed_layers_count: params[:current])
      ProjectChannel.broadcast_to(@project, {
        event: 'progress_update',
        progress: params[:progress],
        current: params[:current],
        total: params[:total]
      })
    when 'error'
      @project.update!(status: :failed, error_message: params[:message])
      ProjectChannel.broadcast_to(@project, {
        event: 'error',
        message: params[:message]
      })
    end
    
    head :ok
  end
  
  private
  
  def set_project
    @project = current_user.projects.find(params[:id])
  end
  
  def set_project_by_id
    @project = Project.find(params[:id])
  end
  
  def project_params
    params.require(:project).permit(:name, :psd_file)
  end
  
  def current_step_message
    return nil unless @project.processing?
    
    if @project.total_layers_count > 0
      "Processing layer #{@project.processed_layers_count + 1} of #{@project.total_layers_count}"
    else
      "Extracting layers from PSD"
    end
  end
  
  def serialize_log(log)
    {
      step: log.step,
      status: log.status,
      message: log.message,
      timestamp: log.created_at.iso8601
    }
  end
end