# Real-time Progress Updates Specification

## Overview

This document specifies the real-time progress update system for mesh generation, using ActionCable for WebSocket communication and Redis PubSub for inter-service messaging.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Web Client     │────▶│  ActionCable    │────▶│  Redis PubSub   │
│  (JavaScript)   │◀────│   (WebSocket)   │◀────│                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                          ▲
                                                          │
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Python Service │────▶│  Progress API   │────▶│  Rails Callback │
│                 │     │   (HTTP POST)   │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## ActionCable Implementation

### 1. Progress Channel

```ruby
# app/channels/mesh_progress_channel.rb
class MeshProgressChannel < ApplicationCable::Channel
  def subscribed
    mesh = find_mesh
    return reject unless authorized?(mesh)
    
    stream_for mesh
    
    # Send current progress immediately
    transmit current_progress(mesh)
  end
  
  def unsubscribed
    # Cleanup if needed
  end
  
  def request_update
    mesh = find_mesh
    return unless authorized?(mesh)
    
    # Force progress check
    transmit current_progress(mesh)
  end
  
  private
  
  def find_mesh
    Mesh.find_by(id: params[:mesh_id])
  end
  
  def authorized?(mesh)
    return false unless mesh
    
    # Check if current user can access this mesh
    ability = Ability.new(current_user)
    ability.can?(:read, mesh)
  end
  
  def current_progress(mesh)
    tracker = Mesh::ProgressTracker.new(mesh)
    progress_data = tracker.current_progress
    
    {
      mesh_id: mesh.id,
      status: progress_data[:status],
      progress: progress_data[:progress],
      message: progress_data[:message],
      updated_at: progress_data[:updated_at],
      estimated_remaining: estimate_remaining_time(mesh, progress_data[:progress])
    }
  end
  
  def estimate_remaining_time(mesh, current_progress)
    return nil if current_progress <= 0
    
    elapsed = Time.current - mesh.created_at
    total_estimated = elapsed / (current_progress / 100.0)
    remaining = total_estimated - elapsed
    
    remaining.positive? ? remaining.round : nil
  end
end
```

### 2. Batch Progress Channel

```ruby
# app/channels/batch_progress_channel.rb
class BatchProgressChannel < ApplicationCable::Channel
  def subscribed
    batch = find_batch
    return reject unless authorized?(batch)
    
    stream_from "batch_progress_#{batch.id}"
    
    # Send current state
    transmit current_batch_progress(batch)
  end
  
  private
  
  def find_batch
    MeshBatch.find_by(id: params[:batch_id])
  end
  
  def authorized?(batch)
    return false unless batch
    
    batch.user_id == current_user.id || 
      current_user.can?(:manage, batch.project)
  end
  
  def current_batch_progress(batch)
    {
      batch_id: batch.id,
      total: batch.total_images,
      completed: batch.completed_count,
      failed: batch.failed_count,
      progress: batch.progress_percentage,
      status: batch.status,
      estimated_remaining: batch.estimated_remaining_time
    }
  end
end
```

## JavaScript Client Implementation

### 1. Progress Subscriber

