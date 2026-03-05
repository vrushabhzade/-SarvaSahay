"""
Unit tests for Outcome Tracking Service
Tests approval rates, rejection reasons, processing times, and benefit verification
"""

import pytest
from datetime import datetime, timedelta
from services.outcome_tracking_service import OutcomeTrackingService


@pytest.fixture
def tracking_service():
    """Create fresh tracking service for each test"""
    return OutcomeTrackingService()


@pytest.fixture
def sample_user_profile():
    """Sample user profile for testing"""
    return {
        'demographics': {'age': 35, 'gender': 'male', 'caste': 'sc'},
        'economic': {'annualIncome': 80000, 'landOwnership': 2.5}
    }


class TestOutcomeRecording:
    """Test outcome recording functionality"""
    
    def test_record_approved_outcome(self, tracking_service, sample_user_profile):
        """Test recording an approved application outcome"""
        outcome = tracking_service.record_outcome(
            application_id='app-001',
            user_id='user-001',
            scheme_id='scheme-001',
            scheme_name='PM-KISAN',
            predicted_eligible=True,
            predicted_confidence=0.92,
            actual_outcome='approved',
            processing_time_days=15,
            benefit_amount_received=6000.0,
            benefit_timing_days=7,
            user_profile=sample_user_profile
        )
        
        assert outcome['application_id'] == 'app-001'
        assert outcome['actual_outcome'] == 'approved'
        assert outcome['correct_prediction'] is True
        assert outcome['benefit_amount_received'] == 6000.0
    
    def test_record_rejected_outcome(self, tracking_service):
        """Test recording a rejected application outcome"""
        outcome = tracking_service.record_outcome(
            application_id='app-002',
            user_id='user-002',
            scheme_id='scheme-001',
            scheme_name='PM-KISAN',
            predicted_eligible=True,
            predicted_confidence=0.75,
            actual_outcome='rejected',
            rejection_reason='Income exceeds limit',
            processing_time_days=10
        )
        
        assert outcome['actual_outcome'] == 'rejected'
        assert outcome['rejection_reason'] == 'Income exceeds limit'
        assert outcome['correct_prediction'] is False
    
    def test_record_pending_outcome(self, tracking_service):
        """Test recording a pending application outcome"""
        outcome = tracking_service.record_outcome(
            application_id='app-003',
            user_id='user-003',
            scheme_id='scheme-001',
            scheme_name='PM-KISAN',
            predicted_eligible=True,
            predicted_confidence=0.88,
            actual_outcome='pending'
        )
        
        assert outcome['actual_outcome'] == 'pending'
        assert outcome['correct_prediction'] is None
    
    def test_invalid_outcome_raises_error(self, tracking_service):
        """Test that invalid outcome raises ValueError"""
        with pytest.raises(ValueError, match="Invalid outcome"):
            tracking_service.record_outcome(
                application_id='app-004',
                user_id='user-004',
                scheme_id='scheme-001',
                scheme_name='PM-KISAN',
                predicted_eligible=True,
                predicted_confidence=0.85,
                actual_outcome='invalid_status'
            )
    
    def test_invalid_confidence_raises_error(self, tracking_service):
        """Test that invalid confidence raises ValueError"""
        with pytest.raises(ValueError, match="Confidence must be between 0 and 1"):
            tracking_service.record_outcome(
                application_id='app-005',
                user_id='user-005',
                scheme_id='scheme-001',
                scheme_name='PM-KISAN',
                predicted_eligible=True,
                predicted_confidence=1.5,
                actual_outcome='approved'
            )


