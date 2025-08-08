class CreateLayers < ActiveRecord::Migration[8.0]
  def change
    create_table :layers do |t|
      t.string :name
      t.integer :position
      t.references :project, null: false, foreign_key: true
      t.integer :status

      t.timestamps
    end
  end
end