```javascript
// app/javascript/channels/mesh_progress_channel.js
import consumer from "./consumer"

class MeshProgressSubscriber {
  constructor(meshId, callbacks = {}) {
    this.meshId = meshId
    this.callbacks = callbacks
    this.subscription = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
  }
  
  subscribe() {
    this.subscription = consumer.subscriptions.create(
      { 
        channel: "MeshProgressChannel", 
        mesh_id: this.meshId 
      },
      {
        connected: () => {
          this.handleConnected()
        },
        
        disconnected: () => {
          this.handleDisconnected()
        },
        
        received: (data) => {
          this.handleProgressUpdate(data)
        },
        
        rejected: () => {
          this.handleRejected()
        }
      }
    )
    
    return this
  }
  
  unsubscribe() {
    if (this.subscription) {
      this.subscription.unsubscribe()
      this.subscription = null
    }
  }
  
  requestUpdate() {
    if (this.subscription) {
      this.subscription.perform('request_update')
    }
  }
  
  handleConnected() {
    console.log(`Connected to mesh progress channel for mesh ${this.meshId}`)
    this.reconnectAttempts = 0
    
    if (this.callbacks.onConnected) {
      this.callbacks.onConnected()
    }
  }
  
  handleDisconnected() {
    console.log(`Disconnected from mesh progress channel`)
    
    if (this.callbacks.onDisconnected) {
      this.callbacks.onDisconnected()
    }
    
    // Attempt to reconnect
    this.attemptReconnect()
  }
  
  handleProgressUpdate(data) {
    console.log('Progress update received:', data)
    
    // Update UI
    this.updateProgressBar(data.progress)
    this.updateStatusMessage(data.message)
    this.updateTimeRemaining(data.estimated_remaining)
    
    // Handle completion
    if (data.status === 'completed') {
      this.handleCompletion(data)
    } else if (data.status === 'failed') {
      this.handleFailure(data)
    }
    
    // Call custom callback
    if (this.callbacks.onProgress) {
      this.callbacks.onProgress(data)
    }
  }
  
  handleRejected() {
    console.error('Subscription rejected - unauthorized')
    
    if (this.callbacks.onError) {
      this.callbacks.onError('Unauthorized to view mesh progress')
    }
  }
  
  handleCompletion(data) {
    this.updateProgressBar(100)
    this.updateStatusMessage('Mesh generation completed!')
    
    if (this.callbacks.onComplete) {
      this.callbacks.onComplete(data)
    }
    
    // Auto-unsubscribe after completion
    setTimeout(() => this.unsubscribe(), 5000)
  }
  
  handleFailure(data) {
    this.updateStatusMessage(`Failed: ${data.message}`)
    
    if (this.callbacks.onError) {
      this.callbacks.onError(data.message)
    }
    
    // Auto-unsubscribe after failure
    setTimeout(() => this.unsubscribe(), 5000)
  }
  
  attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached')
      return
    }
    
    this.reconnectAttempts++
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000)
    
    setTimeout(() => {
      console.log(`Attempting to reconnect (attempt ${this.reconnectAttempts})`)
      this.subscribe()
    }, delay)
  }
  
  updateProgressBar(progress) {
    const progressBar = document.querySelector(`#mesh-${this.meshId}-progress`)
    if (progressBar) {
      progressBar.style.width = `${progress}%`
      progressBar.setAttribute('aria-valuenow', progress)
      progressBar.textContent = `${progress}%`
    }
  }
  
  updateStatusMessage(message) {
    const statusElement = document.querySelector(`#mesh-${this.meshId}-status`)
    if (statusElement) {
      statusElement.textContent = message
    }
  }
  
  updateTimeRemaining(seconds) {
    const timeElement = document.querySelector(`#mesh-${this.meshId}-time`)
    if (timeElement && seconds) {
      const formatted = this.formatTime(seconds)
      timeElement.textContent = `Est. ${formatted} remaining`
    }
  }
  
  formatTime(seconds) {
    if (seconds < 60) return `${seconds}s`
    const minutes = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${minutes}m ${secs}s`
  }
}

export default MeshProgressSubscriber
```

### 2. Progress Component

```javascript
// app/javascript/components/mesh_progress_component.js
import { Controller } from "@hotwired/stimulus"
import MeshProgressSubscriber from "../channels/mesh_progress_channel"

export default class extends Controller {
  static targets = ["container", "progressBar", "status", "time", "result"]
  static values = { meshId: Number }
  
  connect() {
    this.setupProgressSubscription()
  }
  
  disconnect() {
    if (this.progressSubscriber) {
      this.progressSubscriber.unsubscribe()
    }
  }
  
  setupProgressSubscription() {
    this.progressSubscriber = new MeshProgressSubscriber(this.meshIdValue, {
      onProgress: (data) => this.handleProgress(data),
      onComplete: (data) => this.handleComplete(data),
      onError: (error) => this.handleError(error),
      onConnected: () => this.handleConnected(),
      onDisconnected: () => this.handleDisconnected()
    })
    
    this.progressSubscriber.subscribe()
  }
  
  handleProgress(data) {
    // Update progress bar
    this.progressBarTarget.style.width = `${data.progress}%`
    this.progressBarTarget.textContent = `${data.progress}%`
    
    // Update status
    this.statusTarget.textContent = data.message
    
    // Update time remaining
    if (data.estimated_remaining) {
      this.timeTarget.textContent = this.formatTime(data.estimated_remaining)
      this.timeTarget.classList.remove('d-none')
    }
    
    // Add animation class
    this.containerTarget.classList.add('processing')
  }
  
  handleComplete(data) {
    this.containerTarget.classList.remove('processing')
    this.containerTarget.classList.add('completed')
    
    // Show success message
    this.showSuccessMessage()
    
    // Load result if available
    if (data.result_url) {
      this.loadMeshResult(data.result_url)
    }
  }
  
  handleError(error) {
    this.containerTarget.classList.remove('processing')
    this.containerTarget.classList.add('failed')
    
    this.showErrorMessage(error)
  }
  
  handleConnected() {
    this.containerTarget.classList.add('connected')
  }
  
  handleDisconnected() {
    this.containerTarget.classList.remove('connected')
  }
  
  retry() {
    // Trigger mesh regeneration
    fetch(`/api/v1/meshes/${this.meshIdValue}/retry`, {
      method: 'POST',
      headers: {
        'X-CSRF-Token': this.getCSRFToken()
      }
    }).then(response => {
      if (response.ok) {
        this.resetProgress()
        this.setupProgressSubscription()
      }
    })
  }
  
  cancel() {
    // Cancel mesh generation
    fetch(`/api/v1/meshes/${this.meshIdValue}/cancel`, {
      method: 'POST',
      headers: {
        'X-CSRF-Token': this.getCSRFToken()
      }
    }).then(response => {
      if (response.ok) {
        this.progressSubscriber.unsubscribe()
        this.containerTarget.classList.add('cancelled')
      }
    })
  }
  
  formatTime(seconds) {
    const minutes = Math.floor(seconds / 60)
    const secs = seconds % 60
    return minutes > 0 ? `${minutes}m ${secs}s` : `${secs}s`
  }
  
  getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').content
  }
}
```

## Progress Callback API

```ruby
# app/controllers/api/v1/mesh_callbacks_controller.rb
module Api
  module V1
    class MeshCallbacksController < ApiController
      skip_before_action :authenticate_user!
      before_action :verify_callback_token
      
      def progress
        job = Mesh::ProgressCallbackJob.perform_later(
          job_id: params[:job_id],
          progress: params[:progress],
          message: params[:message],
          status: params[:status]
        )
        
        render json: { status: 'accepted', job_id: job.job_id }
      end
      
      private
      
      def verify_callback_token
        mesh = Mesh.find_by!(job_id: params[:job_id])
        
        # Verify callback is from trusted source
        provided_token = request.headers['X-Callback-Token']
        expected_token = generate_callback_token(mesh)
        
        unless ActiveSupport::SecurityUtils.secure_compare(provided_token, expected_token)
          render json: { error: 'Invalid callback token' }, status: :unauthorized
        end
      end
      
      def generate_callback_token(mesh)
        Rails.application.message_verifier(:mesh_callback).generate(
          mesh_id: mesh.id,
          job_id: mesh.job_id,
          expires_at: 1.hour.from_now
        )
      end
    end
  end
end
```

## Redis PubSub Integration

```ruby
# app/services/mesh/progress_publisher.rb
module Mesh
  class ProgressPublisher
    attr_reader :redis
    
    def initialize
      @redis = Redis.new(url: ENV['REDIS_URL'])
    end
    
    def publish(mesh_id, progress_data)
      channel = "mesh_progress:#{mesh_id}"
      
      redis.publish(channel, progress_data.to_json)
      
      # Also broadcast via ActionCable
      ActionCable.server.broadcast(
        "mesh_progress_#{mesh_id}",
        progress_data
      )
    end
    
    def publish_batch(batch_id, progress_data)
      channel = "batch_progress:#{batch_id}"
      
      redis.publish(channel, progress_data.to_json)
      
      ActionCable.server.broadcast(
        "batch_progress_#{batch_id}",
        progress_data
      )
    end
  end
end

# app/services/mesh/progress_subscriber.rb
module Mesh
  class ProgressSubscriber
    def self.start
      Thread.new do
        redis = Redis.new(url: ENV['REDIS_URL'])
        
        redis.psubscribe('mesh_progress:*', 'batch_progress:*') do |on|
          on.pmessage do |pattern, channel, message|
            handle_message(pattern, channel, message)
          end
        end
      end
    end
    
    private
    
    def self.handle_message(pattern, channel, message)
      data = JSON.parse(message, symbolize_names: true)
      
      case pattern
      when 'mesh_progress:*'
        mesh_id = channel.split(':').last
        handle_mesh_progress(mesh_id, data)
      when 'batch_progress:*'
        batch_id = channel.split(':').last
        handle_batch_progress(batch_id, data)
      end
    rescue StandardError => e
      Rails.logger.error "Progress subscriber error: #{e.message}"
    end
    
    def self.handle_mesh_progress(mesh_id, data)
      # Additional processing if needed
      Rails.logger.info "Mesh #{mesh_id} progress: #{data[:progress]}%"
    end
    
    def self.handle_batch_progress(batch_id, data)
      # Additional processing if needed
      Rails.logger.info "Batch #{batch_id} progress: #{data[:completed]}/#{data[:total]}"
    end
  end
end
```

## Progress UI Components

```erb
<!-- app/views/meshes/_progress.html.erb -->
<div id="mesh-<%= mesh.id %>-progress-container" 
     class="mesh-progress-container"
     data-controller="mesh-progress"
     data-mesh-progress-mesh-id-value="<%= mesh.id %>">
  
  <div class="progress-header">
    <h5>Mesh Generation Progress</h5>
    <span class="connection-status" data-mesh-progress-target="connection"></span>
  </div>
  
  <div class="progress mb-3">
    <div class="progress-bar progress-bar-striped progress-bar-animated"
         role="progressbar"
         data-mesh-progress-target="progressBar"
         style="width: 0%"
         aria-valuenow="0"
         aria-valuemin="0"
         aria-valuemax="100">
      0%
    </div>
  </div>
  
  <div class="progress-info">
    <div class="status" data-mesh-progress-target="status">
      Initializing...
    </div>
    <div class="time-remaining d-none" data-mesh-progress-target="time">
      Est. time remaining
    </div>
  </div>
  
  <div class="progress-actions mt-3">
    <button class="btn btn-sm btn-secondary" 
            data-action="click->mesh-progress#cancel"
            data-mesh-progress-target="cancelButton">
      Cancel
    </button>
  </div>
  
  <div class="result-container d-none" data-mesh-progress-target="result">
    <!-- Result will be loaded here -->
  </div>
</div>

<style>
.mesh-progress-container {
  padding: 1.5rem;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #f8f9fa;
}

.mesh-progress-container.processing {
  border-color: #0d6efd;
  background: #e7f1ff;
}

.mesh-progress-container.completed {
  border-color: #198754;
  background: #d1e7dd;
}

.mesh-progress-container.failed {
  border-color: #dc3545;
  background: #f8d7da;
}

.connection-status {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #6c757d;
  display: inline-block;
}

.mesh-progress-container.connected .connection-status {
  background: #198754;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 0.875rem;
  color: #6c757d;
}

.status {
  font-weight: 500;
}
</style>
```

## Testing Strategy

```ruby
# spec/channels/mesh_progress_channel_spec.rb
RSpec.describe MeshProgressChannel, type: :channel do
  let(:user) { create(:user) }
  let(:mesh) { create(:mesh, user: user) }
  
  before do
    stub_connection current_user: user
  end
  
  describe '#subscribed' do
    it 'streams for authorized mesh' do
      subscribe(mesh_id: mesh.id)
      
      expect(subscription).to be_confirmed
      expect(subscription).to have_stream_for(mesh)
    end
    
    it 'rejects unauthorized mesh' do
      other_mesh = create(:mesh)
      
      subscribe(mesh_id: other_mesh.id)
      
      expect(subscription).to be_rejected
    end
    
    it 'transmits current progress on subscribe' do
      subscribe(mesh_id: mesh.id)
      
      expect(transmissions.last).to include(
        'mesh_id' => mesh.id,
        'progress' => 0,
        'status' => 'pending'
      )
    end
  end
end
```