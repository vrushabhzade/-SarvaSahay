# Integration Tests

This directory contains comprehensive integration tests for the SarvaSahay platform, validating cross-service communication, data consistency, and performance under realistic load conditions.

## Test Files

### test_comprehensive_integration.py
Comprehensive integration tests covering:
- **Cross-Service Communication**: Tests data flow between all services
- **Data Consistency**: Validates data integrity across services and storage layers
- **Performance Under Load**: Tests system behavior under concurrent operations

### test_core_services_integration.py
Core service integration tests covering:
- Profile creation and retrieval workflows
- Eligibility evaluation workflows
- Document processing workflows
- End-to-end application workflows
- Performance testing with multiple concurrent operations

### test_government_api_integration.py
Government API integration and compliance tests covering:
- PM-KISAN, DBT, and PFMS API integration
- State government API connections
- API versioning and change adaptation
- Circuit breaker patterns and fallback mechanisms
- Compliance and audit trail features
- GDPR compliance and data privacy

## Test Categories

### 1. Cross-Service Communication Tests
Tests that validate proper data flow and communication between services:
- Profile Service → Eligibility Engine
- Eligibility Engine → Auto-Application Service
- Application Service → Tracking Service
- Tracking Service → Notification Service
- Document Processor → Application Service
- Multi-channel interfaces → Core services

### 2. Data Consistency Tests
Tests that ensure data integrity across the system:
- Profile update consistency across services
- Document-profile data consistency
- Application-tracking data consistency
- Cache-database consistency
- Audit trail consistency

### 3. Performance Under Load Tests
Tests that validate system performance requirements:
- Concurrent profile creation (50+ profiles)
- Concurrent eligibility evaluation (100+ evaluations, <5s requirement)
- Concurrent application submission (30+ applications)
- High-volume notification delivery (50+ notifications)
- Database connection pool under load (100+ operations)
- Cache performance under load (200+ reads)

### 4. End-to-End Integration Tests
Tests that validate complete user journeys:
- Complete user journey under load (20+ concurrent users)
- Government API integration under load (30+ requests)
- System resilience under failure conditions
- Data integrity across all services

## Running the Tests

### Run all integration tests
```bash
pytest tests/integration/ -v
```

### Run specific test file
```bash
pytest tests/integration/test_comprehensive_integration.py -v
```

### Run specific test class
```bash
pytest tests/integration/test_comprehensive_integration.py::TestCrossServiceCommunication -v
```

### Run with coverage
```bash
pytest tests/integration/ --cov=services --cov=shared --cov-report=html
```

### Run performance tests only
```bash
pytest tests/integration/test_comprehensive_integration.py::TestPerformanceUnderLoad -v
```

## Performance Requirements Validated

These tests validate the following performance requirements:
- **Eligibility Evaluation**: <5 seconds for 30+ schemes (Requirement 9.1)
- **Concurrent Users**: 1,000+ users, 10,000+ simultaneous evaluations (Requirement 9.2)
- **System Uptime**: 99.5% during business hours (Requirement 9.5)
- **Response Time**: Consistent performance under load

## Test Data

Tests use synthetic data that covers:
- Multiple user demographics (farmers, laborers, various income levels)
- Various government schemes (PM-KISAN, MGNREGA, state schemes)
- Different communication channels (SMS, voice, web)
- Multiple languages (Marathi, Hindi)

## Dependencies

Required services and infrastructure:
- PostgreSQL database
- Redis cache
- All core services (profile, eligibility, document, application, tracking, notification)
- Government API clients (mock or staging endpoints)

## Notes

- Tests automatically clean up created data
- Concurrent tests use thread pools to simulate realistic load
- Performance assertions may need adjustment based on hardware
- Some tests may require mock government API endpoints in test environment
