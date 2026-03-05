"""
Property-Based Tests for Outcome Learning and Model Improvement
Feature: sarvasahay-platform, Property 7: Outcome Learning and Model Improvement

This test validates that for any application outcome, the system:
1. Tracks approval rates, rejection reasons, and processing times
2. Uses outcome data to retrain models and improve eligibility predictions
3. Identifies patterns and generates improvement recommendations
4. Implements quarterly improvement reporting

Validates: Requirements 7.1, 7.2, 7.3, 7.5
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime, timedelta
from typing import Dict, List, Any

from services.outcome_tracking_service import OutcomeTrackingService
from services.model_improvement_service import ModelImprovementService, PatternAnalyzer


# Strategy for generating valid application outcomes
@st.composite
def outcome_strategy(draw):
    """Generate valid application outcome data"""
    predicted_eligible = draw(st.booleans())
    actual_outcome = draw(st.sampled_from(['approved', 'rejected', 'pending']))
    
    # Generate user profile for pattern analysis
    user_profile = {
        'demographics': {
            'age': draw(st.integers(min_value=18, max_value=80)),
            'gender': draw(st.sampled_from(['male', 'female', 'other'])),
            'caste': draw(st.sampled_from(['general', 'obc', 'sc', 'st'])),
            'maritalStatus': draw(st.sampled_from(['single', 'married', 'widowed']))
        },
        'economic': {
            'annualIncome': draw(st.integers(min_value=0, max_value=500000)),
            'landOwnership': draw(st.floats(min_value=0, max_value=50, allow_nan=False, allow_infinity=False)),
            'employmentStatus': draw(st.sampled_from(['farmer', 'laborer', 'self_employed', 'unemployed']))
        }
    }
    
    return {
        'application_id': f"app-{draw(st.integers(min_value=1000, max_value=9999))}",
        'user_id': f"user-{draw(st.integers(min_value=100, max_value=999))}",
        'scheme_id': f"scheme-{draw(st.integers(min_value=1, max_value=30))}",
        'scheme_name': draw(st.sampled_from([
            'PM-KISAN', 'Ayushman Bharat', 'MGNREGA', 'Pradhan Mantri Awas Yojana',
            'National Social Assistance Programme', 'Kisan Credit Card'
        ])),
        'predicted_eligible': predicted_eligible,
        'predicted_confidence': draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)),
        'actual_outcome': actual_outcome,
        'rejection_reason': draw(st.sampled_from([
            'Income exceeds limit', 'Age not eligible', 'Missing documents',
            'Land ownership exceeds limit', 'Already receiving benefits', None
        ])) if actual_outcome == 'rejected' else None,
        'processing_time_days': draw(st.integers(min_value=1, max_value=180)) if actual_outcome != 'pending' else None,
        'benefit_amount_received': draw(st.floats(min_value=1000, max_value=100000, allow_nan=False, allow_infinity=False)) if actual_outcome == 'approved' else None,
        'benefit_timing_days': draw(st.integers(min_value=1, max_value=90)) if actual_outcome == 'approved' else None,
        'user_profile': user_profile
    }


# Strategy for generating lists of outcomes
@st.composite
def outcomes_list_strategy(draw, min_size=5, max_size=50):
    """Generate a list of application outcomes"""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    return [draw(outcome_strategy()) for _ in range(size)]


class TestOutcomeLearningProperty:
    """
    Property 7: Outcome Learning and Model Improvement
    
    For any application outcome, the system should:
    1. Track approval rates, rejection reasons, and processing times
    2. Use data to retrain models and improve predictions
    3. Identify patterns for algorithm updates
    4. Generate quarterly improvement reports
    """
    
    @given(outcome=outcome_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_outcome_tracking_records_all_metrics(self, outcome: Dict[str, Any]):
        """
        Property: All application outcomes must be tracked with complete metrics
        
        Validates Requirement 7.1: Track approval rates, rejection reasons, and processing times
        """
        service = OutcomeTrackingService()
        
        # Record the outcome
        recorded = service.record_outcome(**outcome)
        
        # Verify all required fields are tracked
        assert recorded['application_id'] == outcome['application_id']
        assert recorded['user_id'] == outcome['user_id']
        assert recorded['scheme_id'] == outcome['scheme_id']
        assert recorded['predicted_eligible'] == outcome['predicted_eligible']
        assert recorded['actual_outcome'] == outcome['actual_outcome']
        assert 'timestamp' in recorded
        
        # Verify outcome is stored
        assert service.get_outcome_count() == 1
        
        # Verify metrics can be retrieved
        if outcome['actual_outcome'] in ['approved', 'rejected']:
            approval_rate = service.get_approval_rate()
            assert 0 <= approval_rate <= 1
    
    @given(outcomes=outcomes_list_strategy(min_size=10, max_size=30))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_approval_rate_calculation_accuracy(self, outcomes: List[Dict[str, Any]]):
        """
        Property: Approval rate must be accurately calculated from outcomes
        
        Validates Requirement 7.1: Track approval rates accurately
        """
        service = OutcomeTrackingService()
        
        # Record all outcomes
        for outcome in outcomes:
            service.record_outcome(**outcome)
        
        # Calculate expected approval rate
        completed = [o for o in outcomes if o['actual_outcome'] in ['approved', 'rejected']]
        
        if completed:
            expected_rate = sum(1 for o in completed if o['actual_outcome'] == 'approved') / len(completed)
            actual_rate = service.get_approval_rate()
            
            # Verify approval rate is correct
            assert abs(actual_rate - expected_rate) < 0.001
            assert 0 <= actual_rate <= 1
    
    @given(outcomes=outcomes_list_strategy(min_size=10, max_size=30))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_rejection_reasons_tracking(self, outcomes: List[Dict[str, Any]]):
        """
        Property: Rejection reasons must be tracked and analyzed
        
        Validates Requirement 7.1: Track rejection reasons for improvement
        """
        service = OutcomeTrackingService()
        
        # Record all outcomes
        for outcome in outcomes:
            service.record_outcome(**outcome)
        
        # Get rejection reasons
        rejection_reasons = service.get_rejection_reasons()
        
        # Verify rejection reasons are tracked
        rejected_outcomes = [o for o in outcomes if o['actual_outcome'] == 'rejected']
        
        if rejected_outcomes:
            # Should have at least one rejection reason
            assert len(rejection_reasons) > 0
            
            # Each reason should have count and percentage
            for reason in rejection_reasons:
                assert 'reason' in reason
                assert 'count' in reason
                assert 'percentage' in reason
                assert reason['count'] > 0
                assert 0 < reason['percentage'] <= 100
            
            # Total percentage should not exceed 100
            total_percentage = sum(r['percentage'] for r in rejection_reasons)
            assert total_percentage <= 100
    
    @given(outcomes=outcomes_list_strategy(min_size=10, max_size=30))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_processing_time_analytics(self, outcomes: List[Dict[str, Any]]):
        """
        Property: Processing time analytics must be calculated correctly
        
        Validates Requirement 7.1: Track processing times for optimization
        """
        service = OutcomeTrackingService()
        
        # Record all outcomes
        for outcome in outcomes:
            service.record_outcome(**outcome)
        
        # Get processing time analytics
        analytics = service.get_processing_time_analytics()
        
        # Verify analytics structure
        assert 'average_days' in analytics
        assert 'median_days' in analytics
        assert 'min_days' in analytics
        assert 'max_days' in analytics
        assert 'sample_size' in analytics
        
        # If we have processing times, verify they're reasonable
        outcomes_with_times = [o for o in outcomes if o.get('processing_time_days') is not None]
        
        if outcomes_with_times:
            assert analytics['sample_size'] == len(outcomes_with_times)
            assert analytics['average_days'] > 0
            assert analytics['min_days'] <= analytics['average_days'] <= analytics['max_days']
    
    @given(outcomes=outcomes_list_strategy(min_size=10, max_size=30))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_benefit_amount_verification(self, outcomes: List[Dict[str, Any]]):
        """
        Property: Benefit amounts must be verified against predictions
        
        Validates Requirement 7.4: Verify actual amounts and timing against predictions
        """
        service = OutcomeTrackingService()
        
        # Record all outcomes
        for outcome in outcomes:
            service.record_outcome(**outcome)
        
        # Get benefit amount verification
        verification = service.get_benefit_amount_verification()
        
        # Verify structure
        assert 'average_amount' in verification
        assert 'median_amount' in verification
        assert 'total_disbursed' in verification
        assert 'sample_size' in verification
        
        # If we have approved outcomes with amounts
        approved_with_amounts = [
            o for o in outcomes
            if o['actual_outcome'] == 'approved' and o.get('benefit_amount_received')
        ]
        
        if approved_with_amounts:
            assert verification['sample_size'] == len(approved_with_amounts)
            assert verification['average_amount'] > 0
            assert verification['total_disbursed'] > 0
    
    @given(outcomes=outcomes_list_strategy(min_size=15, max_size=40))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_pattern_identification_for_improvement(self, outcomes: List[Dict[str, Any]]):
        """
        Property: System must identify patterns in outcomes for model improvement
        
        Validates Requirement 7.2: Retrain models to improve accuracy
        """
        service = ModelImprovementService()
        
        # Analyze outcomes for improvements
        analysis = service.analyze_outcomes_for_improvements(outcomes)
        
        # Verify analysis structure
        assert 'analysis_date' in analysis
        assert 'total_outcomes' in analysis
        assert 'demographic_patterns' in analysis
        assert 'rejection_patterns' in analysis
        assert 'prediction_errors' in analysis
        assert 'recommendations' in analysis
        
        # Verify total outcomes matches input
        assert analysis['total_outcomes'] == len(outcomes)
        
        # Verify recommendations are generated
        assert isinstance(analysis['recommendations'], list)
    
    @given(outcomes=outcomes_list_strategy(min_size=15, max_size=40))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_demographic_pattern_analysis(self, outcomes: List[Dict[str, Any]]):
        """
        Property: Demographic patterns must be identified for algorithm updates
        
        Validates Requirement 7.3: Adjust eligibility predictions based on patterns
        """
        analyzer = PatternAnalyzer()
        
        # Analyze demographic patterns
        patterns = analyzer.analyze_demographic_patterns(outcomes)
        
        # Verify patterns are identified
        assert isinstance(patterns, list)
        
        # Each pattern should have required fields
        for pattern in patterns:
            assert 'pattern_type' in pattern
            assert 'attribute' in pattern
            assert 'insights' in pattern
            assert 'recommendation' in pattern
    
    @given(outcomes=outcomes_list_strategy(min_size=15, max_size=40))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_prediction_error_analysis(self, outcomes: List[Dict[str, Any]]):
        """
        Property: Prediction errors must be analyzed for model improvement
        
        Validates Requirement 7.2: Identify and correct prediction errors
        """
        analyzer = PatternAnalyzer()
        
        # Analyze prediction errors
        error_analysis = analyzer.analyze_prediction_errors(outcomes)
        
        # Verify error analysis structure
        if 'error' not in error_analysis:
            assert 'total_predictions' in error_analysis
            assert 'false_positives' in error_analysis
            assert 'false_negatives' in error_analysis
            assert 'recommendations' in error_analysis
            
            # Verify false positive/negative tracking
            assert 'count' in error_analysis['false_positives']
            assert 'rate' in error_analysis['false_positives']
            assert 'count' in error_analysis['false_negatives']
            assert 'rate' in error_analysis['false_negatives']
            
            # Rates should be between 0 and 100
            assert 0 <= error_analysis['false_positives']['rate'] <= 100
            assert 0 <= error_analysis['false_negatives']['rate'] <= 100
    
    @given(
        current_outcomes=outcomes_list_strategy(min_size=15, max_size=30),
        previous_outcomes=outcomes_list_strategy(min_size=15, max_size=30)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_quarterly_improvement_reporting(
        self,
        current_outcomes: List[Dict[str, Any]],
        previous_outcomes: List[Dict[str, Any]]
    ):
        """
        Property: Quarterly reports must compare performance and identify improvements
        
        Validates Requirement 7.5: Update algorithms quarterly with improvement reporting
        """
        service = ModelImprovementService()
        
        # Generate quarterly report
        report = service.generate_quarterly_report(current_outcomes, previous_outcomes)
        
        # Verify report structure
        assert 'report_type' in report
        assert report['report_type'] == 'quarterly_improvement'
        assert 'report_date' in report
        assert 'quarter' in report
        assert 'current_period' in report
        assert 'comparison' in report
        assert 'improvement_actions' in report
        
        # Verify current period analysis
        assert 'total_applications' in report['current_period']
        assert 'analysis' in report['current_period']
        
        # Verify comparison metrics
        comparison = report['comparison']
        assert 'application_volume_change' in comparison
        assert 'accuracy_change' in comparison
        assert 'approval_rate_change' in comparison
        assert 'trend' in comparison
        assert comparison['trend'] in ['improving', 'declining', 'stable']
    
    @given(outcomes=outcomes_list_strategy(min_size=10, max_size=30))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_model_accuracy_metrics_calculation(self, outcomes: List[Dict[str, Any]]):
        """
        Property: Model accuracy metrics must be calculated for performance monitoring
        
        Validates Requirement 7.2: Monitor model accuracy for retraining decisions
        """
        service = OutcomeTrackingService()
        
        # Record all outcomes
        for outcome in outcomes:
            service.record_outcome(**outcome)
        
        # Get model accuracy metrics
        metrics = service.get_model_accuracy_metrics()
        
        # Verify metrics structure
        assert 'accuracy' in metrics
        assert 'sample_size' in metrics
        
        # Accuracy should be between 0 and 1
        assert 0 <= metrics['accuracy'] <= 1
        
        # If we have completed outcomes, verify detailed metrics
        completed = [o for o in outcomes if o['actual_outcome'] in ['approved', 'rejected']]
        
        if completed:
            assert metrics['sample_size'] == len(completed)
            assert 'precision' in metrics
            assert 'recall' in metrics
            assert 'f1_score' in metrics
            
            # All metrics should be between 0 and 1
            assert 0 <= metrics['precision'] <= 1
            assert 0 <= metrics['recall'] <= 1
            assert 0 <= metrics['f1_score'] <= 1
    
    @given(outcomes=outcomes_list_strategy(min_size=10, max_size=30))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_scheme_performance_reporting(self, outcomes: List[Dict[str, Any]]):
        """
        Property: Scheme-specific performance must be tracked and reported
        
        Validates Requirement 7.1: Track performance per scheme for targeted improvements
        """
        service = OutcomeTrackingService()
        
        # Record all outcomes
        for outcome in outcomes:
            service.record_outcome(**outcome)
        
        # Get unique scheme IDs
        scheme_ids = list(set(o['scheme_id'] for o in outcomes))
        
        # Generate report for first scheme
        if scheme_ids:
            report = service.get_scheme_performance_report(scheme_ids[0])
            
            # Verify report structure
            assert 'scheme_id' in report
            assert 'total_applications' in report
            assert 'approval_rate' in report
            assert 'rejection_reasons' in report
            assert 'processing_time' in report
            assert 'benefit_amounts' in report
            assert 'report_generated_at' in report
    
    @given(outcomes=outcomes_list_strategy(min_size=15, max_size=40))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_improvement_action_recording(self, outcomes: List[Dict[str, Any]]):
        """
        Property: Improvement actions must be recorded and tracked
        
        Validates Requirement 7.3: Document algorithm updates based on patterns
        """
        service = ModelImprovementService()
        
        # Analyze outcomes
        analysis = service.analyze_outcomes_for_improvements(outcomes)
        
        # Record an improvement action
        action = service.record_improvement_action(
            action_type='rule_update',
            description='Updated income threshold based on rejection patterns',
            expected_impact='Reduce false positives by 10%'
        )
        
        # Verify action is recorded
        assert 'action_id' in action
        assert action['action_type'] == 'rule_update'
        assert action['status'] == 'implemented'
        assert 'implementation_date' in action
        
        # Verify action can be retrieved
        history = service.get_improvement_history()
        assert len(history) == 1
        assert history[0]['action_id'] == action['action_id']
    
    @given(outcomes=outcomes_list_strategy(min_size=20, max_size=50))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_overall_platform_performance_reporting(self, outcomes: List[Dict[str, Any]]):
        """
        Property: Overall platform performance must be tracked across all schemes
        
        Validates Requirement 7.5: Generate comprehensive improvement reports
        """
        service = OutcomeTrackingService()
        
        # Record all outcomes
        for outcome in outcomes:
            service.record_outcome(**outcome)
        
        # Get overall performance report
        report = service.get_overall_performance_report()
        
        # Verify report structure
        assert 'total_applications' in report
        assert 'total_schemes' in report
        assert 'overall_approval_rate' in report
        assert 'top_rejection_reasons' in report
        assert 'processing_time' in report
        assert 'benefit_amounts' in report
        assert 'report_generated_at' in report
        
        # Verify metrics are reasonable
        assert report['total_applications'] == len(outcomes)
        assert report['total_schemes'] > 0
        assert 0 <= report['overall_approval_rate'] <= 1
    
    @given(outcomes=outcomes_list_strategy(min_size=15, max_size=40))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_rejection_pattern_analysis(self, outcomes: List[Dict[str, Any]]):
        """
        Property: Rejection patterns must be analyzed for root cause identification
        
        Validates Requirement 7.3: Identify patterns to adjust predictions
        """
        analyzer = PatternAnalyzer()
        
        # Analyze rejection patterns
        patterns = analyzer.analyze_rejection_patterns(outcomes)
        
        # Verify patterns structure
        assert isinstance(patterns, list)
        
        # Each pattern should have required fields
        for pattern in patterns:
            assert 'rejection_reason' in pattern
            assert 'frequency' in pattern
            assert 'percentage' in pattern
            assert 'avg_predicted_confidence' in pattern
            assert 'recommendation' in pattern
            
            # Verify metrics are reasonable
            assert pattern['frequency'] > 0
            assert 0 < pattern['percentage'] <= 100
            assert 0 <= pattern['avg_predicted_confidence'] <= 1
    
    @given(outcomes=outcomes_list_strategy(min_size=10, max_size=30))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_benefit_timing_analytics(self, outcomes: List[Dict[str, Any]]):
        """
        Property: Benefit timing must be tracked for prediction accuracy
        
        Validates Requirement 7.4: Verify timing against predictions
        """
        service = OutcomeTrackingService()
        
        # Record all outcomes
        for outcome in outcomes:
            service.record_outcome(**outcome)
        
        # Get benefit timing analytics
        timing = service.get_benefit_timing_analytics()
        
        # Verify timing structure
        assert 'average_days' in timing
        assert 'median_days' in timing
        assert 'min_days' in timing
        assert 'max_days' in timing
        assert 'sample_size' in timing
        
        # If we have timing data, verify it's reasonable
        outcomes_with_timing = [
            o for o in outcomes
            if o.get('benefit_timing_days') is not None
        ]
        
        if outcomes_with_timing:
            assert timing['sample_size'] == len(outcomes_with_timing)
            assert timing['average_days'] > 0
            assert timing['min_days'] <= timing['average_days'] <= timing['max_days']


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
