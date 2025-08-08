class RegenerateMeshJob < ApplicationJob
  queue_as :default
  
  def perform(layer_id, parameters)
    layer = Layer.find(layer_id)
    
    begin
      layer.update!(status: :processing)
      
      # Regenerate mesh with new parameters
      mesh_data = MeshGenerationService.generate_for_layer(layer, parameters)
      
      # Update mesh
      layer.mesh.update!(
        data: mesh_data,
        parameters: parameters
      )
      
      layer.update!(status: :completed)
      
      # Broadcast update via ActionCable
      LayerChannel.broadcast_to(layer, { 
        status: 'completed',
        mesh: MeshSerializer.new(layer.mesh).serializable_hash
      })
      
    rescue StandardError => e
      layer.update!(status: :failed)
      Rails.logger.error "Failed to regenerate mesh: #{e.message}"
      Rails.logger.error e.backtrace.join("\n")
      
      # Broadcast error
      LayerChannel.broadcast_to(layer, { status: 'failed', error: e.message })
    end
  end
end