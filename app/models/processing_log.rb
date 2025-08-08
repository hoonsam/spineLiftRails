class ProcessingLog < ApplicationRecord
  belongs_to :project
  
  # Enums
  enum :status, {
    started: 0,
    in_progress: 1,
    completed: 2,
    failed: 3
  }
  
  # Validations
  validates :step, presence: true
  validates :status, presence: true
  
  # Scopes
  scope :recent, -> { order(created_at: :desc) }
  scope :for_step, ->(step) { where(step: step) }
  scope :failed, -> { where(status: :failed) }
end
