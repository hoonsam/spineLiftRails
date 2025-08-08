class ProjectSerializer
  include JSONAPI::Serializer
  
  attributes :id, :name, :status, :created_at, :updated_at
  
  has_many :layers
  
  attribute :psd_file_url do |project|
    project.psd_file_url
  end
  
  attribute :layers_count do |project|
    project.layers.count
  end
end