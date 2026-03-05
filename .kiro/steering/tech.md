# Technology Stack

## Architecture Pattern
- **Microservices Architecture**: Domain-driven design with event-driven communication
- **API-First Design**: All services expose REST APIs with OpenAPI specifications
- **Stateless Services**: Designed for horizontal scaling
- **Event-Driven Communication**: Loose coupling between services via events

## Core Technologies

### AI/ML Stack
- **XGBoost**: Extreme Gradient Boosting for eligibility matching (89% accuracy)
- **Tesseract 5.0**: OCR engine with custom Indian language models
- **OpenCV**: Image preprocessing for document enhancement
- **NLP Processor**: Speech-to-text conversion for voice interface

### Backend Infrastructure
- **Database**: Relational database for profiles/schemes, document store for processed files
- **Caching**: Redis for profile caching and performance optimization
- **Load Balancer**: API Gateway with load balancing capabilities

### Integration Layer
- **Government APIs**: PM-KISAN, DBT System, PFMS, State Government APIs
- **Telecom APIs**: SMS interface integration
- **Voice Systems**: Call center integration for voice interface

## Development Standards

### API Design
- REST APIs with OpenAPI 3.0 specifications
- Consistent error handling with proper HTTP status codes
- API versioning (e.g., `/api/v1/`)
- Circuit breaker pattern for external API calls

### Performance Requirements
- Eligibility evaluation: <5 seconds for 30+ schemes
- Model inference: <1 second response time
- System uptime: 99.5% during business hours
- Concurrent user support: 1,000+ users, 10,000+ simultaneous evaluations

### Testing Strategy
- **Property-Based Testing**: Hypothesis framework (Python) with 100+ iterations
- **Unit Testing**: Coverage for all business logic components
- **Integration Testing**: Real government API testing in staging environment
- **Load Testing**: Performance validation under high concurrent load

## Common Commands

### Model Training & Deployment
```bash
# Retrain eligibility model
python scripts/retrain_model.py --data-path data/training --output models/

# Deploy model updates
python scripts/deploy_model.py --model-version v2.1 --environment production

# Validate model performance
python scripts/validate_model.py --test-data data/validation
```

### API Testing
```bash
# Run integration tests
pytest tests/integration/ --env staging

# Load testing
locust -f tests/load/eligibility_test.py --host https://api.sarvasahay.gov.in

# API documentation generation
swagger-codegen generate -i api/openapi.yaml -l html2 -o docs/api/
```

### Development Workflow
```bash
# Start development environment
docker-compose up -d

# Run property-based tests
python -m pytest tests/property/ --hypothesis-profile dev

# Check API compliance
spectral lint api/openapi.yaml
```