class MeshSerializer
  include JSONAPI::Serializer
  
  attributes :id, :data, :parameters, :created_at, :updated_at
  
  belongs_to :layer
  
  attribute :vertices_count do |mesh|
    mesh.data['vertices']&.count || 0
  end
  
  attribute :triangles_count do |mesh|
    mesh.data['triangles']&.count || 0
  end
end