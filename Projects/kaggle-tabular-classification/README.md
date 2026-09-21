# Kaggle Tabular Classification Project

This project contains a machine learning pipeline built for the [Machine Learning 251 Kaggle competition](https://www.kaggle.com/competitions/machine-learning-251-competition/overview). The work was completed by a team of two and focuses on predicting a binary target from anonymized tabular features.

The main challenge in this dataset is the strong class imbalance: the minority class, `circle`, represents only about 6.7% of the training data. Because of that, the notebook focuses on improving minority-class F1 rather than only optimizing overall accuracy using methods such as oversampling and feature engineering.

## Project Structure

```text
kaggle-tabular-classification/
├── project.ipynb
├── README.md
└── mnt/
    └── data/
        ├── dataset-train-vf.csv
        └── dataset-test-vf.csv
```

## Dataset Overview

The training data contains:

- 4,480 training rows
- 792 test rows
- 11 anonymized feature columns: `f1` through `f11`
- One ID column
- One binary target column: `y`

The target distribution is highly imbalanced:

| Class | Count | Percentage |
| --- | ---: | ---: |
| `square` | 4,181 | 93.33% |
| `circle` | 299 | 6.67% |

Several columns also contain substantial missingness:

- `f1`: about 41% missing in train
- `f3`: about 31% missing in train
- `f10`: about 87% missing in train

## Approach

The notebook's workflow:

1. Explore the train and test datasets.
2. Inspect missing values, outliers, target imbalance, and categorical values.
3. Build preprocessing pipelines for numeric and categorical features.
4. Compare multiple models under stratified cross-validation.
5. Add missing-value indicator features for heavily missing columns.
6. Tune XGBoost hyperparameters.
7. Adjust the probability threshold to improve minority-class F1.
8. Generate predictions for the Kaggle test set.

## Preprocessing and Feature Engineering

The preprocessing pipeline handled missing values, categorical encoding, and model-specific scaling. Numeric features were imputed with the median, the categorical feature `f11` was one-hot encoded, and KNN used standard scaling.

Feature engineering focused on missingness indicators. Because `f10`, `f1`, and `f3` had substantial missing values, binary indicators were added to preserve whether a value was originally missing. The original `f10` column was removed because it was missing in most rows, while its missingness pattern was kept as `f10_missing`.

## Models Tested

### Balanced Random Forest

Balanced Random Forest was used as a tree-based model designed for imbalanced classification.

Local cross-validation result:

- Minority-class F1: approximately `0.531`

### KNN with SMOTE

KNN was tested with scaling and SMOTE inside an imbalanced-learn pipeline. SMOTE was applied inside cross-validation to avoid leaking synthetic samples across folds.

Local cross-validation result:

- Minority-class F1: approximately `0.583`

### XGBoost

XGBoost performed best among the tested models. The final version used:

- Median imputation
- One-hot encoding
- Missingness indicators
- `scale_pos_weight` tuning
- Grid search with stratified cross-validation
- A custom scorer using a fixed minority-class probability threshold

Local cross-validation result:

- Initial XGBoost minority-class F1: approximately `0.671`
- Tuned XGBoost minority-class F1: approximately `0.701`

## Final Model

The final selected model is a tuned XGBoost classifier inside a scikit-learn pipeline. The notebook applies a custom probability threshold for the minority class instead of using the default `0.50` cutoff. This was done because the dataset is heavily imbalanced and the competition goal was better served by increasing the model's sensitivity to the minority class.

Best local model configuration from the notebook:

```text
n_estimators: 800
max_depth: 3
learning_rate: 0.1
min_child_weight: 3
subsample: 1.0
colsample_bytree: 1.0
scale_pos_weight: about 6.99
minority-class threshold: 0.15
```

## Kaggle Result

The final team submission achieved:

- Submission F1 score: `0.74698`
- Leaderboard rank: `7th`

## Requirements

Main Python dependencies:

```text
pandas
numpy
matplotlib
scikit-learn
imbalanced-learn
xgboost
```

Install them with:

```bash
pip install pandas numpy matplotlib scikit-learn imbalanced-learn xgboost
```

## How to Run

Open and run the notebook:

```text
project.ipynb
```

The notebook expects the train and test files at:

```text
mnt/data/dataset-train-vf.csv
mnt/data/dataset-test-vf.csv
```

Running the notebook trains the models, compares cross-validation performance, tunes the final XGBoost model, and generates predictions for the Kaggle test set.

## Notes

- This was a team project completed by me and my colleague.
- The dataset uses anonymized feature names, so the modeling process relies on statistical patterns rather than domain-specific feature interpretation.
- The strongest gains came from handling missingness explicitly and tuning the prediction threshold for the minority class.