class TestApprovalRates:
    """Test approval rate calculations"""
    
    def test_approval_rate_all_approved(self, tracking_service):
        """Test approval rate when all applications are approved"""
        for i in range(5):
            tracking_service.record_outcome(
                application_id=f'app-{i}',
                user_id=f'user-{i}',
                scheme_id='scheme-001',
                scheme_name='PM-KISAN',
                predicted_eligible=True,
                predicted_confidence=0.9,
                actual_outcome='approved'
            )
        
        rate = tracking_service.get_approval_rate()
        assert rate == 1.0
    
    def test_approval_rate_mixed_outcomes(self, tracking_service):
        """Test approval rate with mixed outcomes"""
        # 3 approved, 2 rejected
        for i in range(3):
            tracking_service.record_outcome(
                application_id=f'app-approved-{i}',
                user_id=f'user-{i}',
                scheme_id='scheme-001',
                scheme_name='PM-KISAN',
                predicted_eligible=True,
                predicted_confidence=0.9,
                actual_outcome='approved'
            )
        
        for i in range(2):
            tracking_service.record_outcome(
                application_id=f'app-rejected-{i}',
                user_id=f'user-{i+3}',
                scheme_id='scheme-001',
                scheme_name='PM-KISAN',
                predicted_eligible=True,
                predicted_confidence=0.8,
                actual_outcome='rejected',
                rejection_reason='Missing documents'
            )
        
        rate = tracking_service.get_approval_rate()
        assert rate == 0.6  # 3/5
    
    def test_approval_rate_by_scheme(self, tracking_service):
        """Test approval rate filtered by scheme"""
        # Scheme 1: 2 approved, 1 rejected
        for i in range(2):
            tracking_service.record_outcome(
                application_id=f'app-s1-{i}',
                user_id=f'user-{i}',
                scheme_id='scheme-001',
                scheme_name='PM-KISAN',
                predicted_eligible=True,
                predicted_confidence=0.9,
                actual_outcome='approved'
            )
        
        tracking_service.record_outcome(
            application_id='app-s1-rejected',
            user_id='user-3',
            scheme_id='scheme-001',
            scheme_name='PM-KISAN',
            predicted_eligible=True,
            predicted_confidence=0.8,
            actual_outcome='rejected',
            rejection_reason='Income too high'
        )
        
        # Scheme 2: 1 approved, 2 rejected
        tracking_service.record_outcome(
            application_id='app-s2-approved',
            user_id='user-4',
            scheme_id='scheme-002',
            scheme_name='Ayushman Bharat',
            predicted_eligible=True,
            predicted_confidence=0.85,
            actual_outcome='approved'
        )
        
        for i in range(2):
            tracking_service.record_outcome(
                application_id=f'app-s2-rejected-{i}',
                user_id=f'user-{i+5}',
                scheme_id='scheme-002',
                scheme_name='Ayushman Bharat',
                predicted_eligible=True,
                predicted_confidence=0.7,
                actual_outcome='rejected',
                rejection_reason='Not eligible'
            )
        
        rate_s1 = tracking_service.get_approval_rate(scheme_id='scheme-001')
        rate_s2 = tracking_service.get_approval_rate(scheme_id='scheme-002')
        
        assert rate_s1 == pytest.approx(0.667, rel=0.01)
        assert rate_s2 == pytest.approx(0.333, rel=0.01)
    
    def test_approval_rate_excludes_pending(self, tracking_service):
        """Test that pending applications are excluded from approval rate"""
        tracking_service.record_outcome(
            application_id='app-approved',
            user_id='user-1',
            scheme_id='scheme-001',
            scheme_name='PM-KISAN',
            predicted_eligible=True,
            predicted_confidence=0.9,
            actual_outcome='approved'
        )
        
        tracking_service.record_outcome(
            application_id='app-pending',
            user_id='user-2',
            scheme_id='scheme-001',
            scheme_name='PM-KISAN',
            predicted_eligible=True,
            predicted_confidence=0.85,
            actual_outcome='pending'
        )
        
        rate = tracking_service.get_approval_rate()
        assert rate == 1.0  # Only counts the approved one


