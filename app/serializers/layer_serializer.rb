class LayerSerializer
  include JSONAPI::Serializer
  
  attributes :id, :name, :position, :status, :created_at, :updated_at
  
  belongs_to :project
  has_one :mesh
  
  attribute :image_url do |layer|
    layer.image_url
  end
  
  attribute :has_mesh do |layer|
    layer.mesh.present?
  end
end