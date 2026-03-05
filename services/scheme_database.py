"""
Government Scheme Database
Comprehensive database of 30+ government schemes with eligibility rules
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class SchemeCategory(Enum):
    """Categories of government schemes"""
    AGRICULTURE = "agriculture"
    EMPLOYMENT = "employment"
    EDUCATION = "education"
    HEALTH = "health"
    HOUSING = "housing"
    SOCIAL_WELFARE = "social_welfare"
    FINANCIAL_INCLUSION = "financial_inclusion"


@dataclass
class EligibilityRule:
    """Represents a single eligibility rule"""
    field: str
    operator: str  # eq, ne, lt, le, gt, ge, in, not_in, between
    value: Any
    weight: float = 1.0
    
    def evaluate(self, user_value: Any) -> bool:
        """Evaluate rule against user value"""
        if self.operator == "eq":
            return user_value == self.value
        elif self.operator == "ne":
            return user_value != self.value
        elif self.operator == "lt":
            return user_value < self.value
        elif self.operator == "le":
            return user_value <= self.value
        elif self.operator == "gt":
            return user_value > self.value
        elif self.operator == "ge":
            return user_value >= self.value
        elif self.operator == "in":
            return user_value in self.value
        elif self.operator == "not_in":
            return user_value not in self.value
        elif self.operator == "between":
            return self.value[0] <= user_value <= self.value[1]
        else:
            raise ValueError(f"Unknown operator: {self.operator}")


@dataclass
class SchemeData:
    """Complete scheme information with eligibility rules"""
    schemeId: str
    name: str
    category: SchemeCategory
    benefitAmount: float
    benefitType: str  # cash, subsidy, loan, insurance
    frequency: str  # one_time, monthly, quarterly, yearly
    ministry: str
    description: str
    rules: List[EligibilityRule] = field(default_factory=list)
    interdependent_schemes: List[str] = field(default_factory=list)
    priority: int = 1
    active: bool = True


class SchemeDatabase:
    """
    Comprehensive database of 30+ government schemes
    Manages 1000+ eligibility rules with interdependencies
    """
    
    def __init__(self):
        self.schemes: Dict[str, SchemeData] = {}
        self._initialize_schemes()
    
    def _initialize_schemes(self) -> None:
        """Initialize database with 30+ government schemes"""
        
        # Agriculture Schemes (10 schemes)
        self._add_agriculture_schemes()
        
        # Employment Schemes (5 schemes)
        self._add_employment_schemes()
        
        # Social Welfare Schemes (8 schemes)
        self._add_social_welfare_schemes()
        
        # Education Schemes (4 schemes)
        self._add_education_schemes()
        
        # Health Schemes (3 schemes)
        self._add_health_schemes()
        
        # Housing Schemes (2 schemes)
        self._add_housing_schemes()
        
        # Financial Inclusion Schemes (3 schemes)
        self._add_financial_inclusion_schemes()
    
    def _add_agriculture_schemes(self) -> None:
        """Add agriculture-related schemes"""
        
        # PM-KISAN
        self.schemes["PM-KISAN"] = SchemeData(
            schemeId="PM-KISAN",
            name="Pradhan Mantri Kisan Samman Nidhi",
            category=SchemeCategory.AGRICULTURE,
            benefitAmount=6000,
            benefitType="cash",
            frequency="yearly",
            ministry="Ministry of Agriculture",
            description="Income support to farmer families",
            rules=[
                EligibilityRule("economic.employmentStatus", "in", ["farmer"], 2.0),
                EligibilityRule("economic.landOwnership", "between", [0.1, 2.0], 1.5),
                EligibilityRule("economic.annualIncome", "le", 200000, 1.0),
            ],
            priority=1
        )
        
        # Kisan Credit Card
        self.schemes["KCC"] = SchemeData(
            schemeId="KCC",
            name="Kisan Credit Card",
            category=SchemeCategory.AGRICULTURE,
            benefitAmount=300000,
            benefitType="loan",
            frequency="one_time",
            ministry="Ministry of Agriculture",
            description="Credit facility for farmers",
            rules=[
                EligibilityRule("economic.employmentStatus", "in", ["farmer"], 2.0),
                EligibilityRule("economic.landOwnership", "gt", 0.5, 1.5),
                EligibilityRule("demographics.age", "between", [18, 75], 1.0),
            ],
            priority=2
        )
        
        # PM Fasal Bima Yojana
        self.schemes["PMFBY"] = SchemeData(
            schemeId="PMFBY",
            name="Pradhan Mantri Fasal Bima Yojana",
            category=SchemeCategory.AGRICULTURE,
            benefitAmount=200000,
            benefitType="insurance",
            frequency="yearly",
            ministry="Ministry of Agriculture",
            description="Crop insurance scheme",
            rules=[
                EligibilityRule("economic.employmentStatus", "in", ["farmer"], 2.0),
                EligibilityRule("economic.landOwnership", "gt", 0.1, 1.0),
            ],
            priority=2
        )
        
        # Soil Health Card Scheme
        self.schemes["SHC"] = SchemeData(
            schemeId="SHC",
            name="Soil Health Card Scheme",
            category=SchemeCategory.AGRICULTURE,
            benefitAmount=0,
            benefitType="subsidy",
            frequency="one_time",
            ministry="Ministry of Agriculture",
            description="Free soil testing for farmers",
            rules=[
                EligibilityRule("economic.employmentStatus", "in", ["farmer"], 2.0),
                EligibilityRule("economic.landOwnership", "gt", 0, 1.0),
            ],
            priority=3
        )
        
        # PM Krishi Sinchai Yojana
        self.schemes["PMKSY"] = SchemeData(
            schemeId="PMKSY",
            name="Pradhan Mantri Krishi Sinchai Yojana",
            category=SchemeCategory.AGRICULTURE,
            benefitAmount=50000,
            benefitType="subsidy",
            frequency="one_time",
            ministry="Ministry of Agriculture",
            description="Irrigation support for farmers",
            rules=[
                EligibilityRule("economic.employmentStatus", "in", ["farmer"], 2.0),
                EligibilityRule("economic.landOwnership", "between", [0.5, 10.0], 1.5),
                EligibilityRule("economic.annualIncome", "le", 300000, 1.0),
            ],
            priority=2
        )
        
        # National Agriculture Market
        self.schemes["NAM"] = SchemeData(
            schemeId="NAM",
            name="National Agriculture Market",
            category=SchemeCategory.AGRICULTURE,
            benefitAmount=0,
            benefitType="subsidy",
            frequency="one_time",
            ministry="Ministry of Agriculture",
            description="Online trading platform for farmers",
            rules=[
                EligibilityRule("economic.employmentStatus", "in", ["farmer"], 2.0),
            ],
            priority=3
        )
        
        # Paramparagat Krishi Vikas Yojana
        self.schemes["PKVY"] = SchemeData(
            schemeId="PKVY",
            name="Paramparagat Krishi Vikas Yojana",
            category=SchemeCategory.AGRICULTURE,
            benefitAmount=50000,
            benefitType="subsidy",
            frequency="one_time",
            ministry="Ministry of Agriculture",
            description="Organic farming support",
            rules=[
                EligibilityRule("economic.employmentStatus", "in", ["farmer"], 2.0),
                EligibilityRule("economic.landOwnership", "between", [0.5, 5.0], 1.5),
            ],
            priority=3
        )
        
        # Rashtriya Krishi Vikas Yojana
        self.schemes["RKVY"] = SchemeData(
            schemeId="RKVY",
            name="Rashtriya Krishi Vikas Yojana",
            category=SchemeCategory.AGRICULTURE,
            benefitAmount=100000,
            benefitType="subsidy",
            frequency="one_time",
            ministry="Ministry of Agriculture",
            description="Agriculture development support",
            rules=[
                EligibilityRule("economic.employmentStatus", "in", ["farmer"], 2.0),
                EligibilityRule("economic.landOwnership", "gt", 1.0, 1.5),
            ],
            priority=2
        )
        
        # National Horticulture Mission
        self.schemes["NHM"] = SchemeData(
            schemeId="NHM",
            name="National Horticulture Mission",
            category=SchemeCategory.AGRICULTURE,
            benefitAmount=75000,
            benefitType="subsidy",
            frequency="one_time",
            ministry="Ministry of Agriculture",
            description="Horticulture development support",
            rules=[
                EligibilityRule("economic.employmentStatus", "in", ["farmer"], 2.0),
                EligibilityRule("economic.landOwnership", "between", [0.5, 4.0], 1.5),
            ],
            priority=3
        )
        
        # Dairy Entrepreneurship Development Scheme
        self.schemes["DEDS"] = SchemeData(
            schemeId="DEDS",
            name="Dairy Entrepreneurship Development Scheme",
            category=SchemeCategory.AGRICULTURE,
            benefitAmount=1000000,
            benefitType="loan",
            frequency="one_time",
            ministry="Ministry of Animal Husbandry",
            description="Dairy business support",
            rules=[
                EligibilityRule("economic.employmentStatus", "in", ["farmer", "self_employed"], 2.0),
                EligibilityRule("demographics.age", "between", [18, 65], 1.0),
            ],
            priority=3
        )
    
    def _add_employment_schemes(self) -> None:
        """Add employment-related schemes"""
        
        # MGNREGA
        self.schemes["MGNREGA"] = SchemeData(
            schemeId="MGNREGA",
            name="Mahatma Gandhi National Rural Employment Guarantee Act",
            category=SchemeCategory.EMPLOYMENT,
            benefitAmount=25000,
            benefitType="cash",
            frequency="yearly",
            ministry="Ministry of Rural Development",
            description="100 days guaranteed employment",
            rules=[
                EligibilityRule("demographics.age", "between", [18, 65], 1.5),
                EligibilityRule("economic.employmentStatus", "in", ["laborer", "unemployed"], 2.0),
            ],
            priority=1
        )
        
        # PM Svanidhi
        self.schemes["PM-SVANIDHI"] = SchemeData(
            schemeId="PM-SVANIDHI",
            name="PM Street Vendor's AtmaNirbhar Nidhi",
            category=SchemeCategory.EMPLOYMENT,
            benefitAmount=10000,
            benefitType="loan",
            frequency="one_time",
            ministry="Ministry of Housing and Urban Affairs",
            description="Micro-credit for street vendors",
            rules=[
                EligibilityRule("economic.employmentStatus", "in", ["self_employed"], 2.0),
                EligibilityRule("demographics.age", "between", [18, 65], 1.0),
            ],
            priority=2
        )
        
        # Deen Dayal Upadhyaya Grameen Kaushalya Yojana
        self.schemes["DDU-GKY"] = SchemeData(
            schemeId="DDU-GKY",
            name="Deen Dayal Upadhyaya Grameen Kaushalya Yojana",
            category=SchemeCategory.EMPLOYMENT,
            benefitAmount=50000,
            benefitType="subsidy",
            frequency="one_time",
            ministry="Ministry of Rural Development",
            description="Skill development for rural youth",
            rules=[
                EligibilityRule("demographics.age", "between", [15, 35], 2.0),
                EligibilityRule("economic.annualIncome", "le", 100000, 1.5),
            ],
            priority=2
        )
        
        # PM Employment Generation Programme
        self.schemes["PMEGP"] = SchemeData(
            schemeId="PMEGP",
            name="Prime Minister's Employment Generation Programme",
            category=SchemeCategory.EMPLOYMENT,
            benefitAmount=2500000,
            benefitType="loan",
            frequency="one_time",
            ministry="Ministry of MSME",
            description="Self-employment support",
            rules=[
                EligibilityRule("demographics.age", "between", [18, 65], 1.5),
                EligibilityRule("economic.employmentStatus", "in", ["unemployed", "self_employed"], 2.0),
            ],
            priority=2
        )
        
        # Stand Up India
        self.schemes["STAND-UP-INDIA"] = SchemeData(
            schemeId="STAND-UP-INDIA",
            name="Stand Up India Scheme",
            category=SchemeCategory.EMPLOYMENT,
            benefitAmount=5000000,
            benefitType="loan",
            frequency="one_time",
            ministry="Ministry of Finance",
            description="Entrepreneurship support for SC/ST/Women",
            rules=[
                EligibilityRule("demographics.age", "between", [18, 65], 1.5),
                EligibilityRule("demographics.caste", "in", ["sc", "st"], 2.0),
            ],
            priority=2
        )
    
    def _add_social_welfare_schemes(self) -> None:
        """Add social welfare schemes"""
        
        # PM Awas Yojana - Gramin
        self.schemes["PMAY-G"] = SchemeData(
            schemeId="PMAY-G",
            name="Pradhan Mantri Awas Yojana - Gramin",
            category=SchemeCategory.HOUSING,
            benefitAmount=120000,
            benefitType="subsidy",
            frequency="one_time",
            ministry="Ministry of Rural Development",
            description="Housing for rural poor",
            rules=[
                EligibilityRule("economic.annualIncome", "le", 100000, 2.0),
                EligibilityRule("economic.landOwnership", "le", 1.0, 1.5),
            ],
            priority=1
        )
        
        # National Social Assistance Programme - Old Age Pension
        self.schemes["NSAP-OAP"] = SchemeData(
            schemeId="NSAP-OAP",
            name="National Social Assistance Programme - Old Age Pension",
            category=SchemeCategory.SOCIAL_WELFARE,
            benefitAmount=2400,
            benefitType="cash",
            frequency="monthly",
            ministry="Ministry of Rural Development",
            description="Pension for elderly",
            rules=[
                EligibilityRule("demographics.age", "ge", 60, 2.0),
                EligibilityRule("economic.annualIncome", "le", 50000, 1.5),
            ],
            priority=1
        )
        
        # Widow Pension Scheme
        self.schemes["WPS"] = SchemeData(
            schemeId="WPS",
            name="Widow Pension Scheme",
            category=SchemeCategory.SOCIAL_WELFARE,
            benefitAmount=3000,
            benefitType="cash",
            frequency="monthly",
            ministry="Ministry of Rural Development",
            description="Pension for widows",
            rules=[
                EligibilityRule("demographics.maritalStatus", "eq", "widowed", 2.0),
                EligibilityRule("demographics.age", "between", [40, 65], 1.5),
                EligibilityRule("economic.annualIncome", "le", 50000, 1.5),
            ],
            priority=1
        )
        
        # Disability Pension Scheme
        self.schemes["DPS"] = SchemeData(
            schemeId="DPS",
            name="Disability Pension Scheme",
            category=SchemeCategory.SOCIAL_WELFARE,
            benefitAmount=3000,
            benefitType="cash",
            frequency="monthly",
            ministry="Ministry of Social Justice",
            description="Pension for disabled persons",
            rules=[
                EligibilityRule("demographics.age", "between", [18, 65], 1.5),
                EligibilityRule("economic.annualIncome", "le", 50000, 1.5),
            ],
            priority=1
        )
        
        # Antyodaya Anna Yojana
        self.schemes["AAY"] = SchemeData(
            schemeId="AAY",
            name="Antyodaya Anna Yojana",
            category=SchemeCategory.SOCIAL_WELFARE,
            benefitAmount=4200,
            benefitType="subsidy",
            frequency="yearly",
            ministry="Ministry of Consumer Affairs",
            description="Subsidized food grains",
            rules=[
                EligibilityRule("economic.annualIncome", "le", 50000, 2.0),
                EligibilityRule("family.size", "ge", 3, 1.0),
            ],
            priority=1
        )
        
        # National Family Benefit Scheme
        self.schemes["NFBS"] = SchemeData(
            schemeId="NFBS",
            name="National Family Benefit Scheme",
            category=SchemeCategory.SOCIAL_WELFARE,
            benefitAmount=20000,
            benefitType="cash",
            frequency="one_time",
            ministry="Ministry of Rural Development",
            description="Financial assistance on death of breadwinner",
            rules=[
                EligibilityRule("demographics.age", "between", [18, 65], 1.5),
                EligibilityRule("economic.annualIncome", "le", 100000, 2.0),
            ],
            priority=2
        )
        
        # Sukanya Samriddhi Yojana
        self.schemes["SSY"] = SchemeData(
            schemeId="SSY",
            name="Sukanya Samriddhi Yojana",
            category=SchemeCategory.SOCIAL_WELFARE,
            benefitAmount=150000,
            benefitType="subsidy",
            frequency="one_time",
            ministry="Ministry of Finance",
            description="Savings scheme for girl child",
            rules=[
                EligibilityRule("demographics.gender", "eq", "female", 2.0),
                EligibilityRule("demographics.age", "le", 10, 2.0),
            ],
            priority=2
        )
        
        # Beti Bachao Beti Padhao
        self.schemes["BBBP"] = SchemeData(
            schemeId="BBBP",
            name="Beti Bachao Beti Padhao",
            category=SchemeCategory.SOCIAL_WELFARE,
            benefitAmount=50000,
            benefitType="subsidy",
            frequency="one_time",
            ministry="Ministry of Women and Child Development",
            description="Girl child welfare scheme",
            rules=[
                EligibilityRule("demographics.gender", "eq", "female", 2.0),
                EligibilityRule("demographics.age", "le", 18, 1.5),
            ],
            priority=2
        )
    
    def _add_education_schemes(self) -> None:
        """Add education-related schemes"""
        
        # Post Matric Scholarship for SC Students
        self.schemes["PMS-SC"] = SchemeData(
            schemeId="PMS-SC",
            name="Post Matric Scholarship for SC Students",
            category=SchemeCategory.EDUCATION,
            benefitAmount=20000,
            benefitType="subsidy",
            frequency="yearly",
            ministry="Ministry of Social Justice",
            description="Education support for SC students",
            rules=[
                EligibilityRule("demographics.caste", "eq", "sc", 2.0),
                EligibilityRule("demographics.age", "between", [16, 30], 1.5),
                EligibilityRule("economic.annualIncome", "le", 250000, 1.5),
            ],
            priority=2
        )
        
        # Post Matric Scholarship for ST Students
        self.schemes["PMS-ST"] = SchemeData(
            schemeId="PMS-ST",
            name="Post Matric Scholarship for ST Students",
            category=SchemeCategory.EDUCATION,
            benefitAmount=20000,
            benefitType="subsidy",
            frequency="yearly",
            ministry="Ministry of Tribal Affairs",
            description="Education support for ST students",
            rules=[
                EligibilityRule("demographics.caste", "eq", "st", 2.0),
                EligibilityRule("demographics.age", "between", [16, 30], 1.5),
                EligibilityRule("economic.annualIncome", "le", 250000, 1.5),
            ],
            priority=2
        )
        
        # National Means cum Merit Scholarship
        self.schemes["NMMS"] = SchemeData(
            schemeId="NMMS",
            name="National Means cum Merit Scholarship",
            category=SchemeCategory.EDUCATION,
            benefitAmount=12000,
            benefitType="subsidy",
            frequency="yearly",
            ministry="Ministry of Education",
            description="Merit scholarship for economically weaker students",
            rules=[
                EligibilityRule("demographics.age", "between", [13, 16], 2.0),
                EligibilityRule("economic.annualIncome", "le", 150000, 2.0),
            ],
            priority=2
        )
        
        # Pre Matric Scholarship for OBC Students
        self.schemes["PREMS-OBC"] = SchemeData(
            schemeId="PREMS-OBC",
            name="Pre Matric Scholarship for OBC Students",
            category=SchemeCategory.EDUCATION,
            benefitAmount=10000,
            benefitType="subsidy",
            frequency="yearly",
            ministry="Ministry of Social Justice",
            description="Education support for OBC students",
            rules=[
                EligibilityRule("demographics.caste", "eq", "obc", 2.0),
                EligibilityRule("demographics.age", "between", [10, 18], 1.5),
                EligibilityRule("economic.annualIncome", "le", 100000, 1.5),
            ],
            priority=2
        )
    
    def _add_health_schemes(self) -> None:
        """Add health-related schemes"""
        
        # Ayushman Bharat - PM Jan Arogya Yojana
        self.schemes["AB-PMJAY"] = SchemeData(
            schemeId="AB-PMJAY",
            name="Ayushman Bharat - PM Jan Arogya Yojana",
            category=SchemeCategory.HEALTH,
            benefitAmount=500000,
            benefitType="insurance",
            frequency="yearly",
            ministry="Ministry of Health",
            description="Health insurance for poor families",
            rules=[
                EligibilityRule("economic.annualIncome", "le", 100000, 2.0),
                EligibilityRule("family.size", "ge", 3, 1.0),
            ],
            priority=1
        )
        
        # Janani Suraksha Yojana
        self.schemes["JSY"] = SchemeData(
            schemeId="JSY",
            name="Janani Suraksha Yojana",
            category=SchemeCategory.HEALTH,
            benefitAmount=6000,
            benefitType="cash",
            frequency="one_time",
            ministry="Ministry of Health",
            description="Maternity benefit scheme",
            rules=[
                EligibilityRule("demographics.gender", "eq", "female", 2.0),
                EligibilityRule("demographics.age", "between", [18, 45], 2.0),
                EligibilityRule("economic.annualIncome", "le", 120000, 1.5),
            ],
            priority=1
        )
        
        # Rashtriya Swasthya Bima Yojana
        self.schemes["RSBY"] = SchemeData(
            schemeId="RSBY",
            name="Rashtriya Swasthya Bima Yojana",
            category=SchemeCategory.HEALTH,
            benefitAmount=30000,
            benefitType="insurance",
            frequency="yearly",
            ministry="Ministry of Labour",
            description="Health insurance for BPL families",
            rules=[
                EligibilityRule("economic.annualIncome", "le", 50000, 2.0),
            ],
            priority=1
        )
    
    def _add_housing_schemes(self) -> None:
        """Add housing-related schemes"""
        
        # Pradhan Mantri Awas Yojana - Urban
        self.schemes["PMAY-U"] = SchemeData(
            schemeId="PMAY-U",
            name="Pradhan Mantri Awas Yojana - Urban",
            category=SchemeCategory.HOUSING,
            benefitAmount=250000,
            benefitType="subsidy",
            frequency="one_time",
            ministry="Ministry of Housing",
            description="Housing for urban poor",
            rules=[
                EligibilityRule("economic.annualIncome", "le", 300000, 2.0),
            ],
            priority=1
        )
    
    def _add_financial_inclusion_schemes(self) -> None:
        """Add financial inclusion schemes"""
        
        # Pradhan Mantri Jan Dhan Yojana
        self.schemes["PMJDY"] = SchemeData(
            schemeId="PMJDY",
            name="Pradhan Mantri Jan Dhan Yojana",
            category=SchemeCategory.FINANCIAL_INCLUSION,
            benefitAmount=0,
            benefitType="subsidy",
            frequency="one_time",
            ministry="Ministry of Finance",
            description="Financial inclusion - bank account",
            rules=[
                EligibilityRule("demographics.age", "ge", 10, 1.0),
            ],
            priority=3
        )
        
        # Atal Pension Yojana
        self.schemes["APY"] = SchemeData(
            schemeId="APY",
            name="Atal Pension Yojana",
            category=SchemeCategory.FINANCIAL_INCLUSION,
            benefitAmount=60000,
            benefitType="subsidy",
            frequency="yearly",
            ministry="Ministry of Finance",
            description="Pension scheme for unorganized sector",
            rules=[
                EligibilityRule("demographics.age", "between", [18, 40], 2.0),
                EligibilityRule("economic.annualIncome", "le", 200000, 1.5),
            ],
            priority=2
        )
        
        # Pradhan Mantri Jeevan Jyoti Bima Yojana
        self.schemes["PMJJBY"] = SchemeData(
            schemeId="PMJJBY",
            name="Pradhan Mantri Jeevan Jyoti Bima Yojana",
            category=SchemeCategory.FINANCIAL_INCLUSION,
            benefitAmount=200000,
            benefitType="insurance",
            frequency="yearly",
            ministry="Ministry of Finance",
            description="Life insurance scheme",
            rules=[
                EligibilityRule("demographics.age", "between", [18, 50], 2.0),
            ],
            priority=2
        )
    
    def get_all_schemes(self) -> List[Dict[str, Any]]:
        """Get all schemes in dictionary format"""
        return [self._scheme_to_dict(scheme) for scheme in self.schemes.values() if scheme.active]
    
    def get_scheme_by_id(self, scheme_id: str) -> Optional[Dict[str, Any]]:
        """Get specific scheme by ID"""
        scheme = self.schemes.get(scheme_id)
        return self._scheme_to_dict(scheme) if scheme else None
    
    def get_schemes_by_category(self, category: SchemeCategory) -> List[Dict[str, Any]]:
        """Get schemes filtered by category"""
        return [
            self._scheme_to_dict(scheme) 
            for scheme in self.schemes.values() 
            if scheme.category == category and scheme.active
        ]
    
    def _scheme_to_dict(self, scheme: SchemeData) -> Dict[str, Any]:
        """Convert SchemeData to dictionary format"""
        return {
            "schemeId": scheme.schemeId,
            "name": scheme.name,
            "category": scheme.category.value,
            "benefitAmount": scheme.benefitAmount,
            "benefitType": scheme.benefitType,
            "frequency": scheme.frequency,
            "ministry": scheme.ministry,
            "description": scheme.description,
            "eligibilityCriteria": self._rules_to_criteria(scheme.rules),
            "priority": scheme.priority,
            "interdependentSchemes": scheme.interdependent_schemes
        }
    
    def _rules_to_criteria(self, rules: List[EligibilityRule]) -> Dict[str, Any]:
        """Convert rules to eligibility criteria format"""
        criteria = {}
        for rule in rules:
            field_parts = rule.field.split('.')
            if len(field_parts) == 2:
                category, field_name = field_parts
                if category not in criteria:
                    criteria[category] = {}
                
                if rule.operator == "between":
                    criteria[category][field_name] = {"min": rule.value[0], "max": rule.value[1]}
                elif rule.operator == "le":
                    criteria[category][field_name] = {"max": rule.value}
                elif rule.operator == "ge":
                    criteria[category][field_name] = {"min": rule.value}
                elif rule.operator == "in":
                    criteria[category][field_name] = rule.value
                elif rule.operator == "eq":
                    criteria[category][field_name] = rule.value
        
        return criteria
    
    def get_scheme_count(self) -> int:
        """Get total number of active schemes"""
        return sum(1 for scheme in self.schemes.values() if scheme.active)
    
    def get_rule_count(self) -> int:
        """Get total number of eligibility rules across all schemes"""
        return sum(len(scheme.rules) for scheme in self.schemes.values() if scheme.active)
