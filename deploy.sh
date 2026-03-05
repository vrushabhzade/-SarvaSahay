#!/bin/bash

# SarvaSahay Platform - Quick Deployment Script
# This script provides a simple way to deploy the platform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    print_success "Docker is installed"
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    print_success "Docker Compose is installed"
    
    if [ ! -f ".env" ]; then
        print_error ".env file not found. Please create it from .env.example"
        exit 1
    fi
    print_success ".env file exists"
}

# Build Docker images
build_images() {
    print_info "Building Docker images..."
    docker build -t sarvasahay-platform:latest -f infrastructure/docker/Dockerfile .
    print_success "Docker images built successfully"
}

# Start services
start_services() {
    print_info "Starting services..."
    docker-compose up -d
    print_success "Services started successfully"
}

# Wait for services to be ready
wait_for_services() {
    print_info "Waiting for services to be ready..."
    
    # Wait for PostgreSQL
    print_info "Waiting for PostgreSQL..."
    until docker-compose exec -T postgres pg_isready -U sarvasahay &> /dev/null; do
        sleep 2
    done
    print_success "PostgreSQL is ready"
    
    # Wait for Redis
    print_info "Waiting for Redis..."
    until docker-compose exec -T redis redis-cli ping &> /dev/null; do
        sleep 2
    done
    print_success "Redis is ready"
    
    # Wait for application
    print_info "Waiting for application..."
    sleep 10
    until curl -f http://localhost:8000/health &> /dev/null; do
        sleep 5
    done
    print_success "Application is ready"
}

# Initialize database
init_database() {
    print_info "Initializing database..."
    
    # Run migrations
    print_info "Running database migrations..."
    docker-compose exec -T app alembic upgrade head
    print_success "Database migrations completed"
    
    # Load initial data
    print_info "Loading government schemes..."
    docker-compose exec -T app python scripts/db_manager.py load-schemes
    print_success "Government schemes loaded"
    
    print_info "Loading form templates..."
    docker-compose exec -T app python scripts/db_manager.py load-templates
    print_success "Form templates loaded"
}

# Health check
health_check() {
    print_info "Running health checks..."
    
    # Check API
    if curl -f http://localhost:8000/health &> /dev/null; then
        print_success "API health check passed"
    else
        print_error "API health check failed"
        exit 1
    fi
    
    # Check database
    if curl -f http://localhost:8000/api/v1/health/database &> /dev/null; then
        print_success "Database health check passed"
    else
        print_error "Database health check failed"
        exit 1
    fi
    
    # Check cache
    if curl -f http://localhost:8000/api/v1/health/cache &> /dev/null; then
        print_success "Cache health check passed"
    else
        print_error "Cache health check failed"
        exit 1
    fi
}

# Show deployment info
show_info() {
    echo ""
    echo "=========================================="
    echo "  SarvaSahay Platform Deployment Complete"
    echo "=========================================="
    echo ""
    echo "Application URL: http://localhost:8000"
    echo "API Documentation: http://localhost:8000/docs"
    echo "Health Check: http://localhost:8000/health"
    echo ""
    echo "To view logs:"
    echo "  docker-compose logs -f"
    echo ""
    echo "To stop services:"
    echo "  docker-compose down"
    echo ""
    echo "To restart services:"
    echo "  docker-compose restart"
    echo ""
}

# Main deployment flow
main() {
    echo "=========================================="
    echo "  SarvaSahay Platform Deployment"
    echo "=========================================="
    echo ""
    
    check_prerequisites
    build_images
    start_services
    wait_for_services
    init_database
    health_check
    show_info
    
    print_success "Deployment completed successfully!"
}

# Run main function
main
