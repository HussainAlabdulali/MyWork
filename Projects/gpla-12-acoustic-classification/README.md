# GPLA-12 Acoustic Leakage Classification

This project explores machine learning models for classifying acoustic gas pipeline leakage signals from the GPLA-12 dataset. The notebook combines exploratory data analysis, classical machine learning baselines, a PyTorch 1D CNN, and a simple probability-based ensemble.

## Dataset

GPLA-12 is an acoustic signal dataset for gas pipeline leakage fault diagnosis introduced by Jie Li and Lizhong Yao in 2021. The dataset contains 684 labeled acoustic signal samples across 12 balanced classes, with 57 samples per class. Each sample is represented as a 1,460-feature time-series signal.

The 12 classes represent combinations of:

- Pipeline gas pressure: 0.2 MPa, 0.4 MPa, or 0.5 MPa
- Acoustic sensor/microphone source: microphone 1 or microphone 2
- Noise condition: noiseless or strongly noisy environment

References:

- Paper: [GPLA-12: An Acoustic Signal Dataset of Gas Pipeline Leakage](https://arxiv.org/abs/2106.10277)
- Dataset/code source: [Deep-AI-Application-DAIP/acoustic-leakage-dataset-GPLA-12](https://github.com/Deep-AI-Application-DAIP/acoustic-leakage-dataset-GPLA-12)

## Project Structure

```text
gpla-12-acoustic-classification/
├── main.ipynb
├── README.md
└── data/
    ├── data_v1/
    │   ├── data.csv
    │   └── label.csv
    └── data_v2/
        ├── data.xlsx
        └── label.xlsx
```

The notebook currently uses the CSV files in `data/data_v1/`.

## Workflow

The notebook follows this process:

1. Load and merge the signal matrix and labels.
2. Check class balance across the 12 GPLA-12 categories.
3. Analyze within-class diversity and feature variation.
4. Inspect potentially redundant features through correlation, variance, and mutual information checks.
5. Train a Gaussian Naive Bayes baseline.
6. Evaluate the baseline with both a holdout split and stratified cross-validation.
7. Train a PyTorch 1D convolutional neural network on the acoustic signal features.
8. Combine the CNN and GaussianNB predictions with a simple ensemble rule.

## Models

### Reason for the Chosen Models

The model selection was guided by the GPLA-12 paper, which showed that different classifiers performed unevenly across the 12 classes. Because CNN and Gaussian Naive Bayes appeared to make complementary strengths on different class groups, this project uses both models: CNN as the main signal-learning model and GNB as a lightweight classical baseline. Their predictions are then combined in a simple ensemble after fine-tuning the models individually to improve class-level performance.


### Gaussian Naive Bayes

GaussianNB is used as a fast classical baseline. It provides a useful comparison point for the neural model and performs competitively on several classes.

### 1D Convolutional Neural Network

The CNN treats each 1,460-feature sample as a one-dimensional signal. The architecture uses stacked 1D convolution layers, batch normalization, dropout, max pooling, and adaptive average pooling before classification.

### Ensemble

The ensemble combines model probabilities from the CNN and GaussianNB. The notebook uses GaussianNB as an override for selected tail classes when its confidence passes a threshold, otherwise defaulting to the CNN prediction.

## Results

The notebook reports the following headline results:

- GaussianNB holdout macro F1: approximately `0.81`
- GaussianNB 10-fold CV macro F1: approximately `0.81 +/- 0.04`
- CNN holdout macro F1: approximately `0.79`
- CNN + GaussianNB ensemble holdout macro F1: approximately `0.97`

The ensemble result should be interpreted carefully because the holdout test set contains only 69 samples. A stronger future evaluation would repeat the ensemble comparison across stratified cross-validation or multiple random seeds.

## Requirements

Main Python dependencies:

```text
pandas
numpy
matplotlib
scikit-learn
torch
openpyxl
```

Install them with:

```bash
pip install pandas numpy matplotlib scikit-learn torch openpyxl
```

## How to Run

From the `gpla-12-acoustic-classification` folder, open and run:

```text
main.ipynb
```

The notebook expects the data files to be available at:

```text
data/data_v1/data.csv
data/data_v1/label.csv
```

Running all cells trains the baseline model, trains the CNN, evaluates both models, and evaluates the ensemble.

## Notes and Limitations

- GPLA-12 is small, with only 684 total samples, so validation strategy matters.
- The dataset is balanced across classes, but some classes are harder to distinguish than others.
- The current notebook is exploratory and optimized for analysis readability rather than production deployment.
- The ensemble rule is manually designed based on observed model behavior; future work could replace it with a learned stacking model or a cross-validated ensemble.
- Oversampling techniques were attempted using SMOTE, but resulted in middling to worse performence.
