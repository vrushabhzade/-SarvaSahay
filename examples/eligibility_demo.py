"""
Eligibility Engine Demo
Demonstrates the enhanced AI/ML capabilities
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.eligibility_engine import EligibilityEngine


def main():
    """Demonstrate eligibility engine capabilities"""
    
    print("=" * 60)
    print("SarvaSahay Eligibility Engine Demo")
    print("Enhanced with XGBoost ML and Comprehensive Scheme Database")
    print("=" * 60)
    
    # Initialize engine
    print("\n1. Initializing Eligibility Engine...")
    engine = EligibilityEngine()
    
    print(f"   ✓ Loaded {engine.get_scheme_count()} government schemes")
    print(f"   ✓ Configured {engine.get_total_rule_count()} eligibility rules")
    print(f"   ✓ Target accuracy: {engine.get_model_accuracy():.0%}")
    
    # Sample user profile - rural farmer
    print("\n2. Sample User Profile: Rural Farmer")
    user_profile = {
        "profileId": "demo-user-001",
        "demographics": {
            "age": 45,
            "gender": "male",
            "caste": "SC",
            "maritalStatus": "married"
        },
        "economic": {
            "annualIncome": 80000,
            "landOwnership": 1.5,
            "employmentStatus": "farmer"
        },
        "location": {
            "state": "Maharashtra",
            "district": "Pune",
            "block": "Haveli",
            "village": "Pirangut"
        },
        "family": {
            "size": 5,
            "dependents": 3
        }
    }
    
    print(f"   - Age: {user_profile['demographics']['age']}")
    print(f"   - Caste: {user_profile['demographics']['caste']}")
    print(f"   - Income: ₹{user_profile['economic']['annualIncome']:,}")
    print(f"   - Land: {user_profile['economic']['landOwnership']} hectares")
    print(f"   - Employment: {user_profile['economic']['employmentStatus']}")
    print(f"   - Family Size: {user_profile['family']['size']}")
    
    # Evaluate eligibility
    print("\n3. Evaluating Eligibility (Rule-Based Engine)...")
    eligible_schemes = engine.evaluate_eligibility(user_profile)
    
    print(f"   ✓ Found {len(eligible_schemes)} eligible schemes")
    
    # Display top 5 schemes
    print("\n4. Top Eligible Schemes:")
    for i, scheme in enumerate(eligible_schemes[:5], 1):
        print(f"\n   {i}. {scheme['name']}")
        print(f"      Scheme ID: {scheme['schemeId']}")
        print(f"      Benefit: ₹{scheme['benefitAmount']:,}")
        print(f"      Eligibility Score: {scheme['eligibilityScore']:.2%}")
        print(f"      Category: {scheme['category']}")
        print(f"      Approval Probability: {scheme['approvalProbability']:.2%}")
    
    # Get comprehensive summary
    print("\n5. Comprehensive Eligibility Summary:")
    summary = engine.get_eligibility_summary(user_profile)
    
    print(f"   - Total Eligible Schemes: {summary['totalEligibleSchemes']}")
    print(f"   - Total Annual Benefit: ₹{summary['totalAnnualBenefit']:,.0f}")
    
    if summary['recommendations']:
        print("\n   Recommendations:")
        for rec in summary['recommendations']:
            print(f"   • {rec}")
    
    # Demonstrate scheme database capabilities
    print("\n6. Scheme Database Statistics:")
    print(f"   - Total Schemes: {engine.scheme_db.get_scheme_count()}")
    print(f"   - Total Rules: {engine.scheme_db.get_rule_count()}")
    
    # Show scheme categories
    from services.scheme_database import SchemeCategory
    print("\n   Schemes by Category:")
    for category in SchemeCategory:
        schemes = engine.scheme_db.get_schemes_by_category(category)
        if schemes:
            print(f"   • {category.value.title()}: {len(schemes)} schemes")
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
