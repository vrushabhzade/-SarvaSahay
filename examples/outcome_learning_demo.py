"""
Outcome Learning and Analytics Demo
Demonstrates the outcome tracking and model improvement pipeline
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.outcome_tracking_service import OutcomeTrackingService
from services.model_improvement_service import ModelImprovementService
from datetime import datetime, timedelta


def demo_outcome_tracking():
    """Demonstrate outcome tracking functionality"""
    print("=" * 60)
    print("OUTCOME TRACKING DEMO")
    print("=" * 60)
    
    # Initialize service
    tracker = OutcomeTrackingService()
    
    # Record some sample outcomes
    print("\n1. Recording application outcomes...")
    
    # Approved applications
    for i in range(5):
        tracker.record_outcome(
            application_id=f'app-approved-{i}',
            user_id=f'user-{i}',
            scheme_id='pm-kisan',
            scheme_name='PM-KISAN',
            predicted_eligible=True,
            predicted_confidence=0.9,
            actual_outcome='approved',
            processing_time_days=15 + i,
            benefit_amount_received=6000.0,
            benefit_timing_days=7,
            user_profile={
                'demographics': {'age': 35 + i, 'caste': 'sc'},
                'economic': {'annualIncome': 80000 + i * 5000}
            }
        )
    
    # Rejected applications
    for i in range(3):
        tracker.record_outcome(
            application_id=f'app-rejected-{i}',
            user_id=f'user-{i+5}',
            scheme_id='pm-kisan',
            scheme_name='PM-KISAN',
            predicted_eligible=True,
            predicted_confidence=0.75,
            actual_outcome='rejected',
            rejection_reason='Income exceeds limit',
            processing_time_days=10,
            user_profile={
                'demographics': {'age': 40 + i, 'caste': 'general'},
                'economic': {'annualIncome': 250000 + i * 10000}
            }
        )
    
    print(f"   Recorded {tracker.get_outcome_count()} outcomes")
    
    # Get approval rate
    print("\n2. Calculating approval rate...")
    approval_rate = tracker.get_approval_rate()
    print(f"   Overall approval rate: {approval_rate:.1%}")
    
    # Get rejection reasons
    print("\n3. Analyzing rejection reasons...")
    rejection_reasons = tracker.get_rejection_reasons()
    for reason in rejection_reasons:
        print(f"   - {reason['reason']}: {reason['count']} ({reason['percentage']:.1f}%)")
    
    # Get processing time analytics
    print("\n4. Processing time analytics...")
    processing = tracker.get_processing_time_analytics()
    print(f"   Average: {processing['average_days']:.1f} days")
    print(f"   Median: {processing['median_days']:.1f} days")
    print(f"   Range: {processing['min_days']}-{processing['max_days']} days")
    
    # Get benefit verification
    print("\n5. Benefit amount verification...")
    benefits = tracker.get_benefit_amount_verification(expected_amount=6000.0)
    print(f"   Average amount: ₹{benefits['average_amount']:.2f}")
    print(f"   Total disbursed: ₹{benefits['total_disbursed']:.2f}")
    print(f"   Matches expected: {benefits['matches_expected']:.1f}%")
    
    # Get scheme performance report
    print("\n6. Scheme performance report...")
    report = tracker.get_scheme_performance_report('pm-kisan')
    print(f"   Scheme: {report['scheme_name']}")
    print(f"   Total applications: {report['total_applications']}")
    print(f"   Approval rate: {report['approval_rate']:.1%}")
    
    return tracker


def demo_model_improvement(tracker):
    """Demonstrate model improvement functionality"""
    print("\n" + "=" * 60)
    print("MODEL IMPROVEMENT DEMO")
    print("=" * 60)
    
    # Initialize service
    improvement = ModelImprovementService()
    
    # Get outcomes from tracker
    outcomes = tracker.outcomes
    
    # Analyze outcomes for improvements
    print("\n1. Analyzing outcomes for improvement opportunities...")
    analysis = improvement.analyze_outcomes_for_improvements(outcomes)
    
    print(f"   Total outcomes analyzed: {analysis['total_outcomes']}")
    print(f"   Demographic patterns found: {len(analysis['demographic_patterns'])}")
    print(f"   Rejection patterns found: {len(analysis['rejection_patterns'])}")
    
    # Show recommendations
    print("\n2. Improvement recommendations:")
    for i, rec in enumerate(analysis['recommendations'][:3], 1):
        print(f"   {i}. [{rec['type']}] {rec['recommendation']}")
    
    # Generate quarterly report
    print("\n3. Generating quarterly report...")
    report = improvement.generate_quarterly_report(outcomes)
    
    print(f"   Quarter: {report['quarter']}")
    print(f"   Applications: {report['current_period']['total_applications']}")
    print(f"   Improvement actions: {len(report['improvement_actions'])}")
    
    # Show improvement actions
    print("\n4. Prioritized improvement actions:")
    for i, action in enumerate(report['improvement_actions'][:3], 1):
        print(f"   {i}. [{action['priority'].upper()}] {action['action']}")
    
    # Record an improvement action
    print("\n5. Recording improvement action...")
    action = improvement.record_improvement_action(
        action_type='rule_update',
        description='Updated income threshold for PM-KISAN to ₹200,000',
        expected_impact='Reduce false positives by 15%'
    )
    print(f"   Action ID: {action['action_id']}")
    print(f"   Type: {action['action_type']}")
    print(f"   Status: {action['status']}")
    
    # Show improvement history
    print("\n6. Improvement history:")
    history = improvement.get_improvement_history()
    for action in history:
        print(f"   - {action['description']}")
        print(f"     Expected impact: {action['expected_impact']}")
    
    return improvement


def demo_pattern_analysis(tracker):
    """Demonstrate pattern analysis"""
    print("\n" + "=" * 60)
    print("PATTERN ANALYSIS DEMO")
    print("=" * 60)
    
    improvement = ModelImprovementService()
    outcomes = tracker.outcomes
    
    # Analyze demographic patterns
    print("\n1. Demographic patterns:")
    patterns = improvement.pattern_analyzer.analyze_demographic_patterns(outcomes)
    for pattern in patterns:
        print(f"\n   Attribute: {pattern['attribute']}")
        if pattern['insights']:
            for key, value in list(pattern['insights'].items())[:2]:
                print(f"   - {key}: {value['approval_rate']:.1f}% approval rate")
    
    # Analyze rejection patterns
    print("\n2. Rejection patterns:")
    rejections = improvement.pattern_analyzer.analyze_rejection_patterns(outcomes)
    for pattern in rejections:
        print(f"\n   Reason: {pattern['rejection_reason']}")
        print(f"   Frequency: {pattern['frequency']} ({pattern['percentage']:.1f}%)")
        print(f"   Avg confidence: {pattern['avg_predicted_confidence']:.2f}")
    
    # Analyze prediction errors
    print("\n3. Prediction error analysis:")
    errors = improvement.pattern_analyzer.analyze_prediction_errors(outcomes)
    print(f"   Total predictions: {errors['total_predictions']}")
    print(f"   False positives: {errors['false_positives']['count']} ({errors['false_positives']['rate']:.1f}%)")
    print(f"   False negatives: {errors['false_negatives']['count']} ({errors['false_negatives']['rate']:.1f}%)")
    
    print("\n   Recommendations:")
    for rec in errors['recommendations']:
        print(f"   - {rec}")


def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("SARVASAHAY OUTCOME LEARNING & ANALYTICS DEMO")
    print("=" * 60)
    print("\nThis demo showcases the outcome tracking and model improvement")
    print("capabilities of the SarvaSahay platform.")
    
    # Run demos
    tracker = demo_outcome_tracking()
    improvement = demo_model_improvement(tracker)
    demo_pattern_analysis(tracker)
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("\nKey Features Demonstrated:")
    print("✓ Application outcome tracking")
    print("✓ Approval rate calculation")
    print("✓ Rejection reason analysis")
    print("✓ Processing time analytics")
    print("✓ Benefit amount verification")
    print("✓ Pattern identification")
    print("✓ Quarterly reporting")
    print("✓ Improvement action tracking")
    print("\nThese features enable continuous model improvement and")
    print("help achieve the 89% accuracy requirement (Requirement 7.2)")
    print()


if __name__ == '__main__':
    main()
