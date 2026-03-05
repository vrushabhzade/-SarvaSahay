"""
Model Retraining Pipeline
Implements quarterly model retraining with outcome tracking and accuracy monitoring
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json
from ml.models.eligibility_model import EligibilityModel
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


class OutcomeTracker:
    """
    Tracks application outcomes for model improvement
    Monitors approval rates, rejection reasons, and processing times
    """
    
    def __init__(self, storage_path: str = "ml/training/data/outcomes.json"):
        self.storage_path = storage_path
        self.outcomes: List[Dict[str, Any]] = []
        self._load_outcomes()
    
    def _load_outcomes(self) -> None:
        """Load existing outcomes from storage"""
        path = Path(self.storage_path)
        if path.exists():
            with open(path, 'r') as f:
                self.outcomes = json.load(f)
    
    def _save_outcomes(self) -> None:
        """Save outcomes to storage"""
        path = Path(self.storage_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.outcomes, f, indent=2)
    
    def record_outcome(
        self,
        application_id: str,
        user_profile: Dict[str, Any],
        scheme_id: str,
        predicted_eligible: bool,
        predicted_confidence: float,
        actual_outcome: str,  # approved, rejected, pending
        rejection_reason: Optional[str] = None,
        processing_time_days: Optional[int] = None,
        benefit_amount_received: Optional[float] = None
    ) -> None:
        """
        Record application outcome for model learning
        
        Args:
            application_id: Unique application identifier
            user_profile: User demographic and economic data
            scheme_id: Government scheme ID
            predicted_eligible: Model's eligibility prediction
            predicted_confidence: Model's confidence score
            actual_outcome: Actual application outcome
            rejection_reason: Reason for rejection if applicable
            processing_time_days: Days taken to process application
            benefit_amount_received: Actual benefit amount if approved
        """
        outcome = {
            'application_id': application_id,
            'timestamp': datetime.now().isoformat(),
            'user_profile': user_profile,
            'scheme_id': scheme_id,
            'predicted_eligible': predicted_eligible,
            'predicted_confidence': predicted_confidence,
            'actual_outcome': actual_outcome,
            'rejection_reason': rejection_reason,
            'processing_time_days': processing_time_days,
            'benefit_amount_received': benefit_amount_received,
            'correct_prediction': (predicted_eligible and actual_outcome == 'approved') or 
                                 (not predicted_eligible and actual_outcome == 'rejected')
        }
        
        self.outcomes.append(outcome)
        self._save_outcomes()
    
    def get_approval_rate(self, scheme_id: Optional[str] = None) -> float:
        """Calculate approval rate for all or specific scheme"""
        filtered = self.outcomes
        if scheme_id:
            filtered = [o for o in self.outcomes if o['scheme_id'] == scheme_id]
        
        if not filtered:
            return 0.0
        
        approved = sum(1 for o in filtered if o['actual_outcome'] == 'approved')
        return approved / len(filtered)
    
    def get_rejection_reasons(self, scheme_id: Optional[str] = None) -> Dict[str, int]:
        """Get distribution of rejection reasons"""
        filtered = self.outcomes
        if scheme_id:
            filtered = [o for o in self.outcomes if o['scheme_id'] == scheme_id]
        
        reasons = {}
        for outcome in filtered:
            if outcome['actual_outcome'] == 'rejected' and outcome['rejection_reason']:
                reason = outcome['rejection_reason']
                reasons[reason] = reasons.get(reason, 0) + 1
        
        return reasons
    
    def get_average_processing_time(self, scheme_id: Optional[str] = None) -> float:
        """Calculate average processing time in days"""
        filtered = self.outcomes
        if scheme_id:
            filtered = [o for o in self.outcomes if o['scheme_id'] == scheme_id]
        
        times = [o['processing_time_days'] for o in filtered 
                if o['processing_time_days'] is not None]
        
        return sum(times) / len(times) if times else 0.0
    
    def get_model_accuracy(self, since_date: Optional[datetime] = None) -> float:
        """Calculate model prediction accuracy"""
        filtered = self.outcomes
        
        if since_date:
            filtered = [o for o in self.outcomes 
                       if datetime.fromisoformat(o['timestamp']) >= since_date]
        
        # Only consider completed applications (approved or rejected)
        completed = [o for o in filtered if o['actual_outcome'] in ['approved', 'rejected']]
        
        if not completed:
            return 0.0
        
        correct = sum(1 for o in completed if o['correct_prediction'])
        return correct / len(completed)
    
    def get_training_data(self, min_samples: int = 100) -> Tuple[List[Dict[str, Any]], List[int]]:
        """
        Extract training data from outcomes
        
        Args:
            min_samples: Minimum number of samples required
            
        Returns:
            Tuple of (features, labels) for model training
        """
        # Only use completed applications
        completed = [o for o in self.outcomes 
                    if o['actual_outcome'] in ['approved', 'rejected']]
        
        if len(completed) < min_samples:
            raise ValueError(f"Insufficient training data: {len(completed)} < {min_samples}")
        
        features = []
        labels = []
        
        for outcome in completed:
            features.append({
                'user_profile': outcome['user_profile'],
                'scheme_id': outcome['scheme_id']
            })
            labels.append(1 if outcome['actual_outcome'] == 'approved' else 0)
        
        return features, labels
    
    def get_outcome_count(self) -> int:
        """Get total number of recorded outcomes"""
        return len(self.outcomes)


class RetrainingPipeline:
    """
    Quarterly model retraining pipeline
    Achieves and maintains 89% accuracy requirement
    """
    
    def __init__(
        self,
        model: EligibilityModel,
        outcome_tracker: OutcomeTracker,
        target_accuracy: float = 0.89
    ):
        self.model = model
        self.outcome_tracker = outcome_tracker
        self.target_accuracy = target_accuracy
        self.training_history: List[Dict[str, Any]] = []
        self.last_training_date: Optional[datetime] = None
    
    def should_retrain(self, force: bool = False) -> Tuple[bool, str]:
        """
        Determine if model should be retrained
        
        Args:
            force: Force retraining regardless of schedule
            
        Returns:
            Tuple of (should_retrain, reason)
        """
        if force:
            return True, "Forced retraining requested"
        
        # Check if quarterly retraining is due
        if self.last_training_date:
            days_since_training = (datetime.now() - self.last_training_date).days
            if days_since_training >= 90:  # Quarterly = 90 days
                return True, f"Quarterly retraining due ({days_since_training} days since last training)"
        else:
            return True, "Initial training required"
        
        # Check if accuracy has dropped below threshold
        recent_accuracy = self.outcome_tracker.get_model_accuracy(
            since_date=datetime.now() - timedelta(days=30)
        )
        
        if recent_accuracy > 0 and recent_accuracy < self.target_accuracy:
            return True, f"Accuracy dropped to {recent_accuracy:.2%} (target: {self.target_accuracy:.2%})"
        
        # Check if sufficient new data is available
        outcome_count = self.outcome_tracker.get_outcome_count()
        if outcome_count >= 500:  # Retrain with 500+ new outcomes
            return True, f"Sufficient new data available ({outcome_count} outcomes)"
        
        return False, "No retraining needed"
    
    def prepare_training_data(
        self,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Prepare training and test data from outcomes
        
        Args:
            test_size: Proportion of data for testing
            random_state: Random seed for reproducibility
            
        Returns:
            Tuple of (X_train, X_test, y_train, y_test)
        """
        # Get training data from outcome tracker
        features_raw, labels = self.outcome_tracker.get_training_data(min_samples=100)
        
        # Engineer features for each sample
        X = []
        for feature_dict in features_raw:
            # Get scheme data (simplified - in production would fetch from database)
            scheme = {'schemeId': feature_dict['scheme_id'], 'benefitAmount': 50000}
            
            # Engineer features using model's feature engineering
            feature_vector = self.model.engineer_features(
                feature_dict['user_profile'],
                scheme
            )
            X.append(feature_vector.flatten())
        
        X = np.array(X)
        y = np.array(labels)
        
        # Split into train and test sets
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        return X_train, X_test, y_train, y_test
    
    def train_model(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> Dict[str, float]:
        """
        Train the model and evaluate performance
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_test: Test features
            y_test: Test labels
            
        Returns:
            Dictionary of performance metrics
        """
        # Train the model
        training_metrics = self.model.train(X_train, y_train)
        
        # Evaluate on test set
        y_pred = self.model.model.predict(X_test)
        
        metrics = {
            'train_accuracy': training_metrics['accuracy'],
            'test_accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, zero_division=0),
            'recall': recall_score(y_test, y_pred, zero_division=0),
            'f1_score': f1_score(y_test, y_pred, zero_division=0),
            'n_train_samples': len(y_train),
            'n_test_samples': len(y_test),
            'training_date': datetime.now().isoformat()
        }
        
        return metrics
    
    def retrain(
        self,
        save_path: Optional[str] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Execute model retraining pipeline
        
        Args:
            save_path: Path to save retrained model
            force: Force retraining regardless of schedule
            
        Returns:
            Dictionary with retraining results and metrics
        """
        # Check if retraining is needed
        should_retrain, reason = self.should_retrain(force=force)
        
        if not should_retrain:
            return {
                'retrained': False,
                'reason': reason,
                'current_accuracy': self.outcome_tracker.get_model_accuracy()
            }
        
        try:
            # Prepare training data
            X_train, X_test, y_train, y_test = self.prepare_training_data()
            
            # Train model
            metrics = self.train_model(X_train, y_train, X_test, y_test)
            
            # Check if new model meets accuracy requirement
            if metrics['test_accuracy'] < self.target_accuracy:
                return {
                    'retrained': False,
                    'reason': f"New model accuracy {metrics['test_accuracy']:.2%} below target {self.target_accuracy:.2%}",
                    'metrics': metrics
                }
            
            # Save model if path provided
            if save_path:
                self.model.save_model(save_path)
            
            # Update training history
            self.last_training_date = datetime.now()
            self.training_history.append({
                'date': self.last_training_date.isoformat(),
                'reason': reason,
                'metrics': metrics
            })
            
            return {
                'retrained': True,
                'reason': reason,
                'metrics': metrics,
                'model_saved': save_path is not None
            }
            
        except Exception as e:
            return {
                'retrained': False,
                'reason': f"Retraining failed: {str(e)}",
                'error': str(e)
            }
    
    def get_training_history(self) -> List[Dict[str, Any]]:
        """Get history of all training runs"""
        return self.training_history
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive performance report
        
        Returns:
            Dictionary with model performance metrics and insights
        """
        current_accuracy = self.outcome_tracker.get_model_accuracy()
        recent_accuracy = self.outcome_tracker.get_model_accuracy(
            since_date=datetime.now() - timedelta(days=30)
        )
        
        return {
            'current_accuracy': current_accuracy,
            'recent_accuracy_30d': recent_accuracy,
            'target_accuracy': self.target_accuracy,
            'meets_requirement': current_accuracy >= self.target_accuracy,
            'approval_rate': self.outcome_tracker.get_approval_rate(),
            'avg_processing_time': self.outcome_tracker.get_average_processing_time(),
            'total_outcomes': self.outcome_tracker.get_outcome_count(),
            'last_training_date': self.last_training_date.isoformat() if self.last_training_date else None,
            'training_history_count': len(self.training_history),
            'rejection_reasons': self.outcome_tracker.get_rejection_reasons()
        }
