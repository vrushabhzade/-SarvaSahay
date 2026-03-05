"""
Eligibility Rule Engine
Processes complex interdependent eligibility rules (1000+)
"""

from typing import Dict, List, Any, Tuple
from services.scheme_database import SchemeDatabase, SchemeData, EligibilityRule


class RuleEngine:
    """
    Advanced rule engine for processing 1000+ eligibility rules
    Handles interdependencies and complex rule combinations
    """
    
    def __init__(self, scheme_database: SchemeDatabase):
        self.scheme_db = scheme_database
        self.evaluation_cache: Dict[str, Any] = {}
    
    def evaluate_scheme_eligibility(
        self, 
        user_profile: Dict[str, Any], 
        scheme_id: str
    ) -> Tuple[bool, float, List[str]]:
        """
        Evaluate user eligibility for a specific scheme
        
        Args:
            user_profile: User demographic and economic information
            scheme_id: ID of the scheme to evaluate
            
        Returns:
            Tuple of (is_eligible, confidence_score, failed_rules)
        """
        scheme = self.scheme_db.schemes.get(scheme_id)
        if not scheme:
            return False, 0.0, [f"Scheme {scheme_id} not found"]
        
        if not scheme.active:
            return False, 0.0, ["Scheme is not active"]
        
        return self._evaluate_rules(user_profile, scheme)
    
    def _evaluate_rules(
        self, 
        user_profile: Dict[str, Any], 
        scheme: SchemeData
    ) -> Tuple[bool, float, List[str]]:
        """
        Evaluate all rules for a scheme
        
        Returns:
            Tuple of (is_eligible, confidence_score, failed_rules)
        """
        total_weight = sum(rule.weight for rule in scheme.rules)
        passed_weight = 0.0
        failed_rules = []
        
        for rule in scheme.rules:
            try:
                user_value = self._extract_user_value(user_profile, rule.field)
                if rule.evaluate(user_value):
                    passed_weight += rule.weight
                else:
                    failed_rules.append(f"{rule.field} {rule.operator} {rule.value}")
            except (KeyError, TypeError) as e:
                failed_rules.append(f"{rule.field}: {str(e)}")
        
        # Calculate confidence score based on weighted rules
        confidence = passed_weight / total_weight if total_weight > 0 else 0.0
        
        # User is eligible if they pass all mandatory rules (weight >= 1.5)
        mandatory_rules_passed = all(
            self._check_rule(user_profile, rule) 
            for rule in scheme.rules 
            if rule.weight >= 1.5
        )
        
        is_eligible = mandatory_rules_passed and confidence >= 0.7
        
        return is_eligible, confidence, failed_rules
    
    def _check_rule(self, user_profile: Dict[str, Any], rule: EligibilityRule) -> bool:
        """Check if a single rule passes"""
        try:
            user_value = self._extract_user_value(user_profile, rule.field)
            return rule.evaluate(user_value)
        except (KeyError, TypeError):
            return False
    
    def _extract_user_value(self, user_profile: Dict[str, Any], field_path: str) -> Any:
        """
        Extract value from user profile using dot notation
        
        Args:
            user_profile: User profile dictionary
            field_path: Dot-separated path (e.g., 'economic.annualIncome')
            
        Returns:
            Value at the specified path
        """
        parts = field_path.split('.')
        value = user_profile
        
        for part in parts:
            if isinstance(value, dict):
                value = value[part]
            else:
                raise KeyError(f"Cannot access {part} in {field_path}")
        
        return value
    
    def rank_schemes_by_benefit(
        self, 
        eligible_schemes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Rank schemes by benefit amount and approval probability
        
        Args:
            eligible_schemes: List of eligible schemes with scores
            
        Returns:
            Sorted list of schemes
        """
        return sorted(
            eligible_schemes,
            key=lambda s: (
                s.get('benefitAmount', 0) * s.get('approvalProbability', 0.5),
                s.get('priority', 999)
            ),
            reverse=True
        )
    
    def check_interdependencies(
        self, 
        user_profile: Dict[str, Any], 
        scheme_id: str,
        selected_schemes: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Check if scheme has interdependencies with already selected schemes
        
        Args:
            user_profile: User profile
            scheme_id: Scheme to check
            selected_schemes: Already selected scheme IDs
            
        Returns:
            Tuple of (has_conflicts, conflict_messages)
        """
        scheme = self.scheme_db.schemes.get(scheme_id)
        if not scheme:
            return False, []
        
        conflicts = []
        
        # Check if any interdependent schemes are already selected
        for interdep_id in scheme.interdependent_schemes:
            if interdep_id in selected_schemes:
                interdep_scheme = self.scheme_db.schemes.get(interdep_id)
                if interdep_scheme:
                    conflicts.append(
                        f"Cannot apply for both {scheme.name} and {interdep_scheme.name}"
                    )
        
        return len(conflicts) > 0, conflicts
    
    def get_eligibility_summary(
        self, 
        user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get comprehensive eligibility summary for user
        
        Args:
            user_profile: User demographic and economic information
            
        Returns:
            Summary with eligible schemes, total benefits, and recommendations
        """
        eligible_schemes = []
        total_benefit = 0.0
        
        for scheme_id, scheme in self.scheme_db.schemes.items():
            if not scheme.active:
                continue
            
            is_eligible, confidence, failed_rules = self._evaluate_rules(user_profile, scheme)
            
            if is_eligible:
                scheme_dict = self.scheme_db._scheme_to_dict(scheme)
                scheme_dict['eligibilityScore'] = confidence
                scheme_dict['approvalProbability'] = confidence
                scheme_dict['failedRules'] = failed_rules
                
                eligible_schemes.append(scheme_dict)
                
                # Calculate total benefit based on frequency
                if scheme.frequency == "yearly":
                    total_benefit += scheme.benefitAmount
                elif scheme.frequency == "monthly":
                    total_benefit += scheme.benefitAmount * 12
                elif scheme.frequency == "one_time":
                    total_benefit += scheme.benefitAmount
        
        # Rank schemes
        ranked_schemes = self.rank_schemes_by_benefit(eligible_schemes)
        
        return {
            'totalEligibleSchemes': len(eligible_schemes),
            'totalAnnualBenefit': total_benefit,
            'schemes': ranked_schemes,
            'recommendations': self._generate_recommendations(user_profile, ranked_schemes)
        }
    
    def _generate_recommendations(
        self, 
        user_profile: Dict[str, Any], 
        eligible_schemes: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []
        
        # Recommend high-priority schemes first
        high_priority = [s for s in eligible_schemes if s.get('priority', 999) == 1]
        if high_priority:
            recommendations.append(
                f"Apply for {len(high_priority)} high-priority schemes first"
            )
        
        # Recommend based on benefit amount
        high_benefit = [s for s in eligible_schemes if s.get('benefitAmount', 0) > 50000]
        if high_benefit:
            recommendations.append(
                f"Focus on {len(high_benefit)} high-value schemes (>₹50,000)"
            )
        
        # Recommend based on employment status
        employment = user_profile.get('economic', {}).get('employmentStatus')
        if employment == 'farmer':
            farmer_schemes = [s for s in eligible_schemes if 'agriculture' in s.get('category', '').lower()]
            if farmer_schemes:
                recommendations.append(
                    f"As a farmer, you're eligible for {len(farmer_schemes)} agriculture schemes"
                )
        
        # Recommend based on age
        age = user_profile.get('demographics', {}).get('age', 0)
        if age >= 60:
            recommendations.append("Consider applying for pension schemes")
        elif age <= 25:
            recommendations.append("Explore education and skill development schemes")
        
        return recommendations
    
    def clear_cache(self) -> None:
        """Clear evaluation cache"""
        self.evaluation_cache.clear()
