class AddMetadataToLayers < ActiveRecord::Migration[8.0]
  def change
    add_column :layers, :width, :integer
    add_column :layers, :height, :integer
    add_column :layers, :x_offset, :integer
    add_column :layers, :y_offset, :integer
    add_column :layers, :opacity, :float, default: 1.0
    add_column :layers, :blend_mode, :string
    add_column :layers, :psd_metadata, :jsonb, default: {}
    
    add_index :layers, :position
  end
end
