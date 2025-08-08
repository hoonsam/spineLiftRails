# SpineLift Rails Mesh Generation Feature Specifications

This directory contains detailed specifications for implementing the mesh generation feature in SpineLift Rails during weeks 3-4 of development.

## Specification Documents

1. **[01-overview.md](01-overview.md)** - High-level architecture and implementation timeline
2. **[02-python-fastapi-service.md](02-python-fastapi-service.md)** - Python service implementation with FastAPI
3. **[03-rails-service-wrappers.md](03-rails-service-wrappers.md)** - Rails service layer and orchestration
4. **[04-background-jobs.md](04-background-jobs.md)** - Sidekiq jobs for async processing
5. **[05-parameter-validation.md](05-parameter-validation.md)** - Parameter validation and optimization
6. **[06-realtime-progress.md](06-realtime-progress.md)** - WebSocket-based progress updates

## Quick Start

### 1. Review the specifications in order
Start with the overview document to understand the overall architecture, then dive into specific components.

### 2. Set up development environment
```bash
# Python service
cd python_service
pip install -r requirements.txt
uvicorn app.main:app --reload

# Rails application
bundle install
rails db:migrate
rails s
```

### 3. Key implementation priorities
- Port BatchMeshProcessor to FastAPI (Days 1-2)
- Implement Rails service wrappers (Days 3-4)
- Add background job processing (Day 5)
- Implement real-time progress (Week 4, Days 1-2)
- Optimize and handle edge cases (Week 4, Days 3-5)

## Architecture Summary

```
User Upload → Rails API → Sidekiq Job → Python Service → Mesh Result
     ↓                         ↓                ↓            ↓
 Validation              Progress Updates   Processing   Storage
```

## Key Features

- **Asynchronous Processing**: Non-blocking mesh generation using background jobs
- **Real-time Progress**: WebSocket updates during processing
- **Parameter Validation**: Comprehensive validation with optimization suggestions
- **Error Handling**: Graceful failure recovery and user notifications
- **Scalability**: Horizontal scaling support for both Rails and Python services

## Testing Strategy

Each component includes comprehensive tests:
- Unit tests for individual services
- Integration tests for end-to-end workflows
- Performance tests for processing time requirements
- Error scenario tests for edge cases

## Performance Requirements

- Typical image processing: < 30 seconds
- Progress updates: Every 2-3 seconds
- Concurrent processing: Up to 10 simultaneous generations
- API response time: < 200ms for status checks

## Dependencies

### Rails Side
- Ruby 3.2+
- Rails 7.1+
- PostgreSQL 14+
- Redis 7+
- Sidekiq 7+
- ActionCable

### Python Side
- Python 3.11+
- FastAPI 0.104+
- OpenCV 4.8+
- Triangle library
- Pydantic 2.0+

## Deployment Considerations

- Use Docker for consistent environments
- Configure proper resource limits
- Set up monitoring and alerting
- Implement proper logging
- Use environment-specific configurations

## Next Steps

After implementing the mesh generation feature:
1. Add mesh editing capabilities
2. Implement mesh optimization tools
3. Add batch processing UI
4. Create mesh preview system
5. Add export formats support