# This file is auto-generated from the current state of the database. Instead
# of editing this file, please use the migrations feature of Active Record to
# incrementally modify your database, and then regenerate this schema definition.
#
# This file is the source Rails uses to define your schema when running `bin/rails
# db:schema:load`. When creating a new database, `bin/rails db:schema:load` tends to
# be faster and is potentially less error prone than running all of your
# migrations from scratch. Old migrations may fail to apply correctly if those
# migrations use external dependencies or application code.
#
# It's strongly recommended that you check this file into your version control system.

ActiveRecord::Schema[8.0].define(version: 2025_08_08_111311) do
  # These are extensions that must be enabled in order to support this database
  enable_extension "pg_catalog.plpgsql"

  create_table "active_storage_attachments", force: :cascade do |t|
    t.string "name", null: false
    t.string "record_type", null: false
    t.bigint "record_id", null: false
    t.bigint "blob_id", null: false
    t.datetime "created_at", null: false
    t.index ["blob_id"], name: "index_active_storage_attachments_on_blob_id"
    t.index ["record_type", "record_id", "name", "blob_id"], name: "index_active_storage_attachments_uniqueness", unique: true
  end

  create_table "active_storage_blobs", force: :cascade do |t|
    t.string "key", null: false
    t.string "filename", null: false
    t.string "content_type"
    t.text "metadata"
    t.string "service_name", null: false
    t.bigint "byte_size", null: false
    t.string "checksum"
    t.datetime "created_at", null: false
    t.index ["key"], name: "index_active_storage_blobs_on_key", unique: true
  end

  create_table "active_storage_variant_records", force: :cascade do |t|
    t.bigint "blob_id", null: false
    t.string "variation_digest", null: false
    t.index ["blob_id", "variation_digest"], name: "index_active_storage_variant_records_uniqueness", unique: true
  end

  create_table "layers", force: :cascade do |t|
    t.string "name"
    t.integer "position"
    t.bigint "project_id", null: false
    t.integer "status"
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.text "error_message"
    t.integer "width"
    t.integer "height"
    t.integer "x_offset"
    t.integer "y_offset"
    t.float "opacity", default: 1.0
    t.string "blend_mode"
    t.jsonb "psd_metadata", default: {}
    t.index ["position"], name: "index_layers_on_position"
    t.index ["project_id"], name: "index_layers_on_project_id"
  end

  create_table "meshes", force: :cascade do |t|
    t.bigint "layer_id", null: false
    t.jsonb "data"
    t.jsonb "parameters"
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["layer_id"], name: "index_meshes_on_layer_id"
  end

  create_table "processing_logs", force: :cascade do |t|
    t.bigint "project_id", null: false
    t.string "step"
    t.string "status"
    t.text "message"
    t.jsonb "metadata", default: {}
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.index ["project_id", "created_at"], name: "index_processing_logs_on_project_id_and_created_at"
    t.index ["project_id"], name: "index_processing_logs_on_project_id"
  end

  create_table "projects", force: :cascade do |t|
    t.string "name"
    t.integer "status"
    t.bigint "user_id", null: false
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.integer "total_layers_count", default: 0
    t.integer "processed_layers_count", default: 0
    t.string "error_message"
    t.datetime "processing_started_at"
    t.datetime "processing_completed_at"
    t.index ["status"], name: "index_projects_on_status"
    t.index ["user_id"], name: "index_projects_on_user_id"
  end

  create_table "users", force: :cascade do |t|
    t.string "email", default: "", null: false
    t.string "encrypted_password", default: "", null: false
    t.string "reset_password_token"
    t.datetime "reset_password_sent_at"
    t.datetime "remember_created_at"
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.string "name"
    t.index ["email"], name: "index_users_on_email", unique: true
    t.index ["reset_password_token"], name: "index_users_on_reset_password_token", unique: true
  end

  add_foreign_key "active_storage_attachments", "active_storage_blobs", column: "blob_id"
  add_foreign_key "active_storage_variant_records", "active_storage_blobs", column: "blob_id"
  add_foreign_key "layers", "projects"
  add_foreign_key "meshes", "layers"
  add_foreign_key "processing_logs", "projects"
  add_foreign_key "projects", "users"
end
