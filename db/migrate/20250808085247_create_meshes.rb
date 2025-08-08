class CreateMeshes < ActiveRecord::Migration[8.0]
  def change
    create_table :meshes do |t|
      t.references :layer, null: false, foreign_key: true
      t.jsonb :data
      t.jsonb :parameters

      t.timestamps
    end
  end
end