class TestRejectionReasons:
    """Test rejection reason analytics"""
    
    def test_get_rejection_reasons(self, tracking_service):
        """Test getting rejection reason distribution"""
        reasons = [
            'Income exceeds limit',
            'Missing documents',
            'Income exceeds limit',
            'Age not eligible',
            'Income exceeds limit'
        ]
        
        for i, reason in enumerate(reasons):
            tracking_service.record_outcome(
                application_id=f'app-{i}',
                user_id=f'user-{i}',
                scheme_id='scheme-001',
                scheme_name='PM-KISAN',
                predicted_eligible=True,
                predicted_confidence=0.8,
                actual_outcome='rejected',
                rejection_reason=reason
            )
        
        rejection_reasons = tracking_service.get_rejection_reasons()
        
        assert len(rejection_reasons) == 3
        assert rejection_reasons[0]['reason'] == 'Income exceeds limit'
        assert rejection_reasons[0]['count'] == 3
        assert rejection_reasons[0]['percentage'] == 60.0
    
    def test_rejection_reasons_top_n(self, tracking_service):
        """Test limiting rejection reasons to top N"""
        for i in range(10):
            tracking_service.record_outcome(
                application_id=f'app-{i}',
                user_id=f'user-{i}',
                scheme_id='scheme-001',
                scheme_name='PM-KISAN',
                predicted_eligible=True,
                predicted_confidence=0.8,
                actual_outcome='rejected',
                rejection_reason=f'Reason {i}'
            )
        
        top_3 = tracking_service.get_rejection_reasons(top_n=3)
        assert len(top_3) == 3


class TestProcessingTimeAnalytics:
    """Test processing time analytics"""
    
    def test_processing_time_analytics(self, tracking_service):
        """Test processing time statistics"""
        times = [10, 15, 20, 12, 18]
        
        for i, time_days in enumerate(times):
            tracking_service.record_outcome(
                application_id=f'app-{i}',
                user_id=f'user-{i}',
                scheme_id='scheme-001',
                scheme_name='PM-KISAN',
                predicted_eligible=True,
                predicted_confidence=0.9,
                actual_outcome='approved',
                processing_time_days=time_days
            )
        
        analytics = tracking_service.get_processing_time_analytics()
        
        assert analytics['average_days'] == 15.0
        assert analytics['median_days'] == 15.0
        assert analytics['min_days'] == 10
        assert analytics['max_days'] == 20
        assert analytics['sample_size'] == 5
    
    def test_processing_time_no_data(self, tracking_service):
        """Test processing time analytics with no data"""
        analytics = tracking_service.get_processing_time_analytics()
        
        assert analytics['average_days'] == 0.0
        assert analytics['sample_size'] == 0


class TestBenefitAmountVerification:
    """Test benefit amount verification"""
    
    def test_benefit_amount_verification(self, tracking_service):
        """Test benefit amount statistics"""
        amounts = [6000.0, 6000.0, 5500.0, 6000.0, 6200.0]
        
        for i, amount in enumerate(amounts):
            tracking_service.record_outcome(
                application_id=f'app-{i}',
                user_id=f'user-{i}',
                scheme_id='scheme-001',
                scheme_name='PM-KISAN',
                predicted_eligible=True,
                predicted_confidence=0.9,
                actual_outcome='approved',
                benefit_amount_received=amount
            )
        
        verification = tracking_service.get_benefit_amount_verification(
            expected_amount=6000.0
        )
        
        assert verification['average_amount'] == 5940.0
        assert verification['total_disbursed'] == 29700.0
        assert verification['sample_size'] == 5
        assert verification['matches_expected'] == 60.0  # 3 out of 5
    
    def test_benefit_timing_analytics(self, tracking_service):
        """Test benefit timing from approval to receipt"""
        timings = [5, 7, 10, 6, 8]
        
        for i, timing in enumerate(timings):
            tracking_service.record_outcome(
                application_id=f'app-{i}',
                user_id=f'user-{i}',
                scheme_id='scheme-001',
                scheme_name='PM-KISAN',
                predicted_eligible=True,
                predicted_confidence=0.9,
                actual_outcome='approved',
                benefit_timing_days=timing
            )
        
        analytics = tracking_service.get_benefit_timing_analytics()
        
        assert analytics['average_days'] == 7.2
        assert analytics['median_days'] == 7.0
        assert analytics['min_days'] == 5
        assert analytics['max_days'] == 10


