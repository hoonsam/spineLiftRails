class Api::V1::MeshProgressController < Api::V1::BaseController
  skip_before_action :authenticate_user! # Allow Python service to call without auth
  
  def create
    # Receive progress updates from Python service
    job_id = params[:job_id]
    progress = params[:progress]
    message = params[:message]
    data = params[:data] || {}
    
    # Broadcast progress via ActionCable
    if job_id.present?
      ActionCable.server.broadcast(
        "mesh_generation_#{job_id}",
        {
          job_id: job_id,
          progress: progress,
          message: message,
          data: data,
          timestamp: Time.current
        }
      )
    end
    
    # Log progress
    Rails.logger.info "Mesh generation progress: Job #{job_id} - #{progress}% - #{message}"
    
    render json: { status: 'received' }, status: :ok
  rescue StandardError => e
    Rails.logger.error "Error processing mesh progress: #{e.message}"
    render json: { error: e.message }, status: :unprocessable_entity
  end
end