class CreateProcessingLogs < ActiveRecord::Migration[8.0]
  def change
    create_table :processing_logs do |t|
      t.references :project, null: false, foreign_key: true
      t.string :step
      t.string :status
      t.text :message
      t.jsonb :metadata, default: {}

      t.timestamps
    end
    
    add_index :processing_logs, [:project_id, :created_at]
  end
end
