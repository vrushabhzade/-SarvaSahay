"""
Model Improvement Service
Implements pattern identification, algorithm updates, and quarterly reporting
Requirements: 7.2, 7.3, 7.5
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics


class PatternAnalyzer:
    """
    Analyzes outcome patterns to identify improvement opportunities
    """
    
    def __init__(self):
        self.patterns: List[Dict[str, Any]] = []
    
    def analyze_demographic_patterns(
        self,
        outcomes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Identify demographic patterns in approvals/rejections
        
        Args:
            outcomes: List of application outcomes with user profiles
            
        Returns:
            List of identified patterns with recommendations
        """
        patterns = []
        
        # Filter outcomes with user profiles
        outcomes_with_profiles = [
            o for o in outcomes
            if o.get('user_profile') and o['actual_outcome'] in ['approved', 'rejected']
        ]
        
        if not outcomes_with_profiles:
            return patterns
        
        # Analyze by caste
        caste_patterns = self._analyze_by_attribute(
            outcomes_with_profiles, 'demographics', 'caste'
        )
        if caste_patterns:
            patterns.append({
                'pattern_type': 'demographic',
                'attribute': 'caste',
                'insights': caste_patterns,
                'recommendation': self._generate_demographic_recommendation(caste_patterns)
            })
        
        # Analyze by age groups
        age_patterns = self._analyze_age_patterns(outcomes_with_profiles)
        if age_patterns:
            patterns.append({
                'pattern_type': 'demographic',
                'attribute': 'age',
                'insights': age_patterns,
                'recommendation': self._generate_age_recommendation(age_patterns)
            })
        
        # Analyze by income brackets
        income_patterns = self._analyze_income_patterns(outcomes_with_profiles)
        if income_patterns:
            patterns.append({
                'pattern_type': 'economic',
                'attribute': 'income',
                'insights': income_patterns,
                'recommendation': self._generate_income_recommendation(income_patterns)
            })
        
        return patterns
    
    def analyze_rejection_patterns(
        self,
        outcomes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Identify common rejection patterns and root causes
        
        Args:
            outcomes: List of application outcomes
            
        Returns:
            List of rejection patterns with improvement suggestions
        """
        patterns = []
        
        rejected = [o for o in outcomes if o['actual_outcome'] == 'rejected']
        
        if not rejected:
            return patterns
        
        # Group by rejection reason
        reason_groups = defaultdict(list)
        for outcome in rejected:
            if outcome.get('rejection_reason'):
                reason_groups[outcome['rejection_reason']].append(outcome)
        
        # Analyze each rejection reason
        for reason, reason_outcomes in reason_groups.items():
            if len(reason_outcomes) < 3:  # Need minimum sample size
                continue
            
            # Calculate statistics
            avg_confidence = statistics.mean(
                o['predicted_confidence'] for o in reason_outcomes
            )
            
            pattern = {
                'rejection_reason': reason,
                'frequency': len(reason_outcomes),
                'percentage': (len(reason_outcomes) / len(rejected)) * 100,
                'avg_predicted_confidence': avg_confidence,
                'recommendation': self._generate_rejection_recommendation(
                    reason, avg_confidence, len(reason_outcomes)
                )
            }
            
            patterns.append(pattern)
        
        # Sort by frequency
        patterns.sort(key=lambda x: x['frequency'], reverse=True)
        
        return patterns
    
    def analyze_prediction_errors(
        self,
        outcomes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze false positives and false negatives
        
        Args:
            outcomes: List of application outcomes
            
        Returns:
            Analysis of prediction errors with improvement suggestions
        """
        completed = [
            o for o in outcomes
            if o['actual_outcome'] in ['approved', 'rejected']
        ]
        
        if not completed:
            return {'error': 'No completed applications to analyze'}
        
        false_positives = [
            o for o in completed
            if o['predicted_eligible'] and o['actual_outcome'] == 'rejected'
        ]
        
        false_negatives = [
            o for o in completed
            if not o['predicted_eligible'] and o['actual_outcome'] == 'approved'
        ]
        
        analysis = {
            'total_predictions': len(completed),
            'false_positives': {
                'count': len(false_positives),
                'rate': (len(false_positives) / len(completed)) * 100,
                'avg_confidence': statistics.mean(
                    o['predicted_confidence'] for o in false_positives
                ) if false_positives else 0.0,
                'common_reasons': self._get_common_rejection_reasons(false_positives)
            },
            'false_negatives': {
                'count': len(false_negatives),
                'rate': (len(false_negatives) / len(completed)) * 100,
                'avg_confidence': statistics.mean(
                    o['predicted_confidence'] for o in false_negatives
                ) if false_negatives else 0.0
            },
            'recommendations': self._generate_error_recommendations(
                false_positives, false_negatives
            )
        }
        
        return analysis
    
    def _analyze_by_attribute(
        self,
        outcomes: List[Dict[str, Any]],
        category: str,
        attribute: str
    ) -> Dict[str, Any]:
        """Analyze outcomes by a specific profile attribute"""
        groups = defaultdict(lambda: {'approved': 0, 'rejected': 0})
        
        for outcome in outcomes:
            try:
                value = outcome['user_profile'][category][attribute]
                groups[value][outcome['actual_outcome']] += 1
            except (KeyError, TypeError):
                continue
        
        if not groups:
            return {}
        
        results = {}
        for value, counts in groups.items():
            total = counts['approved'] + counts['rejected']
            if total > 0:
                results[value] = {
                    'total': total,
                    'approved': counts['approved'],
                    'rejected': counts['rejected'],
                    'approval_rate': (counts['approved'] / total) * 100
                }
        
        return results
    
    def _analyze_age_patterns(
        self,
        outcomes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze outcomes by age groups"""
        age_groups = {
            '18-30': (18, 30),
            '31-45': (31, 45),
            '46-60': (46, 60),
            '60+': (61, 150)
        }
        
        groups = defaultdict(lambda: {'approved': 0, 'rejected': 0})
        
        for outcome in outcomes:
            try:
                age = outcome['user_profile']['demographics']['age']
                for group_name, (min_age, max_age) in age_groups.items():
                    if min_age <= age <= max_age:
                        groups[group_name][outcome['actual_outcome']] += 1
                        break
            except (KeyError, TypeError):
                continue
        
        results = {}
        for group, counts in groups.items():
            total = counts['approved'] + counts['rejected']
            if total > 0:
                results[group] = {
                    'total': total,
                    'approved': counts['approved'],
                    'rejected': counts['rejected'],
                    'approval_rate': (counts['approved'] / total) * 100
                }
        
        return results
    
    def _analyze_income_patterns(
        self,
        outcomes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze outcomes by income brackets"""
        income_brackets = {
            'Very Low (<50k)': (0, 50000),
            'Low (50k-100k)': (50000, 100000),
            'Medium (100k-200k)': (100000, 200000),
            'High (200k+)': (200000, float('inf'))
        }
        
        groups = defaultdict(lambda: {'approved': 0, 'rejected': 0})
        
        for outcome in outcomes:
            try:
                income = outcome['user_profile']['economic']['annualIncome']
                for bracket_name, (min_income, max_income) in income_brackets.items():
                    if min_income <= income < max_income:
                        groups[bracket_name][outcome['actual_outcome']] += 1
                        break
            except (KeyError, TypeError):
                continue
        
        results = {}
        for bracket, counts in groups.items():
            total = counts['approved'] + counts['rejected']
            if total > 0:
                results[bracket] = {
                    'total': total,
                    'approved': counts['approved'],
                    'rejected': counts['rejected'],
                    'approval_rate': (counts['approved'] / total) * 100
                }
        
        return results
    
    def _get_common_rejection_reasons(
        self,
        outcomes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Get most common rejection reasons from outcomes"""
        reason_counts = defaultdict(int)
        
        for outcome in outcomes:
            if outcome.get('rejection_reason'):
                reason_counts[outcome['rejection_reason']] += 1
        
        reasons = [
            {'reason': reason, 'count': count}
            for reason, count in reason_counts.items()
        ]
        
        reasons.sort(key=lambda x: x['count'], reverse=True)
        return reasons[:5]
    
    def _generate_demographic_recommendation(
        self,
        patterns: Dict[str, Any]
    ) -> str:
        """Generate recommendation based on demographic patterns"""
        if not patterns:
            return "Insufficient data for recommendations"
        
        # Find groups with low approval rates
        low_approval = [
            (group, data['approval_rate'])
            for group, data in patterns.items()
            if data['approval_rate'] < 50
        ]
        
        if low_approval:
            groups = ', '.join(g for g, _ in low_approval)
            return f"Review eligibility criteria for {groups} - approval rates below 50%"
        
        return "Demographic patterns appear balanced"
    
    def _generate_age_recommendation(self, patterns: Dict[str, Any]) -> str:
        """Generate recommendation based on age patterns"""
        if not patterns:
            return "Insufficient age data for recommendations"
        
        # Find age groups with significantly different approval rates
        rates = [data['approval_rate'] for data in patterns.values()]
        if len(rates) > 1:
            rate_variance = max(rates) - min(rates)
            if rate_variance > 30:
                return "Significant variance in approval rates across age groups - review age-related criteria"
        
        return "Age-based approval rates are consistent"
    
    def _generate_income_recommendation(self, patterns: Dict[str, Any]) -> str:
        """Generate recommendation based on income patterns"""
        if not patterns:
            return "Insufficient income data for recommendations"
        
        # Check if higher income brackets have lower approval
        brackets = list(patterns.keys())
        if len(brackets) >= 2:
            return "Review income thresholds - ensure they align with scheme objectives"
        
        return "Income-based patterns appear appropriate"
    
    def _generate_rejection_recommendation(
        self,
        reason: str,
        avg_confidence: float,
        frequency: int
    ) -> str:
        """Generate recommendation for a rejection pattern"""
        if avg_confidence > 0.8:
            return f"High confidence predictions being rejected for '{reason}' - review eligibility rules"
        elif frequency > 10:
            return f"Frequent rejections for '{reason}' - consider adding pre-screening"
        else:
            return f"Monitor '{reason}' rejections for trends"
    
    def _generate_error_recommendations(
        self,
        false_positives: List[Dict[str, Any]],
        false_negatives: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on prediction errors"""
        recommendations = []
        
        if len(false_positives) > len(false_negatives) * 2:
            recommendations.append(
                "High false positive rate - model may be too optimistic. "
                "Consider adjusting confidence thresholds or adding stricter validation."
            )
        elif len(false_negatives) > len(false_positives) * 2:
            recommendations.append(
                "High false negative rate - model may be too conservative. "
                "Review eligibility criteria to ensure all qualified users are identified."
            )
        
        if false_positives:
            fp_reasons = self._get_common_rejection_reasons(false_positives)
            if fp_reasons:
                top_reason = fp_reasons[0]['reason']
                recommendations.append(
                    f"Most common false positive reason: '{top_reason}'. "
                    "Add this as a feature or rule in the model."
                )
        
        if not recommendations:
            recommendations.append("Prediction error rates are balanced - continue monitoring")
        
        return recommendations


class ModelImprovementService:
    """
    Service for implementing algorithm updates and quarterly reporting
    """
    
    def __init__(self):
        self.pattern_analyzer = PatternAnalyzer()
        self.improvement_history: List[Dict[str, Any]] = []
    
    def analyze_outcomes_for_improvements(
        self,
        outcomes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Comprehensive analysis of outcomes to identify improvement opportunities
        
        Args:
            outcomes: List of application outcomes
            
        Returns:
            Analysis report with identified patterns and recommendations
        """
        if not outcomes:
            return {'error': 'No outcomes to analyze'}
        
        analysis = {
            'analysis_date': datetime.now().isoformat(),
            'total_outcomes': len(outcomes),
            'demographic_patterns': self.pattern_analyzer.analyze_demographic_patterns(outcomes),
            'rejection_patterns': self.pattern_analyzer.analyze_rejection_patterns(outcomes),
            'prediction_errors': self.pattern_analyzer.analyze_prediction_errors(outcomes),
            'recommendations': []
        }
        
        # Aggregate recommendations
        for pattern in analysis['demographic_patterns']:
            if pattern.get('recommendation'):
                analysis['recommendations'].append({
                    'type': 'demographic',
                    'recommendation': pattern['recommendation']
                })
        
        for pattern in analysis['rejection_patterns']:
            if pattern.get('recommendation'):
                analysis['recommendations'].append({
                    'type': 'rejection',
                    'recommendation': pattern['recommendation']
                })
        
        if 'recommendations' in analysis['prediction_errors']:
            for rec in analysis['prediction_errors']['recommendations']:
                analysis['recommendations'].append({
                    'type': 'prediction_error',
                    'recommendation': rec
                })
        
        return analysis
    
    def generate_quarterly_report(
        self,
        outcomes: List[Dict[str, Any]],
        previous_quarter_outcomes: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive quarterly improvement report
        
        Args:
            outcomes: Current quarter outcomes
            previous_quarter_outcomes: Previous quarter outcomes for comparison
            
        Returns:
            Quarterly report with trends and recommendations
        """
        report = {
            'report_type': 'quarterly_improvement',
            'report_date': datetime.now().isoformat(),
            'quarter': self._get_current_quarter(),
            'current_period': {
                'total_applications': len(outcomes),
                'analysis': self.analyze_outcomes_for_improvements(outcomes)
            }
        }
        
        # Add comparison if previous quarter data available
        if previous_quarter_outcomes:
            report['comparison'] = self._compare_quarters(
                outcomes, previous_quarter_outcomes
            )
        
        # Add improvement recommendations
        report['improvement_actions'] = self._generate_improvement_actions(
            report['current_period']['analysis']
        )
        
        return report
    
    def record_improvement_action(
        self,
        action_type: str,
        description: str,
        expected_impact: str,
        implementation_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Record an improvement action taken based on analysis
        
        Args:
            action_type: Type of improvement (rule_update, feature_addition, etc.)
            description: Description of the improvement
            expected_impact: Expected impact on model performance
            implementation_date: When the improvement was implemented
            
        Returns:
            Recorded improvement action
        """
        action = {
            'action_id': f"improvement-{len(self.improvement_history) + 1}",
            'action_type': action_type,
            'description': description,
            'expected_impact': expected_impact,
            'implementation_date': (implementation_date or datetime.now()).isoformat(),
            'status': 'implemented'
        }
        
        self.improvement_history.append(action)
        return action
    
    def get_improvement_history(
        self,
        since_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get history of improvement actions
        
        Args:
            since_date: Optional date to filter actions after
            
        Returns:
            List of improvement actions
        """
        if not since_date:
            return self.improvement_history
        
        return [
            action for action in self.improvement_history
            if datetime.fromisoformat(action['implementation_date']) >= since_date
        ]
    
    def _get_current_quarter(self) -> str:
        """Get current quarter identifier"""
        now = datetime.now()
        quarter = (now.month - 1) // 3 + 1
        return f"Q{quarter}-{now.year}"
    
    def _compare_quarters(
        self,
        current: List[Dict[str, Any]],
        previous: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compare current quarter with previous quarter"""
        current_completed = [
            o for o in current if o['actual_outcome'] in ['approved', 'rejected']
        ]
        previous_completed = [
            o for o in previous if o['actual_outcome'] in ['approved', 'rejected']
        ]
        
        current_accuracy = (
            sum(1 for o in current_completed if o.get('correct_prediction'))
            / len(current_completed)
            if current_completed else 0.0
        )
        
        previous_accuracy = (
            sum(1 for o in previous_completed if o.get('correct_prediction'))
            / len(previous_completed)
            if previous_completed else 0.0
        )
        
        current_approval = (
            sum(1 for o in current_completed if o['actual_outcome'] == 'approved')
            / len(current_completed)
            if current_completed else 0.0
        )
        
        previous_approval = (
            sum(1 for o in previous_completed if o['actual_outcome'] == 'approved')
            / len(previous_completed)
            if previous_completed else 0.0
        )
        
        return {
            'application_volume_change': len(current) - len(previous),
            'accuracy_change': current_accuracy - previous_accuracy,
            'approval_rate_change': current_approval - previous_approval,
            'trend': self._determine_trend(current_accuracy, previous_accuracy)
        }
    
    def _determine_trend(self, current: float, previous: float) -> str:
        """Determine trend direction"""
        diff = current - previous
        if abs(diff) < 0.01:
            return 'stable'
        elif diff > 0:
            return 'improving'
        else:
            return 'declining'
    
    def _generate_improvement_actions(
        self,
        analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate actionable improvement recommendations"""
        actions = []
        
        if not analysis.get('recommendations'):
            return actions
        
        for rec in analysis['recommendations']:
            action = {
                'priority': self._determine_priority(rec),
                'type': rec['type'],
                'action': rec['recommendation'],
                'estimated_effort': 'medium',
                'expected_impact': 'improved accuracy'
            }
            actions.append(action)
        
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        actions.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        return actions
    
    def _determine_priority(self, recommendation: Dict[str, Any]) -> str:
        """Determine priority level for a recommendation"""
        rec_text = recommendation.get('recommendation', '').lower()
        
        if 'high confidence' in rec_text or 'frequent' in rec_text:
            return 'high'
        elif 'review' in rec_text or 'consider' in rec_text:
            return 'medium'
        else:
            return 'low'
