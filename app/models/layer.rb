class Layer < ApplicationRecord
  belongs_to :project
  has_one :mesh, dependent: :destroy
  has_one_attached :image
  
  enum :status, {
    pending: 0,
    processing: 1,
    completed: 2,
    failed: 3
  }
  
  validates :name, presence: true
  validates :position, presence: true, numericality: { greater_than_or_equal_to: 0 }
  
  default_scope { order(position: :asc) }
  
  def image_url
    return unless image.attached?
    
    Rails.application.routes.url_helpers.rails_blob_url(
      image,
      host: ENV.fetch('APP_HOST', 'http://localhost:3000')
    )
  end
  
  def mesh_parameters
    {
      detail_factor: 0.01,
      alpha_threshold: 10,
      edge_threshold: 5,
      max_triangles: 5000
    }
  end

  # Metadata accessors
  def bounds
    {
      x: x_offset || 0,
      y: y_offset || 0,
      width: width || 0,
      height: height || 0
    }
  end

  def update_from_psd_data(layer_data)
    update!(
      width: layer_data['width'],
      height: layer_data['height'],
      x_offset: layer_data['x'],
      y_offset: layer_data['y'],
      opacity: layer_data['opacity'] || 1.0,
      blend_mode: layer_data['blend_mode'] || 'normal',
      psd_metadata: layer_data['metadata'] || {}
    )
  end

  def start_processing!
    update!(status: :processing)
  end

  def complete_processing!
    update!(status: :completed)
  end

  def fail_processing!(error_message)
    update!(
      status: :failed,
      error_message: error_message
    )
  end

  def has_mesh?
    mesh.present?
  end

  def regenerate_mesh!
    GenerateMeshJob.perform_later(self.id)
  end
end
