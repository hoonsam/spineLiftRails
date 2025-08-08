class Project < ApplicationRecord
  belongs_to :user
  has_many :layers, dependent: :destroy
  has_many :processing_logs, dependent: :destroy
  has_one_attached :psd_file
  
  enum :status, {
    pending: 0,
    processing: 1,
    completed: 2,
    failed: 3,
    cancelled: 4
  }
  
  validates :name, presence: true
  validates :psd_file, presence: true
  
  # Processing methods
  def processing_progress
    return 0 if total_layers_count.zero?
    (processed_layers_count.to_f / total_layers_count * 100).round
  end
  
  def processing_duration
    return nil unless processing_started_at
    end_time = processing_completed_at || Time.current
    (end_time - processing_started_at).round
  end
  
  def can_cancel?
    pending? || processing?
  end
  
  def cancel_processing!
    return false unless can_cancel?
    
    update!(status: :cancelled)
    # TODO: Cancel background job if running
    true
  end
  
  def psd_file_url
    return unless psd_file.attached?
    
    Rails.application.routes.url_helpers.rails_blob_url(psd_file)
  end

  # Additional processing methods
  def start_processing!
    update!(
      status: :processing,
      processing_started_at: Time.current,
      processed_layers_count: 0
    )
  end

  def complete_processing!
    update!(
      status: :completed,
      processing_completed_at: Time.current
    )
  end

  def fail_processing!(error_message)
    update!(
      status: :failed,
      error_message: error_message,
      processing_completed_at: Time.current
    )
  end

  def increment_processed_layers!
    increment!(:processed_layers_count)
  end

  def add_processing_log(step, status, message, metadata = {})
    processing_logs.create!(
      step: step,
      status: status,
      message: message,
      metadata: metadata
    )
  end

  def broadcast_status_update
    ProjectChannel.broadcast_to(self, {
      type: 'status_update',
      project_id: id,
      status: status,
      progress: processing_progress,
      processed_layers: processed_layers_count,
      total_layers: total_layers_count
    })
  end
end
