# Shared Data Models

from .user_profile import (
    Gender,
    Caste,
    MaritalStatus,
    EmploymentStatus,
    Language,
    CommunicationChannel,
    Demographics,
    Economic,
    Location,
    Family,
    Documents,
    Preferences,
    UserProfile,
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResponse
)

from .government_scheme import (
    SchemeType,
    SchemeStatus,
    EligibilityCategory,
    NumericCriteria,
    EligibilityCriteria,
    GovernmentScheme,
    EligibilityResult,
    EligibilityEvaluation
)

from .application import (
    ApplicationStatus,
    PaymentStatus,
    ApplicationPriority,
    StatusHistory,
    ApplicationPredictions,
    PaymentDetails,
    Application,
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationResponse,
    ApplicationSummary
)

__all__ = [
    # User Profile models
    "Gender",
    "Caste",
    "MaritalStatus",
    "EmploymentStatus",
    "Language",
    "CommunicationChannel",
    "Demographics",
    "Economic",
    "Location",
    "Family",
    "Documents",
    "Preferences",
    "UserProfile",
    "UserProfileCreate",
    "UserProfileUpdate",
    "UserProfileResponse",
    
    # Government Scheme models
    "SchemeType",
    "SchemeStatus",
    "EligibilityCategory",
    "NumericCriteria",
    "EligibilityCriteria",
    "GovernmentScheme",
    "EligibilityResult",
    "EligibilityEvaluation",
    
    # Application models
    "ApplicationStatus",
    "PaymentStatus",
    "ApplicationPriority",
    "StatusHistory",
    "ApplicationPredictions",
    "PaymentDetails",
    "Application",
    "ApplicationCreate",
    "ApplicationUpdate",
    "ApplicationResponse",
    "ApplicationSummary",
]