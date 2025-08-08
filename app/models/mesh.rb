class Mesh < ApplicationRecord
  belongs_to :layer
  
  validates :data, presence: true
  validates :parameters, presence: true
  
  # Store mesh data structure:
  # {
  #   vertices: [[x, y], ...],
  #   triangles: [[i1, i2, i3], ...],
  #   uvs: [[u, v], ...],
  #   bounds: { x: 0, y: 0, width: 100, height: 100 }
  # }
end
