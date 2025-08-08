# Code Style Guide for SpineLift Rails

## Ruby/Rails
- Follow Ruby Style Guide (rubocop-rails-omakase)
- Use Ruby 3.2+ syntax features
- Prefer service objects for complex business logic
- Use concerns for shared model behaviors

### Naming Conventions
- Models: Singular (e.g., `Project`, `Layer`)
- Controllers: Plural with suffix (e.g., `ProjectsController`)
- Services: Descriptive with Service suffix (e.g., `MeshGenerationService`)

### File Organization
```
app/
├── controllers/api/v1/  # API controllers
├── models/              # ActiveRecord models
├── services/            # Business logic services
├── jobs/                # Background jobs
└── serializers/         # JSON serializers
```

## JavaScript/React
- ES6+ syntax with modern features
- Functional components with hooks
- TypeScript for type safety (optional)
- Component file naming: PascalCase

### Component Structure
```
src/
├── components/          # Reusable components
├── pages/              # Page components
├── hooks/              # Custom React hooks
├── api/                # API client code
└── utils/              # Helper functions
```

## Python
- PEP 8 compliance
- Type hints for all functions
- Docstrings for public methods
- Async/await for I/O operations

### Module Organization
```
python/
├── core/               # Core business logic
├── api/                # FastAPI routes
├── services/           # Service classes
└── utils/              # Helper functions
```

## General
- Meaningful variable names
- Comment complex logic
- Keep functions small and focused
- Write tests alongside implementation