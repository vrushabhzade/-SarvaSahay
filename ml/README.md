# SarvaSahay ML Components

This directory contains the machine learning components for the SarvaSahay platform's eligibility engine.

## Overview

The ML system achieves 89% accuracy for government scheme eligibility matching using XGBoost models with 50+ engineered features.

## Components

### 1. Eligibility Model (`models/eligibility_model.py`)

XGBoost-based model for predicting scheme eligibility:

- **Features**: 50+ engineered features from user profiles and scheme data
- **Algorithm**: XGBoost Classifier with optimized hyperparameters
- **Accuracy Target**: 89% (as per requirements)
- **Inference Time**: <1 second per scheme evaluation

Key features include:
- Demographics (age, gender, caste, marital status)
- Economic indicators (income, land ownership, employment)
- Location data (state, district, rural/urban)
- Family composition (size, dependents, elderly members)
- Scheme-specific matching scores
- Interaction features for complex patterns

### 2. Retraining Pipeline (`training/retraining_pipeline.py`)

Quarterly model retraining system with outcome tracking:

**OutcomeTracker**:
- Records application outcomes (approved/rejected)
- Tracks approval rates and rejection reasons
- Monitors processing times
- Calculates model accuracy over time

**RetrainingPipeline**:
- Automatic quarterly retraining schedule
- Accuracy monitoring (89% requirement)
- Performance degradation detection
- Training history and metrics tracking

### 3. Training Script (`training/train_model.py`)

Command-line tool for model training and monitoring:

```bash
# Show performance report
python ml/training/train_model.py --mode report

# Retrain model (if needed)
python ml/training/train_model.py --mode retrain

# Force retraining
python ml/training/train_model.py --mode retrain --force
```

## Integration with Eligibility Engine

The eligibility engine (`services/eligibility_engine.py`) integrates:

1. **XGBoost Model**: For ML-based eligibility predictions
2. **Scheme Database**: 34+ government schemes with 70+ rules
3. **Rule Engine**: Complex interdependent eligibility rules
4. **Fallback Logic**: Rule-based matching when ML model unavailable

## Performance Requirements

- **Evaluation Time**: <5 seconds for 30+ schemes
- **Model Accuracy**: ≥89%
- **Inference Time**: <1 second per prediction
- **Retraining Frequency**: Quarterly (90 days)

## Data Flow

```
User Profile + Scheme Data
    ↓
Feature Engineering (50+ features)
    ↓
XGBoost Model Prediction
    ↓
Eligibility Score + Category
    ↓
Application Outcome Recording
    ↓
Outcome Tracker
    ↓
Quarterly Retraining Pipeline
```

## Model Files

- `models/eligibility_model.py`: Model implementation
- `models/saved/eligibility_model.pkl`: Trained model (created after training)
- `training/data/outcomes.json`: Application outcomes for retraining

## Future Enhancements

1. Hyperparameter optimization with Optuna
2. Model explainability with SHAP values
3. A/B testing for model versions
4. Real-time model monitoring dashboard
5. Automated model deployment pipeline
