"""
SarvaSahay Platform Test Configuration
Shared fixtures and configuration for all tests
"""

import pytest
from typing import Dict, Any


@pytest.fixture
def sample_user_profile() -> Dict[str, Any]:
    """Sample user profile for testing eligibility engine"""
    return {
        "profileId": "test-user-123",
        "demographics": {
            "age": 35,
            "gender": "female",
            "caste": "SC",
            "maritalStatus": "married"
        },
        "economic": {
            "annualIncome": 120000,
            "landOwnership": 2.5,
            "employmentStatus": "farmer"
        },
        "location": {
            "state": "Maharashtra",
            "district": "Pune",
            "block": "Haveli",
            "village": "Pirangut"
        },
        "family": {
            "size": 4,
            "dependents": 2
        }
    }


@pytest.fixture
def sample_government_schemes() -> list:
    """Sample government schemes for testing"""
    return [
        {
            "schemeId": "PM-KISAN",
            "name": "Pradhan Mantri Kisan Samman Nidhi",
            "benefitAmount": 6000,
            "eligibilityCriteria": {
                "landOwnership": {"min": 0.1, "max": 2.0},
                "employmentStatus": ["farmer"],
                "annualIncome": {"max": 200000}
            }
        },
        {
            "schemeId": "MGNREGA",
            "name": "Mahatma Gandhi National Rural Employment Guarantee Act",
            "benefitAmount": 25000,
            "eligibilityCriteria": {
                "location": {"rural": True},
                "age": {"min": 18, "max": 65}
            }
        }
    ]


@pytest.fixture
def mock_government_api_response():
    """Mock response from government APIs"""
    return {
        "status": "success",
        "applicationId": "APP-2026-001",
        "referenceNumber": "REF123456789",
        "submissionDate": "2026-01-25T12:00:00Z",
        "expectedProcessingTime": "15-30 days"
    }