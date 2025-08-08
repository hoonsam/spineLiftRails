class AddProcessingMetadataToProjects < ActiveRecord::Migration[8.0]
  def change
    add_column :projects, :total_layers_count, :integer, default: 0
    add_column :projects, :processed_layers_count, :integer, default: 0
    add_column :projects, :error_message, :string
    add_column :projects, :processing_started_at, :datetime
    add_column :projects, :processing_completed_at, :datetime
    
    add_index :projects, :status
  end
end
