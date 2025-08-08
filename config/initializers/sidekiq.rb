# Sidekiq configuration
require 'sidekiq'

# Configure Sidekiq server
Sidekiq.configure_server do |config|
  config.redis = { 
    url: ENV.fetch('REDIS_URL', 'redis://localhost:6379/0'),
    network_timeout: 5
  }
  
  # Set server middleware
  config.server_middleware do |chain|
    # Add any server middleware here
  end
  
  # Configure error handling
  config.error_handlers << Proc.new do |ex, ctx_hash|
    Rails.logger.error "Sidekiq error: #{ex.class} - #{ex.message}"
    Rails.logger.error ex.backtrace.join("\n")
  end
end

# Configure Sidekiq client
Sidekiq.configure_client do |config|
  config.redis = { 
    url: ENV.fetch('REDIS_URL', 'redis://localhost:6379/0'),
    network_timeout: 5
  }
end

# Configure Sidekiq options
Sidekiq.default_job_options = {
  'backtrace' => true,
  'retry' => 3,
  'dead' => false
}

# Configure queues with priorities
Sidekiq.configure_server do |config|
  config.queues = %w[critical default low]
end