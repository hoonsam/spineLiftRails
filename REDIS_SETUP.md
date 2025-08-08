# Redis Setup Instructions

The application requires Redis for background job processing (Sidekiq) and real-time updates (ActionCable).

## Option 1: Install Redis locally

```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

## Option 2: Use Docker

```bash
docker run -d --name spinelift-redis -p 6379:6379 redis:7-alpine
```

## Option 3: Use docker-compose

```bash
docker-compose up -d redis
```

## Temporary Solution (without Redis)

The application is currently configured to use async adapters when Redis is not available:
- ActiveJob uses the `async` adapter
- ActionCable uses the `async` adapter

This allows the application to run without Redis, but with limitations:
- Background jobs run in-process (not recommended for production)
- WebSocket connections work only within the same process
- No job persistence or retry capabilities

To revert to using Redis/Sidekiq once Redis is installed:
1. Edit `config/application.rb` and change:
   ```ruby
   config.active_job.queue_adapter = :sidekiq
   ```
2. Edit `config/cable.yml` and revert development section to:
   ```yaml
   development:
     adapter: redis
     url: <%= ENV.fetch("REDIS_URL", "redis://localhost:6379/1") %>
     channel_prefix: spinelift_development
   ```
3. Restart the Rails server