class TestPerformanceReports:
    """Test comprehensive performance reports"""
    
    def test_scheme_performance_report(self, tracking_service):
        """Test scheme-specific performance report"""
        # Add some outcomes
        tracking_service.record_outcome(
            application_id='app-1',
            user_id='user-1',
            scheme_id='scheme-001',
            scheme_name='PM-KISAN',
            predicted_eligible=True,
            predicted_confidence=0.9,
            actual_outcome='approved',
            processing_time_days=15,
            benefit_amount_received=6000.0
        )
        
        tracking_service.record_outcome(
            application_id='app-2',
            user_id='user-2',
            scheme_id='scheme-001',
            scheme_name='PM-KISAN',
            predicted_eligible=True,
            predicted_confidence=0.8,
            actual_outcome='rejected',
            rejection_reason='Income too high',
            processing_time_days=10
        )
        
        report = tracking_service.get_scheme_performance_report('scheme-001')
        
        assert report['scheme_id'] == 'scheme-001'
        assert report['scheme_name'] == 'PM-KISAN'
        assert report['total_applications'] == 2
        assert report['approval_rate'] == 0.5
        assert len(report['rejection_reasons']) == 1
        assert 'processing_time' in report
        assert 'benefit_amounts' in report
    
    def test_overall_performance_report(self, tracking_service):
        """Test overall platform performance report"""
        # Add outcomes for multiple schemes
        for i in range(3):
            tracking_service.record_outcome(
                application_id=f'app-s1-{i}',
                user_id=f'user-{i}',
                scheme_id='scheme-001',
                scheme_name='PM-KISAN',
                predicted_eligible=True,
                predicted_confidence=0.9,
                actual_outcome='approved'
            )
        
        for i in range(2):
            tracking_service.record_outcome(
                application_id=f'app-s2-{i}',
                user_id=f'user-{i+3}',
                scheme_id='scheme-002',
                scheme_name='Ayushman Bharat',
                predicted_eligible=True,
                predicted_confidence=0.85,
                actual_outcome='approved'
            )
        
        report = tracking_service.get_overall_performance_report()
        
        assert report['total_applications'] == 5
        assert report['total_schemes'] == 2
        assert report['overall_approval_rate'] == 1.0


class TestModelAccuracyMetrics:
    """Test model accuracy metrics"""
    
    def test_model_accuracy_calculation(self, tracking_service):
        """Test model prediction accuracy calculation"""
        # 3 correct predictions, 2 incorrect
        outcomes = [
            (True, 'approved', True),   # Correct
            (True, 'approved', True),   # Correct
            (False, 'rejected', True),  # Correct
            (True, 'rejected', False),  # Incorrect
            (False, 'approved', False)  # Incorrect
        ]
        
        for i, (predicted, actual, _) in enumerate(outcomes):
            tracking_service.record_outcome(
                application_id=f'app-{i}',
                user_id=f'user-{i}',
                scheme_id='scheme-001',
                scheme_name='PM-KISAN',
                predicted_eligible=predicted,
                predicted_confidence=0.85,
                actual_outcome=actual
            )
        
        metrics = tracking_service.get_model_accuracy_metrics()
        
        assert metrics['accuracy'] == 0.6  # 3/5
        assert metrics['sample_size'] == 5
        assert metrics['true_positives'] == 2
        assert metrics['false_positives'] == 1
        assert metrics['false_negatives'] == 1
    
    def test_model_accuracy_with_pending(self, tracking_service):
        """Test that pending outcomes are excluded from accuracy"""
        tracking_service.record_outcome(
            application_id='app-1',
            user_id='user-1',
            scheme_id='scheme-001',
            scheme_name='PM-KISAN',
            predicted_eligible=True,
            predicted_confidence=0.9,
            actual_outcome='approved'
        )
        
        tracking_service.record_outcome(
            application_id='app-2',
            user_id='user-2',
            scheme_id='scheme-001',
            scheme_name='PM-KISAN',
            predicted_eligible=True,
            predicted_confidence=0.85,
            actual_outcome='pending'
        )
        
        metrics = tracking_service.get_model_accuracy_metrics()
        
        assert metrics['accuracy'] == 1.0
        assert metrics['sample_size'] == 1  # Only counts completed
