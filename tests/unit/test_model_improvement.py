"""
Unit tests for Model Improvement Service
Tests pattern analysis, algorithm updates, and quarterly reporting
"""

import pytest
from datetime import datetime, timedelta
from services.model_improvement_service import (
    PatternAnalyzer,
    ModelImprovementService
)


@pytest.fixture
def pattern_analyzer():
    """Create pattern analyzer for testing"""
    return PatternAnalyzer()


@pytest.fixture
def improvement_service():
    """Create improvement service for testing"""
    return ModelImprovementService()


@pytest.fixture
def sample_outcomes():
    """Sample outcomes with user profiles"""
    return [
        {
            'application_id': 'app-1',
            'scheme_id': 'scheme-001',
            'scheme_name': 'PM-KISAN',
            'predicted_eligible': True,
            'predicted_confidence': 0.9,
            'actual_outcome': 'approved',
            'user_profile': {
                'demographics': {'age': 35, 'caste': 'sc'},
                'economic': {'annualIncome': 80000}
            },
            'correct_prediction': True
        },
        {
            'application_id': 'app-2',
            'scheme_id': 'scheme-001',
            'scheme_name': 'PM-KISAN',
            'predicted_eligible': True,
            'predicted_confidence': 0.85,
            'actual_outcome': 'rejected',
            'rejection_reason': 'Income exceeds limit',
            'user_profile': {
                'demographics': {'age': 45, 'caste': 'general'},
                'economic': {'annualIncome': 250000}
            },
            'correct_prediction': False
        },
        {
            'application_id': 'app-3',
            'scheme_id': 'scheme-001',
            'scheme_name': 'PM-KISAN',
            'predicted_eligible': False,
            'predicted_confidence': 0.6,
            'actual_outcome': 'approved',
            'user_profile': {
                'demographics': {'age': 28, 'caste': 'st'},
                'economic': {'annualIncome': 60000}
            },
            'correct_prediction': False
        }
    ]


class TestPatternAnalyzer:
    """Test pattern analysis functionality"""
    
    def test_analyze_demographic_patterns(self, pattern_analyzer, sample_outcomes):
        """Test demographic pattern analysis"""
        patterns = pattern_analyzer.analyze_demographic_patterns(sample_outcomes)
        
        assert isinstance(patterns, list)
        assert len(patterns) > 0
        
        # Check for caste patterns
        caste_pattern = next(
            (p for p in patterns if p['attribute'] == 'caste'),
            None
        )
        assert caste_pattern is not None
        assert 'insights' in caste_pattern
        assert 'recommendation' in caste_pattern
    
    def test_analyze_rejection_patterns(self, pattern_analyzer, sample_outcomes):
        """Test rejection pattern analysis"""
        patterns = pattern_analyzer.analyze_rejection_patterns(sample_outcomes)
        
        assert isinstance(patterns, list)
        
        if patterns:
            pattern = patterns[0]
            assert 'rejection_reason' in pattern
            assert 'frequency' in pattern
            assert 'percentage' in pattern
            assert 'recommendation' in pattern
    
    def test_analyze_prediction_errors(self, pattern_analyzer, sample_outcomes):
        """Test prediction error analysis"""
        analysis = pattern_analyzer.analyze_prediction_errors(sample_outcomes)
        
        assert 'total_predictions' in analysis
        assert 'false_positives' in analysis
        assert 'false_negatives' in analysis
        assert 'recommendations' in analysis
        
        assert analysis['total_predictions'] == 3
        assert analysis['false_positives']['count'] == 1
        assert analysis['false_negatives']['count'] == 1
    
    def test_analyze_age_patterns(self, pattern_analyzer):
        """Test age group pattern analysis"""
        outcomes = [
            {
                'application_id': f'app-{i}',
                'actual_outcome': 'approved' if i % 2 == 0 else 'rejected',
                'user_profile': {
                    'demographics': {'age': 20 + i * 10}
                }
            }
            for i in range(5)
        ]
        
        patterns = pattern_analyzer.analyze_demographic_patterns(outcomes)
        
        # Should have age patterns
        age_pattern = next(
            (p for p in patterns if p['attribute'] == 'age'),
            None
        )
        assert age_pattern is not None
    
    def test_analyze_income_patterns(self, pattern_analyzer):
        """Test income bracket pattern analysis"""
        outcomes = [
            {
                'application_id': f'app-{i}',
                'actual_outcome': 'approved' if i < 3 else 'rejected',
                'user_profile': {
                    'economic': {'annualIncome': 40000 + i * 50000}
                }
            }
            for i in range(5)
        ]
        
        patterns = pattern_analyzer.analyze_demographic_patterns(outcomes)
        
        # Should have income patterns
        income_pattern = next(
            (p for p in patterns if p['attribute'] == 'income'),
            None
        )
        assert income_pattern is not None


