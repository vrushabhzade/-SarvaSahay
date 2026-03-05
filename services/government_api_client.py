"""
Government API Integration Client
Handles integration with PM-KISAN, DBT, PFMS and other government APIs
Includes circuit breaker pattern and retry logic
"""

from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import time
import random


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class APIError(Exception):
    """Base exception for API errors"""
    pass


class APITimeoutError(APIError):
    """API timeout exception"""
    pass


class APIAuthenticationError(APIError):
    """API authentication exception"""
    pass


class APIRateLimitError(APIError):
    """API rate limit exception"""
    pass


class CircuitBreaker:
    """
    Circuit breaker pattern implementation
    Prevents cascading failures when external APIs are down
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = APIError
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise APIError("Circuit breaker is OPEN - service unavailable")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        
        time_since_failure = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return time_since_failure >= self.recovery_timeout


class RetryPolicy:
    """
    Retry policy with exponential backoff
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except (APITimeoutError, APIRateLimitError) as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    delay = self._calculate_delay(attempt)
                    time.sleep(delay)
                else:
                    raise e
            except APIAuthenticationError:
                # Don't retry authentication errors
                raise
        
        raise last_exception
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter"""
        delay = min(
            self.initial_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        
        if self.jitter:
            delay = delay * (0.5 + random.random() * 0.5)
        
        return delay


class GovernmentAPIClient:
    """
    Base client for government API integration
    Provides common functionality for all government APIs
    """
    
    def __init__(
        self,
        api_name: str,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        self.api_name = api_name
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        
        # Initialize circuit breaker and retry policy
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60
        )
        self.retry_policy = RetryPolicy(
            max_retries=3,
            initial_delay=1.0
        )
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request with circuit breaker and retry
        This is a mock implementation - in production would use requests library
        """
        def request_func():
            # Mock implementation
            # In production, this would use requests.request()
            return {
                "success": True,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Execute with retry policy and circuit breaker
        return self.retry_policy.execute(
            lambda: self.circuit_breaker.call(request_func)
        )
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health status"""
        return {
            "apiName": self.api_name,
            "status": "healthy" if self.circuit_breaker.state == CircuitState.CLOSED else "degraded",
            "circuitState": self.circuit_breaker.state,
            "failureCount": self.circuit_breaker.failure_count,
            "timestamp": datetime.utcnow().isoformat()
        }


class PMKISANClient(GovernmentAPIClient):
    """
    PM-KISAN API Client
    Handles farmer registration and benefit tracking
    """
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            api_name="PM-KISAN",
            base_url="https://api.pmkisan.gov.in/v1",
            api_key=api_key
        )
    
    def submit_application(
        self,
        application_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submit farmer registration application
        
        Args:
            application_data: Application form data
            
        Returns:
            Submission result with reference number
        """
        # Validate required fields
        required_fields = ["aadhaar_number", "name", "bank_account", "bank_ifsc", "land_ownership"]
        for field in required_fields:
            if field not in application_data:
                raise ValueError(f"Missing required field: {field}")
        
        response = self._make_request(
            method="POST",
            endpoint="/applications",
            data=application_data
        )
        
        # Generate reference number
        ref_number = f"PMKISAN{datetime.utcnow().strftime('%Y%m%d')}{random.randint(100000, 999999)}"
        
        return {
            "success": True,
            "referenceNumber": ref_number,
            "status": "submitted",
            "message": "Application submitted successfully",
            "submittedAt": datetime.utcnow().isoformat()
        }
    
    def check_status(
        self,
        reference_number: str
    ) -> Dict[str, Any]:
        """
        Check application status
        
        Args:
            reference_number: Government reference number
            
        Returns:
            Application status
        """
        response = self._make_request(
            method="GET",
            endpoint=f"/applications/{reference_number}"
        )
        
        return {
            "referenceNumber": reference_number,
            "status": "under_review",
            "lastUpdated": datetime.utcnow().isoformat(),
            "expectedCompletionDays": 30
        }
    
    def verify_farmer(
        self,
        aadhaar_number: str,
        land_records: str
    ) -> Dict[str, Any]:
        """
        Verify farmer eligibility
        
        Args:
            aadhaar_number: Farmer's Aadhaar number
            land_records: Land record reference
            
        Returns:
            Verification result
        """
        response = self._make_request(
            method="POST",
            endpoint="/verify",
            data={
                "aadhaar": aadhaar_number,
                "landRecords": land_records
            }
        )
        
        return {
            "verified": True,
            "farmerName": "Mock Farmer",
            "landOwnership": 2.5,
            "verifiedAt": datetime.utcnow().isoformat()
        }


class DBTClient(GovernmentAPIClient):
    """
    Direct Benefit Transfer (DBT) System Client
    Handles benefit payment tracking
    """
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            api_name="DBT",
            base_url="https://api.dbtbharat.gov.in/v1",
            api_key=api_key
        )
    
    def register_beneficiary(
        self,
        beneficiary_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Register beneficiary for DBT
        
        Args:
            beneficiary_data: Beneficiary information
            
        Returns:
            Registration result
        """
        required_fields = ["aadhaar_number", "bank_account", "bank_ifsc", "scheme_id"]
        for field in required_fields:
            if field not in beneficiary_data:
                raise ValueError(f"Missing required field: {field}")
        
        response = self._make_request(
            method="POST",
            endpoint="/beneficiaries",
            data=beneficiary_data
        )
        
        beneficiary_id = f"DBT{random.randint(1000000000, 9999999999)}"
        
        return {
            "success": True,
            "beneficiaryId": beneficiary_id,
            "status": "registered",
            "registeredAt": datetime.utcnow().isoformat()
        }
    
    def check_payment_status(
        self,
        beneficiary_id: str,
        scheme_id: str
    ) -> Dict[str, Any]:
        """
        Check payment status for beneficiary
        
        Args:
            beneficiary_id: DBT beneficiary ID
            scheme_id: Scheme identifier
            
        Returns:
            Payment status
        """
        response = self._make_request(
            method="GET",
            endpoint=f"/payments/{beneficiary_id}/{scheme_id}"
        )
        
        return {
            "beneficiaryId": beneficiary_id,
            "schemeId": scheme_id,
            "paymentStatus": "pending",
            "expectedPaymentDate": (datetime.utcnow() + timedelta(days=15)).isoformat(),
            "lastChecked": datetime.utcnow().isoformat()
        }
    
    def get_payment_history(
        self,
        beneficiary_id: str
    ) -> Dict[str, Any]:
        """
        Get payment history for beneficiary
        
        Args:
            beneficiary_id: DBT beneficiary ID
            
        Returns:
            Payment history
        """
        response = self._make_request(
            method="GET",
            endpoint=f"/payments/{beneficiary_id}/history"
        )
        
        return {
            "beneficiaryId": beneficiary_id,
            "payments": [],
            "totalAmount": 0,
            "retrievedAt": datetime.utcnow().isoformat()
        }


class PFMSClient(GovernmentAPIClient):
    """
    Public Financial Management System (PFMS) Client
    Handles payment tracking and verification
    """
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            api_name="PFMS",
            base_url="https://api.pfms.nic.in/v1",
            api_key=api_key
        )
    
    def track_payment(
        self,
        transaction_id: str
    ) -> Dict[str, Any]:
        """
        Track payment transaction
        
        Args:
            transaction_id: PFMS transaction ID
            
        Returns:
            Payment tracking information
        """
        response = self._make_request(
            method="GET",
            endpoint=f"/transactions/{transaction_id}"
        )
        
        return {
            "transactionId": transaction_id,
            "status": "processing",
            "amount": 0,
            "beneficiaryAccount": "XXXX",
            "initiatedAt": datetime.utcnow().isoformat(),
            "lastUpdated": datetime.utcnow().isoformat()
        }
    
    def verify_payment(
        self,
        transaction_id: str,
        expected_amount: float
    ) -> Dict[str, Any]:
        """
        Verify payment completion
        
        Args:
            transaction_id: PFMS transaction ID
            expected_amount: Expected payment amount
            
        Returns:
            Verification result
        """
        response = self._make_request(
            method="POST",
            endpoint=f"/transactions/{transaction_id}/verify",
            data={"expectedAmount": expected_amount}
        )
        
        return {
            "transactionId": transaction_id,
            "verified": False,
            "actualAmount": 0,
            "status": "pending",
            "verifiedAt": datetime.utcnow().isoformat()
        }
    
    def get_scheme_disbursements(
        self,
        scheme_id: str,
        from_date: str,
        to_date: str
    ) -> Dict[str, Any]:
        """
        Get disbursement summary for a scheme
        
        Args:
            scheme_id: Scheme identifier
            from_date: Start date (ISO format)
            to_date: End date (ISO format)
            
        Returns:
            Disbursement summary
        """
        response = self._make_request(
            method="GET",
            endpoint=f"/schemes/{scheme_id}/disbursements",
            data={
                "fromDate": from_date,
                "toDate": to_date
            }
        )
        
        return {
            "schemeId": scheme_id,
            "totalDisbursements": 0,
            "totalAmount": 0,
            "fromDate": from_date,
            "toDate": to_date,
            "retrievedAt": datetime.utcnow().isoformat()
        }


class StateGovernmentClient(GovernmentAPIClient):
    """
    State Government API Client
    Handles state-specific scheme integrations
    """
    
    def __init__(
        self,
        state_name: str,
        base_url: str,
        api_key: Optional[str] = None
    ):
        super().__init__(
            api_name=f"{state_name}-State-API",
            base_url=base_url,
            api_key=api_key
        )
        self.state_name = state_name
    
    def submit_state_application(
        self,
        scheme_id: str,
        application_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submit application to state government scheme
        
        Args:
            scheme_id: State scheme identifier
            application_data: Application form data
            
        Returns:
            Submission result
        """
        response = self._make_request(
            method="POST",
            endpoint=f"/schemes/{scheme_id}/applications",
            data=application_data
        )
        
        ref_number = f"{self.state_name.upper()}-{scheme_id}-{datetime.utcnow().strftime('%Y%m%d')}-{random.randint(100000, 999999)}"
        
        return {
            "success": True,
            "referenceNumber": ref_number,
            "state": self.state_name,
            "schemeId": scheme_id,
            "status": "submitted",
            "submittedAt": datetime.utcnow().isoformat()
        }
    
    def check_state_status(
        self,
        reference_number: str
    ) -> Dict[str, Any]:
        """
        Check state application status
        
        Args:
            reference_number: State reference number
            
        Returns:
            Application status
        """
        response = self._make_request(
            method="GET",
            endpoint=f"/applications/{reference_number}"
        )
        
        return {
            "referenceNumber": reference_number,
            "state": self.state_name,
            "status": "under_review",
            "lastUpdated": datetime.utcnow().isoformat()
        }
    
    def get_state_schemes(self) -> Dict[str, Any]:
        """
        Get list of active state schemes
        
        Returns:
            List of state schemes
        """
        response = self._make_request(
            method="GET",
            endpoint="/schemes"
        )
        
        return {
            "state": self.state_name,
            "schemes": [],
            "retrievedAt": datetime.utcnow().isoformat()
        }


class APIVersionManager:
    """
    Manages API versioning and change adaptation
    Handles version detection and automatic migration
    """
    
    def __init__(self):
        self.version_mappings: Dict[str, Dict[str, Any]] = {}
        self.deprecated_endpoints: Dict[str, str] = {}
    
    def register_version(
        self,
        api_name: str,
        version: str,
        endpoint_mappings: Dict[str, str]
    ):
        """
        Register API version with endpoint mappings
        
        Args:
            api_name: Name of the API
            version: Version identifier
            endpoint_mappings: Mapping of logical endpoints to versioned endpoints
        """
        if api_name not in self.version_mappings:
            self.version_mappings[api_name] = {}
        
        self.version_mappings[api_name][version] = endpoint_mappings
    
    def get_endpoint(
        self,
        api_name: str,
        version: str,
        logical_endpoint: str
    ) -> str:
        """
        Get versioned endpoint for logical endpoint
        
        Args:
            api_name: Name of the API
            version: Version to use
            logical_endpoint: Logical endpoint name
            
        Returns:
            Versioned endpoint path
        """
        if api_name not in self.version_mappings:
            return logical_endpoint
        
        if version not in self.version_mappings[api_name]:
            # Use latest version if requested version not found
            version = max(self.version_mappings[api_name].keys())
        
        mappings = self.version_mappings[api_name][version]
        return mappings.get(logical_endpoint, logical_endpoint)
    
    def mark_deprecated(
        self,
        endpoint: str,
        replacement: str,
        deprecation_date: str
    ):
        """
        Mark endpoint as deprecated
        
        Args:
            endpoint: Deprecated endpoint
            replacement: Replacement endpoint
            deprecation_date: Date when endpoint will be removed
        """
        self.deprecated_endpoints[endpoint] = {
            "replacement": replacement,
            "deprecationDate": deprecation_date
        }
    
    def check_deprecation(self, endpoint: str) -> Optional[Dict[str, str]]:
        """
        Check if endpoint is deprecated
        
        Args:
            endpoint: Endpoint to check
            
        Returns:
            Deprecation info if deprecated, None otherwise
        """
        return self.deprecated_endpoints.get(endpoint)


class GovernmentAPIIntegration:
    """
    Unified interface for all government API integrations
    Manages multiple API clients with fallback mechanisms
    Supports state government APIs and version management
    """
    
    def __init__(
        self,
        pm_kisan_key: Optional[str] = None,
        dbt_key: Optional[str] = None,
        pfms_key: Optional[str] = None,
        state_configs: Optional[Dict[str, Dict[str, str]]] = None
    ):
        self.pm_kisan = PMKISANClient(pm_kisan_key)
        self.dbt = DBTClient(dbt_key)
        self.pfms = PFMSClient(pfms_key)
        
        # Initialize state government clients
        self.state_clients: Dict[str, StateGovernmentClient] = {}
        if state_configs:
            for state_name, config in state_configs.items():
                self.state_clients[state_name] = StateGovernmentClient(
                    state_name=state_name,
                    base_url=config.get("base_url", ""),
                    api_key=config.get("api_key")
                )
        
        # Initialize version manager
        self.version_manager = APIVersionManager()
        self._register_api_versions()
    
    def _register_api_versions(self):
        """Register known API versions and their endpoint mappings"""
        # PM-KISAN API versions
        self.version_manager.register_version(
            "PM-KISAN",
            "v1",
            {
                "submit_application": "/applications",
                "check_status": "/applications/{ref}",
                "verify_farmer": "/verify"
            }
        )
        
        self.version_manager.register_version(
            "PM-KISAN",
            "v2",
            {
                "submit_application": "/v2/farmer/register",
                "check_status": "/v2/applications/status/{ref}",
                "verify_farmer": "/v2/farmer/verify"
            }
        )
        
        # DBT API versions
        self.version_manager.register_version(
            "DBT",
            "v1",
            {
                "register_beneficiary": "/beneficiaries",
                "check_payment": "/payments/{id}/{scheme}",
                "payment_history": "/payments/{id}/history"
            }
        )
        
        # PFMS API versions
        self.version_manager.register_version(
            "PFMS",
            "v1",
            {
                "track_payment": "/transactions/{id}",
                "verify_payment": "/transactions/{id}/verify",
                "scheme_disbursements": "/schemes/{id}/disbursements"
            }
        )
    
    def adapt_to_api_change(
        self,
        api_name: str,
        new_version: str,
        change_log: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Adapt to API changes within 48 hours
        
        Args:
            api_name: Name of the API that changed
            new_version: New API version
            change_log: Details of changes
            
        Returns:
            Adaptation result
        """
        # Log the change
        adaptation_log = {
            "apiName": api_name,
            "newVersion": new_version,
            "changeLog": change_log,
            "adaptedAt": datetime.utcnow().isoformat(),
            "status": "adapted"
        }
        
        # Update endpoint mappings if provided
        if "endpoint_mappings" in change_log:
            self.version_manager.register_version(
                api_name,
                new_version,
                change_log["endpoint_mappings"]
            )
        
        # Mark deprecated endpoints
        if "deprecated_endpoints" in change_log:
            for endpoint, info in change_log["deprecated_endpoints"].items():
                self.version_manager.mark_deprecated(
                    endpoint,
                    info.get("replacement", ""),
                    info.get("deprecation_date", "")
                )
        
        return adaptation_log
    
    def get_state_client(self, state_name: str) -> Optional[StateGovernmentClient]:
        """
        Get state government API client
        
        Args:
            state_name: Name of the state
            
        Returns:
            State API client if available
        """
        return self.state_clients.get(state_name)
    
    def submit_application(
        self,
        scheme_id: str,
        application_data: Dict[str, Any],
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submit application to appropriate government API
        Supports central and state government schemes
        
        Args:
            scheme_id: Government scheme identifier
            application_data: Application form data
            state: State name for state-specific schemes
            
        Returns:
            Submission result
        """
        try:
            # Check if this is a state-specific scheme
            if state and state in self.state_clients:
                return self.state_clients[state].submit_state_application(
                    scheme_id,
                    application_data
                )
            
            # Central government schemes
            if scheme_id == "PM-KISAN":
                return self.pm_kisan.submit_application(application_data)
            else:
                # Generic submission for other schemes
                return {
                    "success": True,
                    "referenceNumber": f"{scheme_id}-{datetime.utcnow().strftime('%Y%m%d')}-{random.randint(100000, 999999)}",
                    "status": "submitted",
                    "message": "Application submitted successfully",
                    "submittedAt": datetime.utcnow().isoformat()
                }
        except APIError as e:
            # Fallback mechanism - provide alternative submission method
            return {
                "success": False,
                "error": str(e),
                "fallbackMethod": "manual",
                "instructions": "Please visit the nearest government office to submit your application manually.",
                "requiredDocuments": ["Aadhaar Card", "Bank Passbook", "Application Form"]
            }
    
    def check_application_status(
        self,
        scheme_id: str,
        reference_number: str,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check application status across government systems
        Supports central and state government schemes
        
        Args:
            scheme_id: Government scheme identifier
            reference_number: Application reference number
            state: State name for state-specific schemes
            
        Returns:
            Application status
        """
        try:
            # Check if this is a state-specific application
            if state and state in self.state_clients:
                return self.state_clients[state].check_state_status(reference_number)
            
            # Central government schemes
            if scheme_id == "PM-KISAN":
                return self.pm_kisan.check_status(reference_number)
            else:
                return {
                    "referenceNumber": reference_number,
                    "status": "under_review",
                    "lastUpdated": datetime.utcnow().isoformat()
                }
        except APIError:
            return {
                "referenceNumber": reference_number,
                "status": "unknown",
                "error": "Unable to fetch status from government system",
                "lastUpdated": datetime.utcnow().isoformat()
            }
    
    def track_payment(
        self,
        transaction_id: str
    ) -> Dict[str, Any]:
        """
        Track payment through PFMS
        
        Args:
            transaction_id: Payment transaction ID
            
        Returns:
            Payment tracking information
        """
        return self.pfms.track_payment(transaction_id)
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check health of all government API integrations
        Includes central and state government APIs
        
        Returns:
            Health status of all APIs
        """
        health_status = {
            "pmKisan": self.pm_kisan.health_check(),
            "dbt": self.dbt.health_check(),
            "pfms": self.pfms.health_check(),
            "stateAPIs": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add state API health checks
        for state_name, client in self.state_clients.items():
            health_status["stateAPIs"][state_name] = client.health_check()
        
        return health_status
    
    def get_all_state_schemes(self) -> Dict[str, Any]:
        """
        Get all schemes from all connected state governments
        
        Returns:
            Dictionary of state schemes
        """
        all_schemes = {}
        
        for state_name, client in self.state_clients.items():
            try:
                schemes = client.get_state_schemes()
                all_schemes[state_name] = schemes
            except APIError as e:
                all_schemes[state_name] = {
                    "error": str(e),
                    "schemes": []
                }
        
        return {
            "stateSchemes": all_schemes,
            "retrievedAt": datetime.utcnow().isoformat()
        }
