# Project Structure

## Current Repository Organization

```
.kiro/
├── settings/
│   └── mcp.json              # MCP server configuration
├── specs/
│   └── sarvasahay-platform/
│       ├── design.md         # Architecture and component design
│       └── requirements.md   # Functional requirements
└── steering/
    ├── product.md           # Product overview and metrics
    ├── tech.md              # Technology stack and standards
    └── structure.md         # This file - project organization
```

## Planned Implementation Structure

### Core Services (Microservices)
```
services/
├── profile-service/         # User profile management
├── eligibility-engine/      # AI-powered scheme matching
├── document-processor/      # OCR and document validation
├── auto-application/        # Form filling and submission
├── tracking-service/        # Application status monitoring
└── notification-service/    # Multi-channel communications
```

### Shared Components
```
shared/
├── models/                  # Data models and schemas
├── utils/                   # Common utilities
├── config/                  # Configuration management
└── middleware/              # API middleware components
```

### AI/ML Components
```
ml/
├── models/
│   ├── eligibility/         # XGBoost eligibility models
│   ├── ocr/                 # Tesseract configurations
│   └── nlp/                 # Speech processing models
├── training/                # Model training scripts
├── data/                    # Training and validation datasets
└── pipelines/               # ML deployment pipelines
```

### API Layer
```
api/
├── gateway/                 # API Gateway configuration
├── specs/                   # OpenAPI 3.0 specifications
├── docs/                    # API documentation
└── tests/                   # API integration tests
```

### Frontend Applications
```
frontend/
├── web-app/                 # Web application for basic smartphones
├── mobile-app/              # Native mobile application
├── sms-interface/           # SMS interaction handlers
└── voice-interface/         # Voice call processing
```

### Infrastructure & DevOps
```
infrastructure/
├── docker/                  # Container configurations
├── kubernetes/              # K8s deployment manifests
├── terraform/               # Infrastructure as code
└── monitoring/              # Observability configurations
```

### Testing & Quality
```
tests/
├── unit/                    # Unit tests by service
├── integration/             # Cross-service integration tests
├── property/                # Property-based tests (Hypothesis)
├── load/                    # Performance and load tests
└── e2e/                     # End-to-end user journey tests
```

## File Naming Conventions

### Services
- Service directories: `kebab-case` (e.g., `profile-service`)
- API endpoints: `/api/v1/resource-name`
- Configuration files: `config.yaml`, `settings.json`

### Models & Schemas
- Data models: `PascalCase` (e.g., `UserProfile`, `GovernmentScheme`)
- Database tables: `snake_case` (e.g., `user_profiles`, `scheme_eligibility`)
- JSON schemas: `camelCase` for properties

### Documentation
- Specification files: `kebab-case.md` (e.g., `api-design.md`)
- README files: `README.md` in each major directory
- Architecture diagrams: `architecture-*.mmd` (Mermaid format)

## Development Workflow Structure

### Branch Strategy
- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: Individual feature development
- `hotfix/*`: Critical production fixes

### Configuration Management
- Environment-specific configs in `config/environments/`
- Secrets managed via environment variables
- Feature flags in `config/features.yaml`

### Documentation Standards
- Each service has its own `README.md`
- API documentation auto-generated from OpenAPI specs
- Architecture decisions recorded in `docs/adr/`
- Runbooks in `docs/operations/`