class TestModelImprovementService:
    """Test model improvement service"""
    
    def test_analyze_outcomes_for_improvements(
        self,
        improvement_service,
        sample_outcomes
    ):
        """Test comprehensive outcome analysis"""
        analysis = improvement_service.analyze_outcomes_for_improvements(
            sample_outcomes
        )
        
        assert 'analysis_date' in analysis
        assert 'total_outcomes' in analysis
        assert 'demographic_patterns' in analysis
        assert 'rejection_patterns' in analysis
        assert 'prediction_errors' in analysis
        assert 'recommendations' in analysis
        
        assert analysis['total_outcomes'] == 3
    
    def test_analyze_empty_outcomes(self, improvement_service):
        """Test analysis with no outcomes"""
        analysis = improvement_service.analyze_outcomes_for_improvements([])
        
        assert 'error' in analysis
    
    def test_generate_quarterly_report(self, improvement_service, sample_outcomes):
        """Test quarterly report generation"""
        report = improvement_service.generate_quarterly_report(sample_outcomes)
        
        assert 'report_type' in report
        assert report['report_type'] == 'quarterly_improvement'
        assert 'report_date' in report
        assert 'quarter' in report
        assert 'current_period' in report
        assert 'improvement_actions' in report
        
        assert report['current_period']['total_applications'] == 3
    
    def test_quarterly_report_with_comparison(
        self,
        improvement_service,
        sample_outcomes
    ):
        """Test quarterly report with previous quarter comparison"""
        previous_outcomes = [
            {
                'application_id': 'prev-1',
                'predicted_eligible': True,
                'predicted_confidence': 0.8,
                'actual_outcome': 'approved',
                'correct_prediction': True
            },
            {
                'application_id': 'prev-2',
                'predicted_eligible': True,
                'predicted_confidence': 0.75,
                'actual_outcome': 'approved',
                'correct_prediction': True
            }
        ]
        
        report = improvement_service.generate_quarterly_report(
            sample_outcomes,
            previous_quarter_outcomes=previous_outcomes
        )
        
        assert 'comparison' in report
        assert 'application_volume_change' in report['comparison']
        assert 'accuracy_change' in report['comparison']
        assert 'trend' in report['comparison']
    
    def test_record_improvement_action(self, improvement_service):
        """Test recording improvement actions"""
        action = improvement_service.record_improvement_action(
            action_type='rule_update',
            description='Updated income threshold for PM-KISAN',
            expected_impact='Reduce false positives by 10%'
        )
        
        assert 'action_id' in action
        assert action['action_type'] == 'rule_update'
        assert action['status'] == 'implemented'
        assert 'implementation_date' in action
    
    def test_get_improvement_history(self, improvement_service):
        """Test retrieving improvement history"""
        # Record some actions
        improvement_service.record_improvement_action(
            action_type='feature_addition',
            description='Added land ownership feature',
            expected_impact='Improve accuracy by 5%'
        )
        
        improvement_service.record_improvement_action(
            action_type='rule_update',
            description='Updated age criteria',
            expected_impact='Better age-based predictions'
        )
        
        history = improvement_service.get_improvement_history()
        
        assert len(history) == 2
        assert history[0]['action_type'] == 'feature_addition'
        assert history[1]['action_type'] == 'rule_update'
    
    def test_get_improvement_history_filtered(self, improvement_service):
        """Test retrieving improvement history with date filter"""
        # Record action in the past
        past_date = datetime.now() - timedelta(days=100)
        improvement_service.record_improvement_action(
            action_type='old_action',
            description='Old improvement',
            expected_impact='Some impact',
            implementation_date=past_date
        )
        
        # Record recent action
        improvement_service.record_improvement_action(
            action_type='recent_action',
            description='Recent improvement',
            expected_impact='Recent impact'
        )
        
        # Filter to last 30 days
        since_date = datetime.now() - timedelta(days=30)
        recent_history = improvement_service.get_improvement_history(
            since_date=since_date
        )
        
        assert len(recent_history) == 1
        assert recent_history[0]['action_type'] == 'recent_action'


class TestRejectionPatternAnalysis:
    """Test rejection pattern analysis in detail"""
    
    def test_high_frequency_rejection_pattern(self, pattern_analyzer):
        """Test identification of high-frequency rejection patterns"""
        outcomes = []
        
        # Create 15 rejections with same reason
        for i in range(15):
            outcomes.append({
                'application_id': f'app-{i}',
                'predicted_eligible': True,
                'predicted_confidence': 0.85,
                'actual_outcome': 'rejected',
                'rejection_reason': 'Missing documents'
            })
        
        # Add some other rejections
        for i in range(5):
            outcomes.append({
                'application_id': f'app-other-{i}',
                'predicted_eligible': True,
                'predicted_confidence': 0.8,
                'actual_outcome': 'rejected',
                'rejection_reason': 'Income too high'
            })
        
        patterns = pattern_analyzer.analyze_rejection_patterns(outcomes)
        
        assert len(patterns) == 2
        assert patterns[0]['rejection_reason'] == 'Missing documents'
        assert patterns[0]['frequency'] == 15
        assert patterns[0]['percentage'] == 75.0
    
    def test_high_confidence_rejection_pattern(self, pattern_analyzer):
        """Test identification of high-confidence rejections"""
        outcomes = []
        
        # Create rejections with high confidence
        for i in range(5):
            outcomes.append({
                'application_id': f'app-{i}',
                'predicted_eligible': True,
                'predicted_confidence': 0.95,
                'actual_outcome': 'rejected',
                'rejection_reason': 'Age not eligible'
            })
        
        patterns = pattern_analyzer.analyze_rejection_patterns(outcomes)
        
        assert len(patterns) == 1
        assert patterns[0]['avg_predicted_confidence'] == 0.95
        assert 'High confidence' in patterns[0]['recommendation']


