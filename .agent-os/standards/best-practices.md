# Best Practices for SpineLift Rails

## API Design
- RESTful conventions for CRUD operations
- Versioned APIs (/api/v1/)
- Consistent error responses
- JWT authentication for API endpoints

## Database
- Use migrations for all schema changes
- Add indexes for foreign keys and frequently queried fields
- Store large data (mesh vertices) in JSONB fields
- Use database transactions for data integrity

## File Handling
- Use Active Storage for file uploads
- Implement virus scanning for uploaded files
- Set file size limits (500MB for PSD files)
- Clean up orphaned files regularly

## Performance
- Cache expensive operations (mesh data, rendered images)
- Use background jobs for heavy processing
- Implement pagination for list endpoints
- Optimize N+1 queries with includes/joins

## Security
- Validate all user inputs
- Use strong parameters in controllers
- Implement rate limiting
- Sanitize file uploads
- Use HTTPS in production

## Error Handling
- Use specific exception classes
- Log errors with context
- Provide user-friendly error messages
- Implement proper error recovery

## Testing
- Write tests before implementation (TDD)
- Aim for 80%+ code coverage
- Test edge cases and error conditions
- Use factories instead of fixtures
- Mock external services in tests

## Python Service Integration
- Use HTTP/REST for Rails-Python communication
- Implement circuit breakers for resilience
- Handle timeouts gracefully
- Log all inter-service communications

## Frontend
- Implement proper loading states
- Handle network errors gracefully
- Use optimistic updates where appropriate
- Implement proper form validation
- Support keyboard navigation

## Deployment
- Use environment variables for configuration
- Implement health check endpoints
- Set up proper logging and monitoring
- Use multi-stage Docker builds
- Implement zero-downtime deployments