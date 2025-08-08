class AddErrorMessageToLayers < ActiveRecord::Migration[8.0]
  def change
    add_column :layers, :error_message, :text
  end
end
