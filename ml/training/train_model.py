"""
Model Training Script
Script to train or retrain the eligibility model
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ml.models.eligibility_model import EligibilityModel
from ml.training.retraining_pipeline import RetrainingPipeline, OutcomeTracker


def main():
    """Main training script"""
    parser = argparse.ArgumentParser(description='Train or retrain eligibility model')
    parser.add_argument(
        '--mode',
        choices=['train', 'retrain', 'report'],
        default='report',
        help='Training mode: train (initial), retrain (update), or report (show metrics)'
    )
    parser.add_argument(
        '--model-path',
        default='ml/models/saved/eligibility_model.pkl',
        help='Path to save/load model'
    )
    parser.add_argument(
        '--outcomes-path',
        default='ml/training/data/outcomes.json',
        help='Path to outcomes data'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force retraining regardless of schedule'
    )
    
    args = parser.parse_args()
    
    # Initialize components
    model = EligibilityModel()
    outcome_tracker = OutcomeTracker(storage_path=args.outcomes_path)
    pipeline = RetrainingPipeline(model, outcome_tracker, target_accuracy=0.89)
    
    if args.mode == 'report':
        # Generate performance report
        report = pipeline.get_performance_report()
        
        print("\n=== Model Performance Report ===")
        print(f"Current Accuracy: {report['current_accuracy']:.2%}")
        print(f"Recent Accuracy (30d): {report['recent_accuracy_30d']:.2%}")
        print(f"Target Accuracy: {report['target_accuracy']:.2%}")
        print(f"Meets Requirement: {'✓' if report['meets_requirement'] else '✗'}")
        print(f"\nApproval Rate: {report['approval_rate']:.2%}")
        print(f"Avg Processing Time: {report['avg_processing_time']:.1f} days")
        print(f"Total Outcomes: {report['total_outcomes']}")
        print(f"Last Training: {report['last_training_date'] or 'Never'}")
        print(f"Training History: {report['training_history_count']} runs")
        
        if report['rejection_reasons']:
            print("\nTop Rejection Reasons:")
            for reason, count in sorted(
                report['rejection_reasons'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]:
                print(f"  - {reason}: {count}")
    
    elif args.mode == 'retrain':
        # Execute retraining
        print("\n=== Model Retraining ===")
        
        should_retrain, reason = pipeline.should_retrain(force=args.force)
        print(f"Retraining Check: {reason}")
        
        if should_retrain or args.force:
            print("Starting retraining...")
            result = pipeline.retrain(save_path=args.model_path, force=args.force)
            
            if result['retrained']:
                print("✓ Retraining successful!")
                print(f"  Test Accuracy: {result['metrics']['test_accuracy']:.2%}")
                print(f"  Precision: {result['metrics']['precision']:.2%}")
                print(f"  Recall: {result['metrics']['recall']:.2%}")
                print(f"  F1 Score: {result['metrics']['f1_score']:.2%}")
                print(f"  Training Samples: {result['metrics']['n_train_samples']}")
                print(f"  Test Samples: {result['metrics']['n_test_samples']}")
                if result['model_saved']:
                    print(f"  Model saved to: {args.model_path}")
            else:
                print(f"✗ Retraining failed: {result['reason']}")
        else:
            print("No retraining needed at this time.")
    
    elif args.mode == 'train':
        print("\n=== Initial Model Training ===")
        print("Note: Initial training requires outcome data.")
        print("Use --mode retrain --force to train with available data.")


if __name__ == '__main__':
    main()
