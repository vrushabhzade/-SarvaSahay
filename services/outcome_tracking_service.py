"""
Outcome Tracking Service
Tracks application outcomes for model improvement and analytics
Requirements: 7.1, 7.4
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics


class OutcomeTrackingService:
    """
    Comprehensive outcome tracking system for SarvaSahay platform
    Tracks approval rates, rejection reasons, processing times, and benefit amounts
    """
    
    def __init__(self):
        # In-memory storage (in production, this would use database)
        self.outcomes: List[Dict[str, Any]] = []
        self.scheme_stats: Dict[str, Dict[str, Any]] = defaultdict(dict)
    
    def record_outcome(
        self,
        application_id: str,
        user_id: str,
        scheme_id: str,
        scheme_name: str,
        predicted_eligible: bool,
        predicted_confidence: float,
        actual_outcome: str,
        rejection_reason: Optional[str] = None,
        processing_time_days: Optional[int] = None,
        benefit_amount_received: Optional[float] = None,
        benefit_timing_days: Optional[int] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Record application outcome for analytics and model improvement
        
        Args:
            application_id: Unique application identifier
            user_id: User profile ID
            scheme_id: Government scheme ID
            scheme_name: Scheme name for reporting
            predicted_eligible: Model's eligibility prediction
            predicted_confidence: Model's confidence score (0-1)
            actual_outcome: Actual outcome (approved, rejected, pending)
            rejection_reason: Reason for rejection if applicable
            processing_time_days: Days taken to process application
            benefit_amount_received: Actual benefit amount if approved
            benefit_timing_days: Days from approval to benefit receipt
            user_profile: User demographic data for pattern analysis
            
        Returns:
            Dictionary with recorded outcome details
        """
        if actual_outcome not in ['approved', 'rejected', 'pending']:
            raise ValueError(f"Invalid outcome: {actual_outcome}")
        
        if predicted_confidence < 0 or predicted_confidence > 1:
            raise ValueError(f"Confidence must be between 0 and 1: {predicted_confidence}")
        
        outcome = {
            'application_id': application_id,
            'user_id': user_id,
            'scheme_id': scheme_id,
            'scheme_name': scheme_name,
            'timestamp': datetime.now().isoformat(),
            'predicted_eligible': predicted_eligible,
            'predicted_confidence': predicted_confidence,
            'actual_outcome': actual_outcome,
            'rejection_reason': rejection_reason,
            'processing_time_days': processing_time_days,
            'benefit_amount_received': benefit_amount_received,
            'benefit_timing_days': benefit_timing_days,
            'user_profile': user_profile,
            'correct_prediction': self._is_prediction_correct(
                predicted_eligible, actual_outcome
            )
        }
        
        self.outcomes.append(outcome)
        self._update_scheme_stats(scheme_id, outcome)
        
        return outcome
    
    def _is_prediction_correct(self, predicted: bool, actual: str) -> bool:
        """Check if prediction matches actual outcome"""
        if actual == 'pending':
            return None  # Cannot determine yet
        return (predicted and actual == 'approved') or (not predicted and actual == 'rejected')
    
    def _update_scheme_stats(self, scheme_id: str, outcome: Dict[str, Any]) -> None:
        """Update running statistics for a scheme"""
        if scheme_id not in self.scheme_stats:
            self.scheme_stats[scheme_id] = {
                'total_applications': 0,
                'approved': 0,
                'rejected': 0,
                'pending': 0,
                'processing_times': [],
                'benefit_amounts': [],
                'rejection_reasons': defaultdict(int)
            }
        
        stats = self.scheme_stats[scheme_id]
        stats['total_applications'] += 1
        stats[outcome['actual_outcome']] += 1
        
        if outcome['processing_time_days'] is not None:
            stats['processing_times'].append(outcome['processing_time_days'])
        
        if outcome['benefit_amount_received'] is not None:
            stats['benefit_amounts'].append(outcome['benefit_amount_received'])
        
        if outcome['rejection_reason']:
            stats['rejection_reasons'][outcome['rejection_reason']] += 1
    
    def get_approval_rate(
        self,
        scheme_id: Optional[str] = None,
        since_date: Optional[datetime] = None
    ) -> float:
        """
        Calculate approval rate for all schemes or specific scheme
        
        Args:
            scheme_id: Optional scheme ID to filter by
            since_date: Optional date to filter outcomes after
            
        Returns:
            Approval rate as decimal (0.0 to 1.0)
        """
        filtered = self._filter_outcomes(scheme_id, since_date)
        
        # Only consider completed applications
        completed = [o for o in filtered if o['actual_outcome'] in ['approved', 'rejected']]
        
        if not completed:
            return 0.0
        
        approved = sum(1 for o in completed if o['actual_outcome'] == 'approved')
        return approved / len(completed)
    
    def get_rejection_reasons(
        self,
        scheme_id: Optional[str] = None,
        since_date: Optional[datetime] = None,
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get distribution of rejection reasons
        
        Args:
            scheme_id: Optional scheme ID to filter by
            since_date: Optional date to filter outcomes after
            top_n: Number of top reasons to return
            
        Returns:
            List of rejection reasons with counts and percentages
        """
        filtered = self._filter_outcomes(scheme_id, since_date)
        
        rejected = [o for o in filtered if o['actual_outcome'] == 'rejected']
        
        if not rejected:
            return []
        
        reason_counts = defaultdict(int)
        for outcome in rejected:
            if outcome['rejection_reason']:
                reason_counts[outcome['rejection_reason']] += 1
        
        total_rejected = len(rejected)
        reasons = [
            {
                'reason': reason,
                'count': count,
                'percentage': (count / total_rejected) * 100
            }
            for reason, count in reason_counts.items()
        ]
        
        # Sort by count descending
        reasons.sort(key=lambda x: x['count'], reverse=True)
        
        return reasons[:top_n]
    
    def get_processing_time_analytics(
        self,
        scheme_id: Optional[str] = None,
        since_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Calculate processing time statistics
        
        Args:
            scheme_id: Optional scheme ID to filter by
            since_date: Optional date to filter outcomes after
            
        Returns:
            Dictionary with processing time analytics
        """
        filtered = self._filter_outcomes(scheme_id, since_date)
        
        times = [
            o['processing_time_days'] for o in filtered
            if o['processing_time_days'] is not None
        ]
        
        if not times:
            return {
                'average_days': 0.0,
                'median_days': 0.0,
                'min_days': 0,
                'max_days': 0,
                'sample_size': 0
            }
        
        return {
            'average_days': statistics.mean(times),
            'median_days': statistics.median(times),
            'min_days': min(times),
            'max_days': max(times),
            'std_dev_days': statistics.stdev(times) if len(times) > 1 else 0.0,
            'sample_size': len(times)
        }
    
    def get_benefit_amount_verification(
        self,
        scheme_id: Optional[str] = None,
        expected_amount: Optional[float] = None,
        since_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Verify benefit amounts received vs expected
        
        Args:
            scheme_id: Optional scheme ID to filter by
            expected_amount: Expected benefit amount for comparison
            since_date: Optional date to filter outcomes after
            
        Returns:
            Dictionary with benefit amount analytics
        """
        filtered = self._filter_outcomes(scheme_id, since_date)
        
        approved = [
            o for o in filtered
            if o['actual_outcome'] == 'approved' and o['benefit_amount_received'] is not None
        ]
        
        if not approved:
            return {
                'average_amount': 0.0,
                'median_amount': 0.0,
                'min_amount': 0.0,
                'max_amount': 0.0,
                'total_disbursed': 0.0,
                'sample_size': 0,
                'matches_expected': None
            }
        
        amounts = [o['benefit_amount_received'] for o in approved]
        
        result = {
            'average_amount': statistics.mean(amounts),
            'median_amount': statistics.median(amounts),
            'min_amount': min(amounts),
            'max_amount': max(amounts),
            'total_disbursed': sum(amounts),
            'sample_size': len(amounts)
        }
        
        if expected_amount is not None:
            matches = sum(1 for amt in amounts if abs(amt - expected_amount) < 0.01)
            result['matches_expected'] = (matches / len(amounts)) * 100
            result['expected_amount'] = expected_amount
        
        return result
    
    def get_benefit_timing_analytics(
        self,
        scheme_id: Optional[str] = None,
        since_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Analyze timing from approval to benefit receipt
        
        Args:
            scheme_id: Optional scheme ID to filter by
            since_date: Optional date to filter outcomes after
            
        Returns:
            Dictionary with benefit timing analytics
        """
        filtered = self._filter_outcomes(scheme_id, since_date)
        
        timings = [
            o['benefit_timing_days'] for o in filtered
            if o['benefit_timing_days'] is not None
        ]
        
        if not timings:
            return {
                'average_days': 0.0,
                'median_days': 0.0,
                'min_days': 0,
                'max_days': 0,
                'sample_size': 0
            }
        
        return {
            'average_days': statistics.mean(timings),
            'median_days': statistics.median(timings),
            'min_days': min(timings),
            'max_days': max(timings),
            'sample_size': len(timings)
        }
    
    def get_scheme_performance_report(
        self,
        scheme_id: str,
        since_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive performance report for a scheme
        
        Args:
            scheme_id: Scheme ID to analyze
            since_date: Optional date to filter outcomes after
            
        Returns:
            Comprehensive performance report
        """
        filtered = self._filter_outcomes(scheme_id, since_date)
        
        if not filtered:
            return {
                'scheme_id': scheme_id,
                'error': 'No data available for this scheme'
            }
        
        return {
            'scheme_id': scheme_id,
            'scheme_name': filtered[0]['scheme_name'] if filtered else 'Unknown',
            'total_applications': len(filtered),
            'approval_rate': self.get_approval_rate(scheme_id, since_date),
            'rejection_reasons': self.get_rejection_reasons(scheme_id, since_date),
            'processing_time': self.get_processing_time_analytics(scheme_id, since_date),
            'benefit_amounts': self.get_benefit_amount_verification(scheme_id, since_date=since_date),
            'benefit_timing': self.get_benefit_timing_analytics(scheme_id, since_date),
            'report_generated_at': datetime.now().isoformat()
        }
    
    def get_overall_performance_report(
        self,
        since_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate overall platform performance report
        
        Args:
            since_date: Optional date to filter outcomes after
            
        Returns:
            Platform-wide performance report
        """
        filtered = self._filter_outcomes(None, since_date)
        
        if not filtered:
            return {
                'error': 'No data available'
            }
        
        # Get unique schemes
        schemes = set(o['scheme_id'] for o in filtered)
        
        return {
            'total_applications': len(filtered),
            'total_schemes': len(schemes),
            'overall_approval_rate': self.get_approval_rate(None, since_date),
            'top_rejection_reasons': self.get_rejection_reasons(None, since_date, top_n=5),
            'processing_time': self.get_processing_time_analytics(None, since_date),
            'benefit_amounts': self.get_benefit_amount_verification(None, since_date=since_date),
            'benefit_timing': self.get_benefit_timing_analytics(None, since_date),
            'report_generated_at': datetime.now().isoformat()
        }
    
    def get_model_accuracy_metrics(
        self,
        scheme_id: Optional[str] = None,
        since_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Calculate model prediction accuracy metrics
        
        Args:
            scheme_id: Optional scheme ID to filter by
            since_date: Optional date to filter outcomes after
            
        Returns:
            Model accuracy metrics
        """
        filtered = self._filter_outcomes(scheme_id, since_date)
        
        # Only consider completed applications
        completed = [o for o in filtered if o['actual_outcome'] in ['approved', 'rejected']]
        
        if not completed:
            return {
                'accuracy': 0.0,
                'sample_size': 0
            }
        
        correct = sum(1 for o in completed if o['correct_prediction'])
        accuracy = correct / len(completed)
        
        # Calculate precision and recall
        true_positives = sum(
            1 for o in completed
            if o['predicted_eligible'] and o['actual_outcome'] == 'approved'
        )
        false_positives = sum(
            1 for o in completed
            if o['predicted_eligible'] and o['actual_outcome'] == 'rejected'
        )
        false_negatives = sum(
            1 for o in completed
            if not o['predicted_eligible'] and o['actual_outcome'] == 'approved'
        )
        
        precision = (
            true_positives / (true_positives + false_positives)
            if (true_positives + false_positives) > 0 else 0.0
        )
        recall = (
            true_positives / (true_positives + false_negatives)
            if (true_positives + false_negatives) > 0 else 0.0
        )
        f1_score = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0 else 0.0
        )
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'sample_size': len(completed),
            'true_positives': true_positives,
            'false_positives': false_positives,
            'false_negatives': false_negatives
        }
    
    def _filter_outcomes(
        self,
        scheme_id: Optional[str] = None,
        since_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Filter outcomes by scheme and date"""
        filtered = self.outcomes
        
        if scheme_id:
            filtered = [o for o in filtered if o['scheme_id'] == scheme_id]
        
        if since_date:
            filtered = [
                o for o in filtered
                if datetime.fromisoformat(o['timestamp']) >= since_date
            ]
        
        return filtered
    
    def get_outcome_count(self, scheme_id: Optional[str] = None) -> int:
        """Get total number of recorded outcomes"""
        if scheme_id:
            return len([o for o in self.outcomes if o['scheme_id'] == scheme_id])
        return len(self.outcomes)
    
    def clear_outcomes(self) -> None:
        """Clear all recorded outcomes (for testing)"""
        self.outcomes = []
        self.scheme_stats = defaultdict(dict)
