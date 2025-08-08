class GenerateMeshJob < ApplicationJob
  queue_as :default
  
  def perform(layer_id, custom_parameters = nil)
    layer = Layer.find(layer_id)
    job_id = self.job_id
    
    begin
      layer.update!(status: :processing)
      
      # Generate mesh using Python service with progress tracking
      mesh_data = MeshGenerationService.generate_for_layer(layer, custom_parameters, job_id)
      
      # Create or update mesh
      if layer.mesh.present?
        layer.mesh.update!(
          data: mesh_data,
          parameters: custom_parameters || layer.mesh_parameters || MeshGenerationService.default_parameters
        )
      else
        layer.create_mesh!(
          data: mesh_data,
          parameters: custom_parameters || layer.mesh_parameters || MeshGenerationService.default_parameters
        )
      end
      
      layer.update!(status: :completed)
      
      # Broadcast update via ActionCable
      LayerChannel.broadcast_to(layer, { 
        status: 'completed',
        mesh: MeshSerializer.new(layer.mesh).serializable_hash
      })
      
    rescue MeshGenerationService::MeshGenerationError => e
      layer.update!(status: :failed, error_message: e.message)
      Rails.logger.error "Failed to generate mesh: #{e.message}"
      
      # Broadcast error
      LayerChannel.broadcast_to(layer, { status: 'failed', error: e.message })
      
      # Re-raise to mark job as failed
      raise
    rescue StandardError => e
      layer.update!(status: :failed, error_message: "Unexpected error: #{e.message}")
      Rails.logger.error "Unexpected error generating mesh: #{e.message}"
      Rails.logger.error e.backtrace.join("\n")
      
      # Broadcast error
      LayerChannel.broadcast_to(layer, { status: 'failed', error: e.message })
      
      # Re-raise to mark job as failed
      raise
    end
  end
end