class TestQuarterlyReporting:
    """Test quarterly reporting functionality"""
    
    def test_quarter_identification(self, improvement_service):
        """Test correct quarter identification"""
        report = improvement_service.generate_quarterly_report([
            {
                'application_id': 'app-1',
                'predicted_eligible': True,
                'predicted_confidence': 0.9,
                'actual_outcome': 'approved',
                'correct_prediction': True
            }
        ])
        
        # Quarter should be in format Q1-2024, Q2-2024, etc.
        assert 'quarter' in report
        assert report['quarter'].startswith('Q')
        assert '-' in report['quarter']
    
    def test_improvement_actions_prioritization(self, improvement_service):
        """Test that improvement actions are prioritized"""
        outcomes = []
        
        # Create outcomes that will generate multiple recommendations
        for i in range(10):
            outcomes.append({
                'application_id': f'app-{i}',
                'predicted_eligible': True,
                'predicted_confidence': 0.95,
                'actual_outcome': 'rejected',
                'rejection_reason': 'Income exceeds limit',
                'user_profile': {
                    'demographics': {'age': 30 + i},
                    'economic': {'annualIncome': 200000 + i * 10000}
                },
                'correct_prediction': False
            })
        
        report = improvement_service.generate_quarterly_report(outcomes)
        
        assert 'improvement_actions' in report
        actions = report['improvement_actions']
        
        if actions:
            # Check that actions have priority
            for action in actions:
                assert 'priority' in action
                assert action['priority'] in ['high', 'medium', 'low']
    
    def test_trend_determination(self, improvement_service):
        """Test trend determination in quarterly comparison"""
        current = [
            {
                'application_id': f'app-{i}',
                'predicted_eligible': True,
                'predicted_confidence': 0.9,
                'actual_outcome': 'approved',
                'correct_prediction': True
            }
            for i in range(10)
        ]
        
        previous = [
            {
                'application_id': f'prev-{i}',
                'predicted_eligible': True,
                'predicted_confidence': 0.8,
                'actual_outcome': 'approved' if i < 7 else 'rejected',
                'correct_prediction': i < 7
            }
            for i in range(10)
        ]
        
        report = improvement_service.generate_quarterly_report(
            current,
            previous_quarter_outcomes=previous
        )
        
        assert 'comparison' in report
        assert report['comparison']['trend'] in ['improving', 'declining', 'stable']


class TestPredictionErrorAnalysis:
    """Test prediction error analysis in detail"""
    
    def test_false_positive_analysis(self, pattern_analyzer):
        """Test false positive analysis"""
        outcomes = []
        
        # Create false positives
        for i in range(10):
            outcomes.append({
                'application_id': f'app-{i}',
                'predicted_eligible': True,
                'predicted_confidence': 0.85,
                'actual_outcome': 'rejected',
                'rejection_reason': 'Income exceeds limit',
                'correct_prediction': False
            })
        
        # Add some true positives
        for i in range(3):
            outcomes.append({
                'application_id': f'app-tp-{i}',
                'predicted_eligible': True,
                'predicted_confidence': 0.9,
                'actual_outcome': 'approved',
                'correct_prediction': True
            })
        
        analysis = pattern_analyzer.analyze_prediction_errors(outcomes)
        
        assert analysis['false_positives']['count'] == 10
        assert analysis['false_positives']['rate'] > 50
        assert len(analysis['recommendations']) > 0
    
    def test_false_negative_analysis(self, pattern_analyzer):
        """Test false negative analysis"""
        outcomes = []
        
        # Create false negatives
        for i in range(8):
            outcomes.append({
                'application_id': f'app-{i}',
                'predicted_eligible': False,
                'predicted_confidence': 0.6,
                'actual_outcome': 'approved',
                'correct_prediction': False
            })
        
        # Add some true negatives
        for i in range(2):
            outcomes.append({
                'application_id': f'app-tn-{i}',
                'predicted_eligible': False,
                'predicted_confidence': 0.7,
                'actual_outcome': 'rejected',
                'correct_prediction': True
            })
        
        analysis = pattern_analyzer.analyze_prediction_errors(outcomes)
        
        assert analysis['false_negatives']['count'] == 8
        assert analysis['false_negatives']['rate'] > 50
        assert len(analysis['recommendations']) > 0
